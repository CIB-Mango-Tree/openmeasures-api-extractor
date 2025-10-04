from dataclasses import dataclass


@dataclass
class FileExport:
    filename: str
    data: bytes
