# steam-to-sqlite

Public [Steam](https://store.steampowered.com/) app and achievement data in a sqlite database

## Quick links

The database and deployments are updated automatically through gitub actions.

| | |
|-|-|
|SQLite3 File|[database.db ⬇️](https://www.dropbox.com/s/i47qt3chrp9lr9e/database.db?dl=1) |
|[Datasette deployment](https://datasette.io/)|<https://steam-to-sqlite.vercel.app/>|
|GraphQL interface|<https://steam-to-sqlite.vercel.app/graphql>|

To preview the database schema, you can view [models.py](/steam2sqlite/models.py), which contains a [SQLModel](https://sqlmodel.tiangolo.com/) representation.

## Install

To install the project locally:

1. Ensure you have Python >= 3.10. [pyenv](https://github.com/pyenv/pyenv) recommended
2. install [poetry](https://python-poetry.org/) >= 1.1.11
3. `poetry install`

## Run

```sh
python steam2sqlite/main.py
```

Due to rate limits on the public Steam api, the program will take several days to iterate over all the Steam apps in the Steam catalog.

Limit the runtime in minutes with the `-l` or `--limit` argument:

```sh
python steam2sqlite/main.py --limit 10
```

Will run for 10 minutes and then (hopefully) exit cleanly with a database partially updated.

## Migrations

To upgrade db to current migration/revision

```sh
alembic upgrade head
```

Generate a migration/revision

```sh
alembic revision --autogenerate -m "MESSAGE"
```

Examine generated file in `migrations/versions`. Pay attention to table/column renames (they will be dropped/created in migration file).

## Deploy to Vercel

The deployment runs automatically with [github actions](/.github/workflows/main.yml). To manually deploy:

1. install [Vercel CLI](https://vercel.com/cli)
2. `vercel login`
3. Deploy:
    ```sh
    datasette publish vercel database.db \
    --install datasette-graphql \
    --project steam-to-sqlite`
    ```
