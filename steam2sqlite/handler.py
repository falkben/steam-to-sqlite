import asyncio
import json
import sqlite3
from datetime import datetime

import httpx
import sqlalchemy.exc
from loguru import logger
from sqlmodel import Session, select

from steam2sqlite import ACHIEVEMENT_URL, APPID_URL, BATCH_SIZE, navigator, utils
from steam2sqlite.models import Achievement, AppidError, Category, Genre, SteamApp


class DataParsingError(Exception):
    def __init__(self, appid: int, reason: str = ""):
        self.appid = appid
        self.reason = reason


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.flush()
        return instance


def update_or_create(session, model, filterargs, **kwargs):

    try:
        instance = session.exec(select(model).filter_by(**filterargs)).one_or_none()
    except sqlalchemy.exc.MultipleResultsFound:
        logger.error(
            f"multiple results found for filter arguments: {filterargs} on model {model}"
        )
        raise

    if instance:  # update
        for key, value in kwargs.items():
            setattr(instance, key, value)
    else:  # create
        instance = model(**kwargs)

    return instance


def attach_achievements_to_app(
    session: Session, app_achievements_dict: list[dict], app: SteamApp
):

    for achievement_dict in app_achievements_dict:
        achievement_args = achievement_dict | {"steam_app": app}  # joining dicts
        update_or_create(
            session,
            Achievement,
            {"steam_app": app, "name": achievement_dict["name"]},
            **achievement_args,
        )

    session.commit()


def clear_and_store_achievements(
    session: Session, app_achievements_dict: list[dict], app: SteamApp
):
    app.achievements = []
    session.commit()
    session.refresh(app)

    for achievement_dict in app_achievements_dict:
        inst = Achievement(**achievement_dict)
        app.achievements.append(inst)
    session.commit()


def get_apps_achievements(apps: list[SteamApp]) -> list[tuple[SteamApp, list[dict]]]:

    urls = [ACHIEVEMENT_URL.format(app.appid) for app in apps]
    responses = asyncio.run(navigator.make_requests(urls))

    apps_achievements_data = []
    for app, resp in zip(apps, responses):
        # make_requests inserts exceptions into the responses list
        if isinstance(resp, navigator.NavigatorError):
            logger.error(f"Error getting achievement data for {app.appid}")
            continue

        try:
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, json.JSONDecodeError):
            logger.error(f"Error getting achievements for appid: {app.appid}")
            continue

        if (
            "achievementpercentages" in data
            and "achievements" in data["achievementpercentages"]
        ):
            apps_achievements_data.append(
                (app, data["achievementpercentages"]["achievements"])
            )
        else:
            logger.error(f"Error getting achievements for appid: {app.appid}")

    return apps_achievements_data


def store_apps_achievements(
    session: Session, apps_achievements_data: list[tuple[SteamApp, list[dict]]]
):
    for app_achievement_data in apps_achievements_data:
        app, achievement_data = app_achievement_data
        try:
            attach_achievements_to_app(session, achievement_data, app)
        except sqlalchemy.exc.MultipleResultsFound:
            # clear out achievements and store them fresh
            clear_and_store_achievements(session, achievement_data, app)


def load_app_into_db(session: Session, data: dict) -> SteamApp:

    genres_data = data.get("genres") or []
    if genres_data:
        # deduplicate
        genres_data = list({v["id"]: v for v in genres_data}.values())
    genres = [get_or_create(session, Genre, **dd) for dd in genres_data]

    categories_data = data.get("categories") or []
    if categories_data:
        # deduplicate
        categories_data = list({v["id"]: v for v in categories_data}.values())
    categories = [get_or_create(session, Category, **dd) for dd in categories_data]

    metacritic_score, metacritic_url = None, None
    if "metacritic" in data:
        metacritic_score = data["metacritic"].get("score")
        metacritic_url = data["metacritic"].get("url")

    recommendations_total = None
    if "recommendations" in data:
        recommendations_total = data["recommendations"].get("total")

    achievements_total = 0
    if "achievements" in data:
        achievements_total = data["achievements"].get("total", 0)

    release_date = None
    if "release_date" in data and not (
        "coming_soon" in data["release_date"] and data["release_date"]["coming_soon"]
    ):
        release_date_str = data["release_date"].get("date")
        try:
            if release_date_str:
                release_date = datetime.strptime(release_date_str, "%b %d, %Y").date()
        except ValueError:
            # todo: log this error
            pass

    app_attrs = {
        "appid": data["steam_appid"],
        "type": data["type"],
        "is_free": data.get("is_free"),
        "name": data["name"],
        "controller_support": data.get("controller_support"),
        "metacritic_score": metacritic_score,
        "metacritic_url": metacritic_url,
        "recommendations": recommendations_total,
        "achievements_total": achievements_total,
        "release_date": release_date,
    }
    steam_app = update_or_create(
        session, SteamApp, {"appid": data["steam_appid"]}, **app_attrs
    )

    steam_app.categories = categories
    steam_app.genres = genres

    steam_app.updated = datetime.utcnow()

    session.add(steam_app)
    session.commit()
    session.refresh(steam_app)

    return steam_app


def import_single_app(session: Session, item: dict) -> SteamApp:

    appid = list(item.keys())[0]
    if item[appid]["success"] is False:
        raise DataParsingError(int(appid), reason="Response from api: success=False")

    data = item[appid]["data"]

    if int(appid) != data["steam_appid"]:
        raise DataParsingError(
            int(appid),
            reason=f"duplicate entry with current appid {appid} and steam appid: {data['steam_appid']}",
        )

    try:
        app = load_app_into_db(session, data)
    except (sqlite3.DatabaseError, sqlalchemy.exc.IntegrityError) as e:
        raise DataParsingError(int(appid), reason=f"Database error: {e}")

    return app


def get_appids_from_db(session: Session) -> list[tuple[int, datetime]]:
    return session.exec(
        select(SteamApp.appid, SteamApp.updated).order_by(SteamApp.updated.asc())  # type: ignore
    ).all()


def get_error_appids(session: Session) -> list[int]:
    return session.exec(select(AppidError.appid)).all()


def record_appid_error(
    session, appid: int, name: str | None = None, reason: str | None = None
):
    get_or_create(
        session, AppidError, **{"appid": appid, "name": name, "reason": reason}
    )
    session.commit()


# delay for rate limiting
@utils.delay_by(BATCH_SIZE)
def get_apps_data(
    session: Session, steam_appids_names: dict[int, str], appids: list[int]
) -> list[dict]:

    urls = [APPID_URL.format(appid) for appid in appids if appid is not None]
    responses = asyncio.run(navigator.make_requests(urls))

    apps_data = []
    for appid, resp in zip(appids, responses):
        # make_requests inserts exceptions into the responses list
        if isinstance(resp, navigator.NavigatorError):
            logger.error(f"Error getting app data for {appid}")
            record_appid_error(session, appid, steam_appids_names[appid], f"{resp}")
            continue

        try:
            resp.raise_for_status()
            item = resp.json()
            apps_data.append(item)
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            logger.error(f"Http error with appid: {appid}")
            record_appid_error(session, appid, steam_appids_names[appid], f"{e}")

    return apps_data


def store_apps_data(
    session: Session, steam_appids_names: dict[int, str], apps_data: list[dict]
) -> list[SteamApp]:
    apps = []
    for app_data in apps_data:
        try:
            app = import_single_app(session, app_data)
            apps.append(app)
        except DataParsingError as e:
            logger.error(f"Error for appid: {e.appid}, reason: {e.reason}")
            record_appid_error(
                session, e.appid, steam_appids_names.get(e.appid, "unknown"), e.reason
            )
    return apps
