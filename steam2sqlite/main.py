#!/usr/bin/env python3

import asyncio
import datetime
import json
from collections.abc import Sequence

import uvloop
from sqlmodel import Session, create_engine

from steam2sqlite.handler import InsertionError, get_appids_from_db, import_single_item
from steam2sqlite.navigator import make_requests

DAILY_API_LIMIT = 100_000
APPID_URL = "https://store.steampowered.com/api/appdetails/?appids={}"

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"


def get_appids_from_steam() -> list[tuple[int, str]]:
    # todo: eventually will be an API call but currently have it locally
    # http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json
    with open("steam_appids.json") as steam_appids_fp:
        appid_data = json.load(steam_appids_fp)

    return [(item["appid"], item["name"]) for item in appid_data["applist"]["apps"]]


def main(argv: Sequence[str] | None = None) -> int:

    uvloop.install()

    engine = create_engine(sqlite_url, echo=False)

    # get list of steam appids
    steam_appids_names = get_appids_from_steam()

    with Session(engine) as session:

        # query db for all appids we already have, sort by last_modified
        db_appids_updated = get_appids_from_db(session)

        # identify any missing appids -- these go on the top of our stack to process
        missing_appids = {appid for appid, _ in steam_appids_names} - {
            appid for appid, _ in db_appids_updated
        }

        # remove any appids that have been modified within the last 3 days
        db_appids = [
            appid
            for appid, updated in db_appids_updated
            if ((datetime.datetime.utcnow().date() - updated.date()).days > 3)
        ]

        appids_to_process = list(missing_appids) + db_appids

        urls = [APPID_URL.format(appid) for appid in appids_to_process]

        # ! limit our urls
        urls = urls[0:10]

        responses = asyncio.run(make_requests(urls))

        for resp in responses:
            item = resp.json()
            try:
                import_single_item(session, item)
            except InsertionError:
                # todo: store bad appids in separate table to exclude on future runs
                pass

    # do not go over DAILY_API_LIMIT

    # request batches of appids from steam
    # insert batches into database
    # write out to the database

    return 0


if __name__ == "__main__":
    exit(main())
