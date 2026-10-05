import time
import requests
import pandas as pd
from urllib.parse import quote

USERS = ["iliekcomputers", "H-music", "s_john_s", "John V", "music_af"]
MAX_PER_USER = 500
URL = "https://api.listenbrainz.org/1/user/{}/listens"

def fetch(user, params):
    for attempt in range(6):
        try:
            r = requests.get(URL.format(quote(user)), params=params, timeout=90)
            if r.status_code == 429:
                time.sleep(10)
                continue
            return r
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            print("  timeout, retrying", attempt + 1)
            time.sleep(5)
    raise RuntimeError("gave up on " + user)

rows = []
for user in USERS:
    max_ts, got = None, 0
    while got < MAX_PER_USER:
        params = {"count": min(100, MAX_PER_USER - got)}
        if max_ts:
            params["max_ts"] = max_ts
        r = fetch(user, params)
        if r.status_code == 204:
            break
        r.raise_for_status()
        listens = r.json()["payload"]["listens"]
        if not listens:
            break
        for l in listens:
            tm = l.get("track_metadata", {})
            ai = tm.get("additional_info") or {}
            mm = tm.get("mbid_mapping") or {}
            rows.append({
                "username": user,
                "listened_at": pd.to_datetime(l["listened_at"], unit="s", utc=True),
                "track_name": tm.get("track_name"),
                "artist_name": tm.get("artist_name"),
                "release_name": tm.get("release_name"),
                "recording_msid": ai.get("recording_msid") or l.get("recording_msid"),
                "artist_mbids": mm.get("artist_mbids"),
                "recording_mbid": mm.get("recording_mbid"),
                "release_mbid": mm.get("release_mbid"),
            })
        got += len(listens)
        max_ts = listens[-1]["listened_at"]
        time.sleep(1)
    print(user, got, flush=True)
    pd.DataFrame(rows).to_csv("listenbrainz_sample.csv", index=False)

print("saved", len(rows), "rows")