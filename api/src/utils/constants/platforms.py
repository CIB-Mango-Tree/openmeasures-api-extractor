PLATFORMS: dict[str, dict[str, str | list[str]]] = {
    "bluesky": {
        "readable": "Bluesky",
        "created_at_column": "createdAt",
        "columns": [
            "_index",
            "_id",
            "author",
            "createdAt",
            "text",
            "embed.external.description",
            "embed.external.title",
            "authorProfile.handle",
            "authorProfile.display_name",
            "authorProfile._id",
            "authorProfile.did",
        ],
        # Free-text columns passed through clean_text (HTML unescaping + mojibake repair).
        "clean_columns": [
            "text",
            "embed.external.description",
            "embed.external.title",
        ],
    },
    "truth_social": {
        "readable": "Truth Social",
        "created_at_column": "created_at",
        "columns": [
            "account.display_name",
            "account.username",
            "account.id",
            "content_cleaned",
            "created_at",
            "datatype",
            "mentions",
            "_id",
            "in_reply_to_account_id",
            "in_reply_to_id",
            "reblog.id",
            "replies_count",
            "reblogs_count",
        ],
        # Left empty to preserve existing behaviour: the previous pipeline only ever cleaned the
        # bluesky fields. content_cleaned arrives pre-sanitized from the API.
        "clean_columns": [],
    },
}
