#!/usr/bin/env python3

import asyncio
import json
from collections.abc import Sequence

import uvloop
from sqlmodel import Session, create_engine

from steam2sqlite.handler import import_single_item
from steam2sqlite.navigator import make_requests

DAILY_API_LIMIT = 100_000

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"


def get_appids() -> list[tuple[int, str]]:
    # todo: eventually will be an API call but currently have it locally
    # http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json
    with open("steam_appids.json") as steam_appids_fp:
        appid_data = json.load(steam_appids_fp)

    return [(item["appid"], item["name"]) for item in appid_data["applist"]["apps"]]


def main(argv: Sequence[str] | None = None) -> int:

    uvloop.install()

    engine = create_engine(sqlite_url, echo=True)

    # get list of steam appids
    steam_app_ids = get_appids()

    # query db for all appids we already have, sort by last_modified
    # identify any missing appids -- these go on the top of our stack to process
    # additional appids to process are in order of last_modified
    # do not go over DAILY_API_LIMIT

    # request batches of appids from steam
    # insert batches into database
    # write out to the database

    # responses = asyncio.run(make_requests(urls))
    # with Session(engine) as session:
    #     import_single_item(session)
    return 0


if __name__ == "__main__":
    exit(main())
