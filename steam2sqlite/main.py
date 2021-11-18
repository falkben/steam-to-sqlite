#!/usr/bin/env python3

import asyncio
import datetime
import json
from collections.abc import Sequence

import uvloop
from httpx import HTTPStatusError
from sqlmodel import Session, create_engine

from steam2sqlite.handler import (
    DataParsingError,
    get_appids_from_db,
    get_error_appids,
    import_single_item,
    record_appid_error,
)
from steam2sqlite.navigator import make_requests

DAILY_API_LIMIT = 100_000
APPID_URL = "https://store.steampowered.com/api/appdetails/?appids={}"

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"


def get_appids_from_steam() -> dict[int, str]:
    # todo: eventually will be an API call but currently have it locally
    # http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json
    with open("steam_appids.json") as steam_appids_fp:
        appid_data = json.load(steam_appids_fp)

    return {item["appid"]: item["name"] for item in appid_data["applist"]["apps"]}


def main(argv: Sequence[str] | None = None) -> int:

    uvloop.install()

    engine = create_engine(sqlite_url, echo=False)

    # get dict of steam appids: names
    steam_appids_names = get_appids_from_steam()

    with Session(engine) as session:

        # query db for all appids we already have, sort by last_modified
        db_appids_updated = get_appids_from_db(session)

        # identify any missing appids -- these go on the top of our stack to process
        missing_appids = set(steam_appids_names.keys()) - {
            appid for appid, _ in db_appids_updated
        }

        # remove any appids that have been modified within the last 3 days
        db_appids = [
            appid
            for appid, updated in db_appids_updated
            if ((datetime.datetime.utcnow().date() - updated.date()).days > 3)
        ]

        appids_to_process_with_error_ids = list(missing_appids) + db_appids

        # remove any appids that have been flagged as errors from previous runs
        error_appids = get_error_appids(session)
        appids_to_process = [
            appid
            for appid in appids_to_process_with_error_ids
            if appid not in set(error_appids)
        ]

        urls = [APPID_URL.format(appid) for appid in appids_to_process]

        # ! do not go over DAILY_API_LIMIT
        urls = urls[0:10]

        responses = asyncio.run(make_requests(urls))

        for resp in responses:
            try:
                resp.raise_for_status()
            except HTTPStatusError as e:
                appid = int(str(resp.request.url).split("=")[-1])
                reason = f"Response code: {e.response.status_code}, {e}"
                print(reason)
                record_appid_error(session, appid, steam_appids_names[appid], reason)

            try:
                item = resp.json()
                import_single_item(session, item)
            except DataParsingError as e:
                record_appid_error(
                    session, e.appid, steam_appids_names[e.appid], e.reason
                )

    # request batches of appids from steam
    # insert batches into database
    # write out to the database

    return 0


if __name__ == "__main__":
    exit(main())
