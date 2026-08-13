
from pathlib import Path
from shutil import rmtree
from typing import Any, Sequence
from uuid import UUID
import polars as pl
from ..utils.constants import PLATFORMS
from ..utils.sanitize import clean_text
from ..utils.user_dir import get_app_data_dir

# Extracted posts live on disk as Parquet rather than in the database. Keeping them in rows meant
# the same posts were stored three times (raw JSON, cleaned JSON, and a Feather blob) and that
# every list query dragged multi-megabyte blobs through SQLite.
DATASETS_DIRNAME = "datasets"

# Fields that live on the Elasticsearch hit itself rather than under _source.
ES_METADATA_FIELDS = frozenset({"_id", "_index", "_score", "_type"})

PARQUET_COMPRESSION = "zstd"


def datasets_root() -> Path:
    return Path(get_app_data_dir()) / DATASETS_DIRNAME


def dataset_dir(query_id: UUID) -> Path:
    return datasets_root() / str(query_id)


def raw_dir(query_id: UUID) -> Path:
    return dataset_dir(query_id) / "raw"


def raw_page_path(query_id: UUID, request_id: UUID) -> Path:
    """One Parquet file per request row, so the two stay 1:1 with no extra bookkeeping column."""
    return raw_dir(query_id) / f"{request_id}.parquet"


def processed_path(query_id: UUID) -> Path:
    return dataset_dir(query_id) / "processed.parquet"


def platform_columns(platform: str) -> list[str]:
    columns = PLATFORMS.get(platform, {}).get("columns", None)

    if columns is None:
        raise ValueError(f"unknown platform: {platform}")

    return list(columns)


def clean_columns(platform: str) -> list[str]:
    return list(PLATFORMS.get(platform, {}).get("clean_columns", []))


def clean_frame(platform: str, frame: pl.DataFrame) -> pl.DataFrame:
    """Applies clean_text to the platform's free-text columns.

    Replaces the previous in-place cleaning of request JSON, which had a bug: it assigned the
    placeholder "␣" to embed.external.description/title and then called clean_text on the
    placeholder, discarding the result. Every exported description and title was that character.
    """
    targets = [
        column
        for column in clean_columns(platform)
        if column in frame.columns and frame[column].dtype == pl.String
    ]

    if not targets:
        return frame

    return frame.with_columns(
        [
            pl.col(column)
            .map_elements(clean_text, return_dtype=pl.String)
            .alias(column)
            for column in targets
        ]
    )


def _pluck(hit: dict[str, Any], column: str) -> Any:
    """Resolves a dotted column against a hit, mirroring json_normalize + '_source.' stripping."""
    if column in ES_METADATA_FIELDS:
        return hit.get(column)

    node: Any = hit.get("_source")

    for part in column.split("."):
        if not isinstance(node, dict):
            return None

        node = node.get(part)

    return node


def extract_hits(platform: str, hits: Sequence[dict[str, Any]]) -> pl.DataFrame:
    """Projects raw hits onto the columns declared for the platform.

    Every declared column is always present, even when absent from these particular hits, so that
    each page writes an identical schema and the pages can be read back as one dataset.
    """
    columns = platform_columns(platform)
    data: dict[str, list[Any]] = {
        column: [_pluck(hit, column) for hit in hits] for column in columns
    }

    # strict=False lets mixed scalar types fall back to a common type instead of raising;
    # infer_schema_length=None scans every row, so a field first appearing late in a ragged
    # result is still typed correctly rather than silently dropped.
    return pl.DataFrame(data, strict=False, infer_schema_length=None)


def write_raw_page(query_id: UUID, request_id: UUID, frame: pl.DataFrame) -> Path:
    target = raw_page_path(query_id, request_id)

    target.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(target, compression=PARQUET_COMPRESSION)

    return target


def read_raw(query_id: UUID, request_ids: Sequence[UUID]) -> pl.DataFrame | None:
    """Reads raw pages back in the order given, so output ordering follows fetch order."""
    frames: list[pl.DataFrame] = []

    for request_id in request_ids:
        page = raw_page_path(query_id, request_id)

        if not page.exists():
            continue

        frames.append(pl.read_parquet(page))

    if not frames:
        return None

    return pl.concat(frames, how="vertical_relaxed")


def write_processed(query_id: UUID, frame: pl.DataFrame) -> Path:
    target = processed_path(query_id)

    target.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(target, compression=PARQUET_COMPRESSION)

    return target


def read_processed(query_id: UUID) -> pl.DataFrame | None:
    target = processed_path(query_id)

    if not target.exists():
        return None

    return pl.read_parquet(target)


def delete_dataset(query_id: UUID) -> None:
    target = dataset_dir(query_id)

    if target.exists():
        rmtree(target, ignore_errors=True)


def drop_empty_columns(frame: pl.DataFrame) -> pl.DataFrame:
    """Drops columns that are null for every row.

    Raw pages carry the full declared schema so pages stay concatenable; the processed output
    keeps only columns that actually carried data, matching what the previous pandas pipeline
    produced (it only kept columns json_normalize had found in the hits).
    """
    if frame.height == 0:
        return frame

    keep = [name for name in frame.columns if frame[name].null_count() < frame.height]

    return frame.select(keep)
