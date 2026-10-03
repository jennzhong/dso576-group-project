# ListenBrainz Record-Level Cleaning Checks

These checks compare `listenbrainz_sample.csv` with `cleaned_listenbrainz.csv` and, for the boundary check, `user_observation_summary.csv`. The raw and cleaned datasets were read only; neither was modified.

## Check 1 — Repeated recording

**Why selected:** The `recording_msid` `711271db-ea46-4f97-8da0-457e5f4d4713` occurs 116 times in the raw file. It is the most repeated recording identifier and tests that repeated plays are retained as separate events.

**Original raw records (two examples from the 116 events):**

```json
{
  "username": "H-music",
  "listened_at": "1563209770",
  "track_name": "Road ii Eternity",
  "artist_name": "Roseboy666",
  "release_name": "",
  "recording_msid": "711271db-ea46-4f97-8da0-457e5f4d4713",
  "artist_mbids": "",
  "recording_mbid": "",
  "release_mbid": ""
}
```

```json
{
  "username": "H-music",
  "listened_at": "1568989968",
  "track_name": "Road ii Eternity",
  "artist_name": "Roseboy666",
  "release_name": "",
  "recording_msid": "711271db-ea46-4f97-8da0-457e5f4d4713",
  "artist_mbids": "",
  "recording_mbid": "",
  "release_mbid": ""
}
```

**Expected before checking:** All 116 timestamp-distinct listen events remain. Repeating a recording ID alone should not remove a listen.

**Actual cleaned result:** The cleaned CSV contains 116 rows with this MSID and 116 distinct `listened_at` values. Both raw records above are present with their original raw values. Their derived `listened_at_utc` values are `2019-07-15 16:56:10+00:00` and `2019-09-20 14:32:48+00:00`, respectively.

**Matched expected result:** Yes.

**Demonstrates:** Repeated recording identifiers are retained as separate listen events; the derived timestamp is added without replacing the raw epoch text.

## Check 2 — Multi-artist MBIDs

**Why selected:** This listen has two artist MBIDs in one source field and tests safe parsing without expanding the primary event table.

**Original raw record:**

```json
{
  "username": "iliekcomputers",
  "listened_at": "1734336277",
  "track_name": "Take Care",
  "artist_name": "Drake, Rihanna",
  "release_name": "Take Care (Deluxe)",
  "recording_msid": "a9dccce2-eb7b-4e87-ba43-0cf9219997b7",
  "artist_mbids": "[\"9fff2f8a-21e6-47de-a2b8-7f449929d43f\", \"73e5e69d-3554-40d8-8516-00cb38737a1c\"]",
  "recording_mbid": "a23ccdb8-765f-4b7d-b47a-63191b2f856f",
  "release_mbid": "02f7e348-b1ae-4c4e-a057-b97f1f56e53c"
}
```

**Expected before checking:** The raw `artist_mbids` text remains exactly as submitted. `artist_mbids_parsed` represents a two-element list, while the primary cleaned dataset retains one row for the listen.

**Actual cleaned result:** One cleaned row matches the nine raw fields above. Its `artist_mbids` value is unchanged, and its derived `artist_mbids_parsed` value is:

```json
["9fff2f8a-21e6-47de-a2b8-7f449929d43f", "73e5e69d-3554-40d8-8516-00cb38737a1c"]
```

The row's derived `listened_at_utc` is `2024-12-16 08:04:37+00:00`.

**Matched expected result:** Yes.

**Demonstrates:** The list can be parsed into a usable derived representation without changing the raw field or exploding the event into multiple rows.

## Check 3 — Artist-name case variation

**Why selected:** These two records share the same recording MSID, track, artist MBID, and recording MBID, while the submitted artist-name capitalization differs. They test that text is preserved and not silently standardized or merged.

**Original raw records:**

```json
{
  "username": "H-music",
  "listened_at": "1572995054",
  "track_name": "Monitor",
  "artist_name": "Arthrn",
  "release_name": "",
  "recording_msid": "0b197626-8c02-40cc-a3c0-01acad783270",
  "artist_mbids": "[\"25d54fa4-0afa-4e47-a1ce-e2cfe5948fda\"]",
  "recording_mbid": "29eb0ba1-47b0-4194-bd24-d4293a05d7e9",
  "release_mbid": "0d22d470-ece4-40b4-8087-b3b479300d2f"
}
```

```json
{
  "username": "H-music",
  "listened_at": "1572715102",
  "track_name": "Monitor",
  "artist_name": "arthrn",
  "release_name": "",
  "recording_msid": "0b197626-8c02-40cc-a3c0-01acad783270",
  "artist_mbids": "[\"25d54fa4-0afa-4e47-a1ce-e2cfe5948fda\"]",
  "recording_mbid": "29eb0ba1-47b0-4194-bd24-d4293a05d7e9",
  "release_mbid": "0d22d470-ece4-40b4-8087-b3b479300d2f"
}
```

**Expected before checking:** Both timestamp-distinct events remain, with `artist_name` values exactly `Arthrn` and `arthrn`. Any identity relationship is left for review rather than resolved by text normalization.

**Actual cleaned result:** Both rows are present. The first retains `Arthrn` with `listened_at_utc` `2019-11-05 23:04:14+00:00`; the second retains `arthrn` with `listened_at_utc` `2019-11-02 17:18:22+00:00`. The shared recording ID appears on three events in both source and cleaned data.

**Matched expected result:** Yes.

**Demonstrates:** Artist-name case is preserved, and distinct timestamped events are not collapsed because their identifier or display name repeats.

## Check 4 — Missing artist MBID

**Why selected:** This listen has a blank `artist_mbids` value but populated core event fields, testing that unresolved identity does not cause row loss or identifier inference.

**Original raw record:**

```json
{
  "username": "iliekcomputers",
  "listened_at": "1734320229",
  "track_name": "Apna Bana Le",
  "artist_name": "Sachin-Jigar, Arijit Singh, Amitabh Bhattacharya",
  "release_name": "Bhediya (Original Motion Picture Soundtrack)",
  "recording_msid": "db3299d8-f4a0-46a7-8847-0e800c2e037a",
  "artist_mbids": "",
  "recording_mbid": "",
  "release_mbid": ""
}
```

**Expected before checking:** The event remains in the cleaned table. `artist_mbids` and the derived parsed-list field remain blank; no MBID is inferred from the artist name.

**Actual cleaned result:** One cleaned row matches all nine raw fields above. `artist_mbids` and `artist_mbids_parsed` are blank. `listened_at_utc` is `2024-12-16 03:37:09+00:00`.

**Matched expected result:** Yes.

**Demonstrates:** Missing artist identifiers are retained as unresolved; core event data remains available without inventing an identity.

## Check 5 — Observation-window boundary

**Why selected:** H-music reached the 500-listen cap. Its final listen checks that the sample boundary event survives and that the user summary reflects the observed window and cap status.

**Original raw record (H-music's last listen):**

```json
{
  "username": "H-music",
  "listened_at": "1573841027",
  "track_name": "You Should Try",
  "artist_name": "Pills",
  "release_name": "",
  "recording_msid": "1ade7272-8968-484c-a140-e513d484c490",
  "artist_mbids": "",
  "recording_mbid": "",
  "release_mbid": ""
}
```

**Expected before checking:** This final event remains in the cleaned data. The user summary reports 500 rows, first listen `2019-07-15 16:56:10+00:00`, last listen matching the event timestamp, observed duration `123 days 01:07:37`, and `sampling_cap_reached=True`.

**Actual cleaned result:** The matching event is present with raw `listened_at` `1573841027` and derived `listened_at_utc` `2019-11-15 18:03:47+00:00`. The summary row for H-music reports `row_count=500`, `source_row_count=500`, first listen `2019-07-15 16:56:10+00:00`, last listen `2019-11-15 18:03:47+00:00`, duration `123 days 01:07:37`, and `sampling_cap_reached=True`.

**Matched expected result:** Yes.

**Demonstrates:** The boundary event is retained, raw epoch text is preserved, UTC datetime is correctly derived, and cap/window diagnostics use the source history.

## Conclusion

All five record checks passed. The selected repeated listens, multi-artist MBIDs, name-case variation, missing artist MBID, and capped-window boundary were preserved and represented as expected in the cleaned data and user summary.
