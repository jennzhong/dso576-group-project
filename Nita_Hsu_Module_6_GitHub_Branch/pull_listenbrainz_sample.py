"""Download the project's documented raw ListenBrainz sample."""

import csv
import json
import time
from pathlib import Path
from urllib.parse import quote

import requests


API_ROOT = "https://api.listenbrainz.org/1"
OUTPUT_PATH = Path(__file__).resolve().with_name("listenbrainz_sample.csv")

# These are the five users listed in project-start.md for the documented
# sample. Search them through ListenBrainz rather than assuming they still
# exist, then independently check the documented 50-listen minimum.
SAMPLE_USERNAMES = (
    "iliekcomputers",
    "H-music",
    "s_john_s",
    "John V",
    "music_af",
)
MINIMUM_LISTENS = 50
MAX_LISTENS_PER_USER = 500
# project-start.md describes using no more than 100 listens per request.
PAGE_SIZE = 100

# ListenBrainz requires a descriptive User-Agent with a contact URL and no
# more than one API request per second.
HEADERS = {
    "User-Agent": (
        "DSO576-EmergingArtistSample/1.0 "
        "(https://github.com/jennzhong/dso576-group-project)"
    )
}
MIN_SECONDS_BETWEEN_REQUESTS = 1.05
MAX_RETRIES = 5

CSV_COLUMNS = (
    "username",
    "listened_at",
    "track_name",
    "artist_name",
    "release_name",
    "recording_msid",
    "artist_mbids",
    "recording_mbid",
    "release_mbid",
)


class ListenBrainzClient:
    """Small paced client for the public ListenBrainz endpoints."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.last_request_at = 0.0

    def get_json(self, url, params=None):
        """GET JSON, respecting the one-request-per-second limit and retries."""
        for attempt in range(MAX_RETRIES):
            # Rate-limit all requests through this client, including retries.
            wait = MIN_SECONDS_BETWEEN_REQUESTS - (time.monotonic() - self.last_request_at)
            if wait > 0:
                time.sleep(wait)

            response = self.session.get(url, params=params, timeout=30)
            self.last_request_at = time.monotonic()

            if response.status_code == 429 or response.status_code >= 500:
                if attempt == MAX_RETRIES - 1:
                    response.raise_for_status()

                # Prefer the API's relative reset header, then Retry-After,
                # with exponential backoff as a fallback.
                delay = response.headers.get("X-RateLimit-Reset-In")
                delay = delay or response.headers.get("Retry-After")
                try:
                    delay_seconds = max(float(delay), 1.0)
                except (TypeError, ValueError):
                    delay_seconds = min(2**attempt, 30)
                time.sleep(delay_seconds)
                continue

            response.raise_for_status()
            return response.json()

        raise RuntimeError(f"Could not retrieve API response from {url}")


def find_documented_user(client, username):
    """Find the named project user through ListenBrainz user search."""
    result = client.get_json(
        f"{API_ROOT}/search/users/",
        params={"search_term": username},
    )
    payload = result.get("payload", result)
    users = payload.get("users", []) if isinstance(payload, dict) else []

    # Search responses may include approximate matches, so require the exact
    # username from the documented sample (case-insensitive comparison).
    for user in users:
        returned_name = user.get("user_name") or user.get("username")
        if returned_name and returned_name.casefold() == username.casefold():
            return returned_name
    raise RuntimeError(
        f"ListenBrainz user search did not return the documented account {username!r}."
    )


def get_listen_count(client, username):
    """Return the public listen-count endpoint's total for one user."""
    result = client.get_json(
        f"{API_ROOT}/user/{quote(username, safe='')}/listen-count"
    )
    payload = result.get("payload", result)
    return int(payload["count"])


def get_recent_listens(client, username):
    """Fetch up to 500 recent listens by paging backwards with max_ts."""
    all_listens = []
    max_ts = None

    while len(all_listens) < MAX_LISTENS_PER_USER:
        params = {"count": PAGE_SIZE}
        if max_ts is not None:
            params["max_ts"] = max_ts

        result = client.get_json(
            f"{API_ROOT}/user/{quote(username, safe='')}/listens",
            params=params,
        )
        payload = result.get("payload", {})
        page = payload.get("listens", [])
        if not page:
            break

        # Keep the API's listen objects intact in memory. Only the documented
        # raw fields are selected later for the project's CSV layout.
        all_listens.extend(page[: MAX_LISTENS_PER_USER - len(all_listens)])
        oldest_timestamp = min(int(listen["listened_at"]) for listen in page)

        # max_ts is exclusive. Moving to the oldest timestamp walks backward
        # without re-requesting the last event from the preceding page.
        if max_ts is not None and oldest_timestamp >= max_ts:
            raise RuntimeError(
                f"Pagination for {username!r} did not move to older listens."
            )
        max_ts = oldest_timestamp

        if len(page) < PAGE_SIZE:
            break

    return all_listens


def raw_csv_row(username, listen):
    """Project an API listen into the documented CSV columns without cleaning."""
    metadata = listen.get("track_metadata") or {}
    mapping = metadata.get("mbid_mapping") or {}

    # Preserve the list-valued artist MBIDs using JSON text in the CSV cell.
    # Missing values remain blank; no identifiers or names are inferred.
    artist_mbids = mapping.get("artist_mbids")
    if artist_mbids is not None:
        artist_mbids = json.dumps(artist_mbids, ensure_ascii=False)

    return {
        "username": username,
        "listened_at": listen.get("listened_at"),
        "track_name": metadata.get("track_name"),
        "artist_name": metadata.get("artist_name"),
        "release_name": metadata.get("release_name"),
        "recording_msid": listen.get("recording_msid"),
        "artist_mbids": artist_mbids,
        "recording_mbid": mapping.get("recording_mbid"),
        "release_mbid": mapping.get("release_mbid"),
    }


def main():
    # Do not overwrite a prior raw extract without the user explicitly moving
    # or removing it first.
    if OUTPUT_PATH.exists():
        raise FileExistsError(
            f"{OUTPUT_PATH} already exists; move it aside before downloading a new sample."
        )

    client = ListenBrainzClient()
    rows = []

    # Search each of the five named sample users, verify the documented
    # eligibility threshold, then retrieve at most 500 recent listens.
    for search_name in SAMPLE_USERNAMES:
        username = find_documented_user(client, search_name)
        listen_count = get_listen_count(client, username)
        if listen_count < MINIMUM_LISTENS:
            raise RuntimeError(
                f"{username!r} has {listen_count} listens; the sample requires at least "
                f"{MINIMUM_LISTENS}."
            )

        listens = get_recent_listens(client, username)
        print(f"Retrieved {len(listens)} listens for {username} (total: {listen_count}).")
        rows.extend(raw_csv_row(username, listen) for listen in listens)

    # Write only after every API retrieval succeeds, so a network failure does
    # not leave a partial CSV that looks like a complete sample.
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} raw listen rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
