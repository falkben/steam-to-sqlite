# steam-to-sqlite

![main branch](https://github.com/falkben/steam-to-sqlite/actions/workflows/test.yml/badge.svg?branch=main) [![codecov](https://codecov.io/gh/falkben/steam-to-sqlite/branch/main/graph/badge.svg?token=ZPVU94M3XE)](https://codecov.io/gh/falkben/steam-to-sqlite)

Public [Steam](https://store.steampowered.com/) app and achievement data in a sqlite database

## Quick links

The database and deployments are updated automatically through GitHub actions.

| | |
|-|-|
|SQLite3 File|[database.db ⬇️](https://www.dropbox.com/s/i47qt3chrp9lr9e/database.db?dl=1) |
|[Datasette](https://datasette.io/) deployment|<https://steam-to-sqlite.fly.dev/>|
|GraphQL interface|<https://steam-to-sqlite.fly.dev/graphql>|

To preview what's included in the database schema, you can view [models.py](/steam2sqlite/models.py), which contains the [SQLModel](https://sqlmodel.tiangolo.com/) representation, or just explore on Datasette.

## Data exploration

The following are some plots generated from the data. Follow the Datasette links to view what's most recent.

- Steam games over time (and you thought _your_ Steam library was large!)

   ![Steam games over time](https://user-images.githubusercontent.com/653031/199382416-cf8c43f0-2cc5-47a5-99d7-ad7b32b41af9.png)

   [Datasette Link](https://steam-to-sqlite.fly.dev/database?sql=select%0D%0A++strftime%28%27%25Y%27%2C+steam_app.release_date%29+as+year%2C%0D%0A++sum%28count%28steam_app.pk%29%29+over+%28%0D%0A++++order+by%0D%0A++++++steam_app.release_date%0D%0A++%29+as+total%0D%0Afrom%0D%0A++steam_app%0D%0Awhere%0D%0A++steam_app.release_date+is+not+NULL%0D%0A++and+steam_app.release_date+%3E%3D+date%28%222003-01-01%22%29%0D%0A++and+steam_app.release_date+%3C+CURRENT_DATE%0D%0A++and+steam_app.type+%3D+%22game%22%0D%0Agroup+by%0D%0A++year%0D%0Aorder+by%0D%0A++steam_app.release_date+asc#g.mark=line&g.x_column=year&g.x_type=ordinal&g.y_column=total&g.y_type=quantitative)

- Games per genre (who knew there were so many indie games?!)

   ![Games per genre](https://user-images.githubusercontent.com/653031/199382566-bf2cc609-f2c3-4841-a871-3cb2605c32de.png)

   [Datasette Link](https://steam-to-sqlite.fly.dev/database?sql=select+genre.description%2C+count(steam_app.pk)+as+apps%0D%0Afrom+genre%0D%0Ajoin+genresteammapplink+on+genre_pk+%3D+genre.pk%0D%0Ajoin+steam_app+on+genresteammapplink.steam_app_pk+%3D+steam_app.pk%0D%0AGROUP+by+genre.pk%0D%0Aorder+by+apps+desc%3B#g.mark=bar&g.x_column=description&g.x_type=ordinal&g.y_column=apps&g.y_type=quantitative)

- Games with full controller support (stand-in for Steam Deck support)

   ![Games with full controller support over time](https://user-images.githubusercontent.com/653031/199390356-ad488ecd-e64b-4ca1-a5ba-0bc6ff3dd4cd.png)

   [Datasette Link](https://steam-to-sqlite.fly.dev/database?sql=select%0D%0A++strftime%28%27%25Y%27%2C+steam_app.release_date%29+as+year%2C%0D%0A++sum%28count%28steam_app.pk%29%29+over+%28%0D%0A++++order+by%0D%0A++++++steam_app.release_date%0D%0A++%29+as+total%0D%0Afrom%0D%0A++steam_app%0D%0Awhere%0D%0A++steam_app.release_date+is+not+NULL%0D%0A++and+steam_app.release_date+%3E%3D+date%28%222003-01-01%22%29%0D%0A++and+steam_app.release_date+%3C+CURRENT_DATE%0D%0A++and+steam_app.type+%3D+%22game%22%0D%0A++and+steam_app.controller_support+%3D%3D+%22full%22%0D%0Agroup+by%0D%0A++year%0D%0Aorder+by%0D%0A++steam_app.release_date+asc#g.mark=line&g.x_column=year&g.x_type=ordinal&g.y_column=total&g.y_type=quantitative)

Hopefully these inspire you to explore the data. If you find something you want to highlight, PRs are welcome!

## Install

To install the project locally:

1. Ensure you have Python >= 3.10. [pyenv](https://github.com/pyenv/pyenv) recommended
2. Create and activate a virtual environment: `python -m venv .venv && . .venv/bin/activate`
3. Install:
   - `pip install -r requirements.txt`
   - With dev. dependencies: `pip install -r requirements.txt -r dev-requirements.txt`
4. Install package: `pip install -e .` or w/ dev dependencies `pip install -e ".[dev]"`

## Manage dependencies

1. install/upgrade pip-tools: `pip install pip-tools -U` or globally with [pipx](https://github.com/pypa/pipx): `pipx install pip-tools`
2. Create lock files with:

   ```sh
   pip-compile -o requirements.txt pyproject.toml --quiet && \
   pip-compile --extra dev -o dev-requirements.txt pyproject.toml --quiet
   ```

3. Upgrade a package:

   ```sh
   pip-compile -o requirements.txt pyproject.toml --quiet --upgrade-package PACKAGE && \
   pip-compile --extra dev -o dev-requirements.txt pyproject.toml --quiet
   ```

4. Upgrade all packages with:

   ```sh
   pip-compile -o requirements.txt pyproject.toml --quiet --upgrade && \
   pip-compile --extra dev -o dev-requirements.txt pyproject.toml --quiet --upgrade
   ```

More here: <https://github.com/jazzband/pip-tools/>

## Run

Download a copy of the database and save locally to `database.db`

To verify installation:

```bash
python steam2sqlite/main.py --help
usage: main.py [-h] [-l [LIMIT]]

options:
  -h, --help            show this help message and exit
  -l [LIMIT], --limit [LIMIT]
                        limit runtime (minutes)
```

To run:

```sh
python steam2sqlite/main.py
```

Due to rate limits on the public Steam api, the program will take several days to iterate over all the Steam apps in the Steam catalog.

Limit the runtime in minutes with the `-l` or `--limit` argument:

```sh
python steam2sqlite/main.py --limit 1
```

Will run for 1 minutes and then (hopefully) exit cleanly with a database partially updated.

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

## Deploy to Fly

The deployment runs automatically with [GitHub actions](/.github/workflows/main.yml). To manually deploy:

1. install [flyctl](https://fly.io/docs/getting-started/installing-flyctl/)
2. `flyctl auth login`
3. Deploy:

    ```sh
    datasette publish fly database.db \
      --install datasette-graphql --install datasette-vega \
      --app steam-to-sqlite \
      --metadata datasette-data/metadata.json
    ```
