import json

import pytest
from sqlmodel import Session, create_engine
from steam2sqlite import handler, models

steam_appids_names = {620: "Portal 2", 659: "Portal 2 - Pre-order"}
SQLITE_URL = "sqlite://"


@pytest.fixture
def session():
    engine = create_engine(SQLITE_URL, echo=False)
    models.create_db_and_tables(engine)
    with Session(engine) as session:
        yield session


def get_apps_data(appids: list[str]):
    """'mocks' the get_apps_data function"""

    apps_data = []
    for appid in appids:
        with open(f"test_data/{appid}.json") as app_data_file:
            apps_data.append(json.load(app_data_file))
    return apps_data


def test_app_with_duplicated_appid(session):
    """portal 2 is listed more than once with different appids (620, 659)
    However the preorder (659) has an internal appid of 620
    We want to assert that we don't ingest dup items
    """

    dup_appid = "659"
    dup_app_data = get_apps_data([dup_appid])[0]

    # returned data reference a single steam appid (620)
    # we don't want to store the duplicated data

    assert dup_appid in dup_app_data
    assert dup_app_data[dup_appid]["success"]
    assert "steam_appid" in dup_app_data[dup_appid]["data"]

    with pytest.raises(handler.DataParsingError):
        handler.import_single_item(session, dup_app_data)


def test_ingest_item_twice(session: Session):

    appid = "620"
    app_data = get_apps_data([appid])[0]

    app = handler.import_single_item(session, app_data)
    app_double = handler.import_single_item(session, app_data)
    # todo: load app achievements
    handler.get_apps_achievements(session, [app])
    handler.get_apps_achievements(session, [app_double])

    # asserts on app
    assert app == app_double
    #  app is only in db once

    apps = (
        session.query(models.SteamApp).filter(models.SteamApp.appid == app.appid).all()
    )
    assert len(apps) == 1

    # genres
    genres = (
        session.query(models.Genre)
        .filter(models.Genre.steam_apps.any(appid=appid))
        .all()
    )
    assert len(genres) == len(app.genres)

    achievements = (
        session.query(models.Achievement)
        .filter(models.Achievement.steam_app == app)
        .all()
    )
    assert len(achievements) == app.achievements_total
