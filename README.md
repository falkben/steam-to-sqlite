# steam-to-sqlite

Public [Steam](https://store.steampowered.com/) app and achievement data in a sqlite database

## Quick links

The database and deployments are updated automatically through gitub actions.

- View the data inside a [Datasette](https://datasette.io/) deployment at: <https://steam-to-sqlite.vercel.app/>. A graphql interface can be accessed at <https://steam-to-sqlite.vercel.app/graphql>.
- Download the most recent sqlite [database.db](https://github.com/falkben/steam2sqlite/raw/main/database.db) file.

To preview the database schema without, you can view [models.py](/steam2sqlite/models.py), which contains a [SQLModel](https://sqlmodel.tiangolo.com/) representation.

## Dev

To install the project locally:

1. Ensure you have Python >= 3.10. [pyenv](https://github.com/pyenv/pyenv) recommended
2. install [poetry](https://python-poetry.org/) >= 1.1.11
3. `poetry install`

## Run

```sh
python steam2sqlite/main.py
```

Note: Due to the rate limits on the public steam api, the program will take several days to iterate over all the steam apps in the steam catalog.

Limit the runtime in minutes with the `-l` or `--limit` argument:

```sh
python steam2sqlite/main.py --limit 10
```

Will run for 10 minutes and then (hopefully) exit cleanly with a database partially updated.

## Deploy to vercel

The deployment runs automatically with [github actions](/.github/workflows/main.yml). To manually deploy:

1. install [vercel](https://vercel.com/cli)
2. `vercel login`
3. Deploy:
    ```sh
    datasette publish vercel database.db \
    --install datasette-graphql \
    --project steam-to-sqlite`
    ```
