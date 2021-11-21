import json

import pytest
from sqlmodel import Session, create_engine
from steam2sqlite import handler
from steam2sqlite.main import SQLITE_URL

steam_appids_names = {659: "some_name"}


@pytest.fixture
def session():
    # todo: look into create_mock_engine
    engine = create_engine(SQLITE_URL, echo=False)
    with Session(engine) as session:
        yield session


def test_app_with_duplicated_appid(session):

    # portal 2 is listed more than once with different appids (620, 659)
    # returned data reference a single steam appid (620)
    # we don't want to store the duplicated data
    appid = "659"

    # mocking the get_apps_data function
    # app_data = handler.get_apps_data(session, steam_appids_names, [appid])[0]
    with open("test_data/659.json") as app_data_file:
        app_data = json.load(app_data_file)

    assert appid in app_data
    assert app_data[appid]["success"]
    assert "steam_appid" in app_data[appid]["data"]

    with pytest.raises(handler.DataParsingError):
        handler.import_single_item(session, app_data)
