#!/usr/bin/env python3

from collections.abc import Sequence
from datetime import datetime

from sqlmodel import Session, create_engine, select

from models import Category, Genre, SteamApp

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


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

    genres_data = data["genres"]
    genres = [get_or_create(session, Genre, **dd) for dd in genres_data]

    categories_data = data["categories"]
    categories = [get_or_create(session, Category, **dd) for dd in categories_data]

    metacritic_score, metacritic_url = None, None
    if data.get("metacritic"):
        metacritic_score = data["metacritic"].get("score")
        metacritic_url = data["metacritic"].get("url")

    recommendations_total = None
    if data.get("recommendations"):
        recommendations_total = data["recommendations"].get("total")

    achievements_total = None
    if data.get("achievements"):
        achievements_total = data["achievements"].get("total")

    release_date = None
    if data.get("release_date"):
        release_date = data["release_date"].get("date")

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
        "release_date": datetime.strptime(release_date, "%b %d, %Y").date(),
    }
    steam_app = session.exec(
        select(SteamApp).where(SteamApp.steam_appid == data["steam_appid"])
    ).one_or_none()
    if steam_app:
        # update
        for key, value in app_attrs.items():
            setattr(steam_app, key, value)
    else:
        # create
        steam_app = SteamApp(**app_attrs)

    steam_app.categories = categories
    steam_app.genres = genres

    session.add(steam_app)
    session.commit()
    session.refresh(steam_app)

    return steam_app


def import_single_item(session: Session):
    import json

    with open("broforce.json") as datafile:
        resp = json.load(datafile)

    appid = list(resp.keys())[0]
    data = resp[appid]["data"]

    steam_app = load_into_db(session, data)
    print(steam_app)


def main(argv: Sequence[str] | None = None) -> int:
    with Session(engine) as session:
        import_single_item(session)
    return 0


if __name__ == "__main__":
    exit(main())
