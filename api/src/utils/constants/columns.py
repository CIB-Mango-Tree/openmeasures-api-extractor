DATAFRAME_COLUMNS = {
    "bluesky": [
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
    "truth_social": [
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
}

TIMESTAMP_COLUMNS = {"bluesky": "createdAt", "truth_social": "created_at"}
