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
    """'mocks' the handler.get_apps_data function"""

    # todo: actually mock the handler function replacing the url requests w/ static data

    apps_data = []
    for appid in appids:
        with open(f"test_data/{appid}.json") as app_data_file:
            apps_data.append(json.load(app_data_file))
    return apps_data


def get_apps_achievements(
    apps: list[models.SteamApp],
) -> list[tuple[models.SteamApp, list[dict]]]:
    """'mocks' handler.get_apps_achievements function"""

    # todo: actually mock the handler function replacing the url requests w/ static data

    apps_achievements_data = []
    for app in apps:
        with open(f"test_data/{app.appid}_achievements.json") as app_achievement_fh:
            achievement_data = json.load(app_achievement_fh)["achievementpercentages"][
                "achievements"
            ]
        apps_achievements_data.append((app, achievement_data))
    return apps_achievements_data


@pytest.fixture
def portal_app(session):
    app_data = get_apps_data(["620"])[0]
    app = handler.import_single_app(session, app_data)
    return app


@pytest.fixture
def portal_achievements(session, portal_app):
    apps_achievements_data = get_apps_achievements([portal_app])
    handler.store_apps_achievements(session, apps_achievements_data)


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
        handler.import_single_app(session, dup_app_data)


def test_ingest_item_twice(session: Session):

    appid = "620"
    app_data = get_apps_data([appid])[0]

    app = handler.import_single_app(session, app_data)
    apps_achievements_data = get_apps_achievements([app])
    handler.store_apps_achievements(session, apps_achievements_data)

    # now ingest the data again
    app_double = handler.import_single_app(session, app_data)
    apps_achievements_data = get_apps_achievements([app])
    handler.store_apps_achievements(session, apps_achievements_data)

    # assert that the two instances are the same
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


def test_updates_on_diff_app_data(session: Session, portal_app: models.SteamApp):
    """assert updates on new app data"""

    appid = "620"
    app_data = get_apps_data([appid])[0]

    assert portal_app.is_free is False
    app_data[appid]["data"]["is_free"] = True

    updated_app = handler.import_single_app(session, app_data)
    assert updated_app.is_free is True

    assert portal_app == updated_app


def test_updates_on_diff_achievement_data(
    session: Session, portal_app: models.SteamApp, portal_achievements
):
    """assert updates on diff achievement data"""
    apps_achievements_data = get_apps_achievements([portal_app])
    portal_achievements_data = apps_achievements_data[0]
    modified_achievement_name = portal_achievements_data[1][0]["name"]
    portal_achievements_data[1][0]["percent"] = 100
    handler.store_apps_achievements(session, [portal_achievements_data])

    modified_achievement = next(
        (
            achievement
            for achievement in portal_app.achievements
            if achievement.name == modified_achievement_name
        ),
        None,
    )
    assert modified_achievement.percent == 100


def test_duplicate_acheievemnts_on_app(
    session: Session, portal_app: models.SteamApp, portal_achievements
):
    """App with duplicated achievements
    assert clear out achievements with updates
    """

    # duplicate the first achievement
    first_achievement = portal_app.achievements[0]
    a = models.Achievement(
        name=first_achievement.name, percent=first_achievement.percent
    )
    portal_app.achievements.append(a)
    session.commit()

    # assert we have a duplicate
    result = (
        session.query(models.Achievement)
        .filter_by(name=first_achievement.name, steam_app=portal_app)
        .all()
    )
    assert len(result) == 2
    assert portal_app.achievements_total == len(portal_app.achievements) - 1

    # set first achievement percent to something diff for assertions
    apps_achievements_data = get_apps_achievements([portal_app])
    portal_achievements_data = apps_achievements_data[0]
    modified_achievement_name = portal_achievements_data[1][0]["name"]
    portal_achievements_data[1][0]["percent"] = 100

    # now update
    handler.store_apps_achievements(session, [portal_achievements_data])

    # assert we got an update
    modified_achievement = next(
        (
            achievement
            for achievement in portal_app.achievements
            if achievement.name == modified_achievement_name
        ),
        None,
    )
    assert modified_achievement.percent == 100

    # assert there are the correct number of achievements
    assert portal_app.achievements_total == len(portal_app.achievements)

    # assert we only have 51 achievements total in the db (cascade delete)
    assert len(session.query(models.Achievement).all()) == portal_app.achievements_total


def test_update_column_updated(session: Session, portal_app: models.SteamApp):

    initial_updated = portal_app.updated

    # assert our initial data
    assert portal_app.is_free is False

    # make an update
    portal_app.is_free = True
    session.add(portal_app)
    session.commit()
    session.refresh(portal_app)

    assert portal_app.updated > initial_updated
