from collections.abc import Sequence
from datetime import date, datetime
from typing import Optional  # to be removed once Pydantic supports Union operator
from typing import List

from sqlmodel import Field, Relationship, SQLModel, create_engine


class CategorySteamAppLink(SQLModel, table=True):
    category_pk: Optional[int] = Field(
        default=None, foreign_key="category.pk", primary_key=True
    )
    steam_app_pk: Optional[int] = Field(
        default=None, foreign_key="steam_app.pk", primary_key=True
    )


class Category(SQLModel, table=True):
    pk: Optional[int] = Field(default=None, primary_key=True)
    id: int
    description: str
    steam_apps: List["SteamApp"] = Relationship(
        back_populates="categories", link_model=CategorySteamAppLink
    )


class GenreSteammAppLink(SQLModel, table=True):
    genre_pk: Optional[int] = Field(
        default=None, foreign_key="genre.pk", primary_key=True
    )
    steam_app_pk: Optional[int] = Field(
        default=None, foreign_key="steam_app.pk", primary_key=True
    )


class Genre(SQLModel, table=True):
    pk: Optional[int] = Field(default=None, primary_key=True)
    id: int
    description: str
    steam_apps: List["SteamApp"] = Relationship(
        back_populates="genres", link_model=GenreSteammAppLink
    )


class SteamApp(SQLModel, table=True):
    __tablename__ = "steam_app"
    pk: Optional[int] = Field(default=None, primary_key=True)
    appid: int = Field(index=True, sa_column_kwargs={"unique": True})
    type: Optional[str] = None
    is_free: Optional[bool] = False
    name: str = Field(index=True)
    controller_support: Optional[str] = None
    metacritic_score: Optional[int] = None
    metacritic_url: Optional[str] = Field(default=None, index=False)
    recommendations: Optional[int] = None
    achievements_total: Optional[int] = None
    release_date: Optional[date] = None

    created: datetime = Field(sa_column_kwargs={"default": datetime.utcnow})
    updated: datetime = Field(
        sa_column_kwargs={"default": datetime.utcnow, "onupdate": datetime.utcnow}
    )

    categories: List[Category] = Relationship(
        back_populates="steam_apps", link_model=CategorySteamAppLink
    )
    genres: List[Genre] = Relationship(
        back_populates="steam_apps", link_model=GenreSteammAppLink
    )


class AppidError(SQLModel, table=True):
    """Table to store appids to skip"""

    __tablename__ = "appid_error"

    pk: Optional[int] = Field(default=None, primary_key=True)
    appid: int = Field(index=False, sa_column_kwargs={"unique": True})
    name: Optional[str] = Field(default=None, index=False)
    reason: Optional[str] = Field(default=None, index=False)


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def main(argv: Sequence[str] | None = None) -> int:
    create_db_and_tables()
    return 0


if __name__ == "__main__":
    exit(main())
