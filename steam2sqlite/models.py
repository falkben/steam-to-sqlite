from datetime import date, datetime
from typing import Optional  # to be removed once Pydantic supports Union operator
from typing import List

from sqlmodel import Field, Relationship, SQLModel


class CategorySteamAppLink(SQLModel, table=True):
    category_pk: Optional[int] = Field(
        default=None, foreign_key="category.pk", primary_key=True
    )
    steam_app_pk: Optional[int] = Field(
        default=None, foreign_key="steam_app.pk", primary_key=True
    )


class Category(SQLModel, table=True):
    pk: Optional[int] = Field(default=None, primary_key=True)
    id: int = Field()
    description: str = Field()
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
    id: int = Field()
    description: str = Field()
    steam_apps: List["SteamApp"] = Relationship(
        back_populates="genres", link_model=GenreSteammAppLink
    )


class SteamApp(SQLModel, table=True):
    __tablename__ = "steam_app"  # type: ignore
    pk: Optional[int] = Field(default=None, primary_key=True)
    appid: int = Field(index=True, sa_column_kwargs={"unique": True})
    type: Optional[str] = Field(default=None)
    is_free: Optional[bool] = Field(default=False)
    name: str = Field(index=True)
    controller_support: Optional[str] = Field(default=None)
    metacritic_score: Optional[int] = Field(default=None)
    metacritic_url: Optional[str] = Field(default=None)
    recommendations: Optional[int] = Field(default=None)
    achievements_total: int = Field(default=0)
    release_date: Optional[date] = Field(default=None)
    initial_price: Optional[int] = Field(default=None)
    current_price: Optional[int] = Field(default=None)

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
    achievements: List["Achievement"] = Relationship(
        back_populates="steam_app",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Achievement(SQLModel, table=True):
    pk: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field()
    percent: float = Field()

    steam_app_pk: Optional[int] = Field(default=None, foreign_key="steam_app.pk")
    steam_app: Optional[SteamApp] = Relationship(back_populates="achievements")


class AppidError(SQLModel, table=True):
    """Table to store appids to skip"""

    __tablename__ = "appid_error"  # type: ignore

    pk: Optional[int] = Field(default=None, primary_key=True)
    appid: int = Field(sa_column_kwargs={"unique": True})
    name: Optional[str] = Field(default=None)
    reason: Optional[str] = Field(default=None)


def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)
