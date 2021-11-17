from datetime import datetime

from sqlmodel import Session, select

from steam2sqlite.models import Category, Genre, SteamApp


class InsertionError(Exception):
    pass


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.flush()
        return instance


def load_into_db(session: Session, data: dict) -> SteamApp:

    genres_data = data.get("genres") or []
    genres = [get_or_create(session, Genre, **dd) for dd in genres_data]

    categories_data = data.get("categories") or []
    categories = [get_or_create(session, Category, **dd) for dd in categories_data]

    metacritic_score, metacritic_url = None, None
    if "metacritic" in data:
        metacritic_score = data["metacritic"].get("score")
        metacritic_url = data["metacritic"].get("url")

    recommendations_total = None
    if "recommendations" in data:
        recommendations_total = data["recommendations"].get("total")

    achievements_total = None
    if "achievements" in data:
        achievements_total = data["achievements"].get("total")

    release_date = None
    if "release_date" in data and not (
        "coming_soon" in data["release_date"] and data["release_date"]["coming_soon"]
    ):
        release_date_str = data["release_date"].get("date")
        try:
            if release_date_str:
                release_date = datetime.strptime(release_date_str, "%b %d, %Y").date()
        except ValueError:
            raise InsertionError

    app_attrs = {
        "steam_appid": data["steam_appid"],
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
    steam_app = session.exec(
        select(SteamApp).where(SteamApp.steam_appid == data["steam_appid"])
    ).one_or_none()
    if steam_app:  # update
        for key, value in app_attrs.items():
            setattr(steam_app, key, value)
    else:  # create
        steam_app = SteamApp(**app_attrs)

    steam_app.categories = categories
    steam_app.genres = genres

    session.add(steam_app)
    session.commit()
    session.refresh(steam_app)

    return steam_app


def import_single_item(session: Session, item: dict) -> SteamApp | None:
    # hardcoded app data from api:
    # https://store.steampowered.com/api/appdetails/?appids=274190
    # import json
    # with open("broforce.json") as datafile:
    #     item = json.load(datafile)

    appid = list(item.keys())[0]
    if item[appid]["success"] is False:
        # todo: log the error/appid
        print(f"error encountered with appid {appid}")
        raise InsertionError

    data = item[appid]["data"]
    return load_into_db(session, data)


def get_appids_from_db(session: Session) -> list[tuple[int, datetime]]:
    return session.execute(
        select(SteamApp.steam_appid, SteamApp.updated).order_by(SteamApp.updated)
    ).all()
