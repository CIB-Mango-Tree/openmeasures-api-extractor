from ..db.models import Query, QueryRequest, QueryLimit
from ..db.repositories import QueryRequestRepository, QueryLimitRepository
from ..settings import API_URL
from requests import get
from asyncio import run


def fetch_data(query) -> None:
    async def func() -> None:
        all_hits = []
        while True:
            try:
                response = get(API_URL, params=params_copy)
                response.raise_for_status()  # error for any http issues
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])

                if not hits:
                    all_hits.extend(hits)

                if len(hits) < 10000:
                    break

                last_created_at = hits[-1]["_source"].get(field)

                if not last_created_at:
                    print("No 'created_at' found in the last hit.")
                    break

                print(last_created_at)
                params_copy["since"] = last_created_at

            except Exception as e:
                print(f"Error occurred: {e}")
                break


run(func())
