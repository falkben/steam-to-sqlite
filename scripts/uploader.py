#!/usr/bin/env python3

# partially vendored from
# https://github.com/dropbox/dropbox-sdk-python/blob/cc17caf7dc325708309aa52807621c6c48d7e349/example/updown.py

import datetime
import os
import time
from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path

import dropbox
from dotenv import load_dotenv

load_dotenv()


TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")


def upload(dbx, fullname, destination, overwrite=True):
    """Upload a file.
    Return the request response, or None in case of error.
    """
    mode = (
        dropbox.files.WriteMode.overwrite if overwrite else dropbox.files.WriteMode.add
    )
    mtime = os.path.getmtime(fullname)
    with open(fullname, "rb") as f:
        data = f.read()
    try:
        res = dbx.files_upload(
            data,
            destination,
            mode,
            client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
            mute=True,
        )
    except dropbox.exceptions.ApiError as err:
        print("*** API error", err)
        return None
    print("uploaded as", res.name.encode("utf8"))
    return res


def main(argv: Sequence[str] | None = None) -> int:
    parser = ArgumentParser()
    parser.add_argument("filename", help="Full path to local filename")
    parser.add_argument("destination", help="Full path to the destination")
    parser.add_argument(
        "--token",
        default=TOKEN,
        help="Access token (see https://www.dropbox.com/developers/apps)",
    )
    args = parser.parse_args(argv)

    if not args.token:
        print("--token is mandatory")
        return 2

    filename = Path(args.filename)
    if not filename.exists():
        print("filename doesn't exist")
        return 2

    dbx = dropbox.Dropbox(args.token)

    upload(dbx, filename, args.destination)

    return 0


if __name__ == "__main__":
    exit(main())
