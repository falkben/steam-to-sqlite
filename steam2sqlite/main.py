#!/usr/bin/env python3

import datetime
import json
from collections.abc import Sequence

import uvloop
from sqlmodel import Session, create_engine

import utils
from steam2sqlite import APPID_URL, BATCH_SIZE
from steam2sqlite.handler import (
    get_and_store_app_data,
    get_appids_from_db,
    get_apps_achievements,
    get_error_appids,
)

sqlite_file_name = ".private/database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"


def get_appids_from_steam() -> dict[int, str]:
    # todo: eventually will be an API call but currently have it locally
    # https://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json
    with open(".private/steam_appids.json") as steam_appids_fp:
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

        urls_total = (APPID_URL.format(appid) for appid in appids_to_process)

        for urls in utils.grouper(urls_total, BATCH_SIZE, fillvalue=None):

            apps = get_and_store_app_data(session, steam_appids_names, urls)

            apps_with_achievements = [app for app in apps if app.achievements_total > 0]
            # dynamically delay our next set of API calls
            utils.delay_by(len(apps_with_achievements))(get_apps_achievements)(
                session, apps_with_achievements
            )

    return 0


if __name__ == "__main__":
    exit(main())
