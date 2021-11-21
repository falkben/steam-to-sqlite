#!/usr/bin/env python3

import asyncio
import datetime
import json
import os
import time
from argparse import ArgumentParser
from collections.abc import Sequence

import httpx
import uvloop
from dotenv import load_dotenv
from rich import print
from sqlmodel import Session, create_engine

from steam2sqlite import APPIDS_URL, BATCH_SIZE, utils
from steam2sqlite.handler import (
    get_appids_from_db,
    get_apps_achievements,
    get_apps_data,
    get_error_appids,
    store_apps_achievements,
    store_apps_data,
)
from steam2sqlite.models import create_db_and_tables

load_dotenv()

APPIDS_FILE = os.getenv("APPIDS_FILE")

sqlite_file_name = "database.db"
SQLITE_URL = f"sqlite:///{sqlite_file_name}"


def get_appids_from_steam(local_file: str = None) -> dict[int, str]:
    if local_file:
        with open(local_file) as steam_appids_fp:
            appid_data = json.load(steam_appids_fp)
    else:
        try:
            resp = httpx.get(APPIDS_URL)
            appid_data = resp.json()
            time.sleep(1)
        except httpx.HTTPStatusError as e:
            print(e)
            raise

    return {item["appid"]: item["name"] for item in appid_data["applist"]["apps"]}


def main(argv: Sequence[str] | None = None) -> int:

    parser = ArgumentParser()
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=None,
        nargs="?",
        const=1,
        help="limit the number of batches to process",
    )
    args = parser.parse_args(argv)

    uvloop.install()

    engine = create_engine(SQLITE_URL, echo=False)
    create_db_and_tables(engine)

    # From steam api, dict of: {appids: names}
    steam_appids_names = get_appids_from_steam(APPIDS_FILE)

    with Session(engine) as session:

        # query db for all appids we already have, sort by last_modified
        db_appids_updated = get_appids_from_db(session)

        # identify any missing appids -- these go on the top of our stack to process
        missing_appids = set(steam_appids_names.keys()) - {
            appid for appid, _ in db_appids_updated
        }

        # remove any appids that have been modified recently
        db_appids = [
            appid
            for appid, updated in db_appids_updated
            if ((datetime.datetime.utcnow().date() - updated.date()).days > 3)
        ]

        appids_missing_and_older = list(missing_appids) + db_appids

        # remove any appids that have been flagged as errors from previous runs
        error_appids = get_error_appids(session)
        appids_to_process = [
            appid
            for appid in appids_missing_and_older
            if appid not in set(error_appids)
        ]

        for iters, appids in enumerate(
            utils.grouper(appids_to_process, BATCH_SIZE, fillvalue=None)
        ):

            apps_data = get_apps_data(session, steam_appids_names, appids)
            apps = store_apps_data(session, steam_appids_names, apps_data)

            apps_with_achievements = [app for app in apps if app.achievements_total > 0]
            if apps_with_achievements:
                apps_achievements = utils.delay_by(len(apps_with_achievements))(
                    asyncio.run
                )(get_apps_achievements(apps_with_achievements))
                store_apps_achievements(
                    session, apps_with_achievements, apps_achievements
                )

            # todo: support a time limit instead
            if args.limit and iters + 1 >= args.limit:
                break

    return 0


if __name__ == "__main__":
    exit(main())
