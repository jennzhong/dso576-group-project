# Cleaning Rules — ListenBrainz Listening Sample (Andy Chen)

Written after inspecting the raw file (`inspect_raw.py`, `inspect_followup.py`)
and **before** writing `clean_listens.py`. Any rule changed after this point is
recorded in the "Changes to rules" section at the bottom.

## Project question these rules serve

Which artists in our sample show *repeat engagement* — listeners who come back
to an artist on more than one day — and which listeners drive it? The main
metrics are, per artist: **countable listens**, **unique listeners**, and the
**return rate** (share of listener–artist pairs with listens on 2+ distinct
UTC days). Listener-growth over time cannot be measured from this sample
(see Limitations in the report), so the rules protect the repeat-engagement
counts above all.

## One row

One row = one listen event: one user submitting one track at one second.
Candidate key: `username` + `listened_at` (inspection: 0 repeats).
The cleaned table adds `listen_id = "<username>|<unix seconds>"`.

## Rules

| ID | Rule | Reason |
|---|---|---|
| R1 | Load `listenbrainz_sample.csv` with every column as text (`dtype=str`), only empty cells as missing. Check its SHA-256 equals `463000bf005a3c667cfeb708b44aa12f0d35342e34f467ede3caf924426b816d` and never write to it. | The raw file is the frozen version of the source; the API returns live data and cannot recreate it. Text loading stops pandas from changing IDs or names before we see them. |
| R2 | Convert `listened_at` to a timezone-aware UTC datetime (`listened_at_utc`) with format `%Y-%m-%d %H:%M:%S`. Count failures; a failure becomes missing and is excluded from time-based metrics. | Times are needed for distinct-day and gap calculations. The API check showed the CSV values equal the API's Unix times read as UTC. |
| R3 | Parse `artist_mbids` (a Python-list string) with `ast.literal_eval` into `artist_mbids_json` (JSON list) and `n_credited_artists`. Count failures. | The list string can't be grouped or exploded as-is. |
| R4 | Check every ID column against the lowercase UUID pattern; keep IDs as text exactly as given. | IDs like `000c52a6-...` must keep their leading zeros; any malformed ID would break joins to MusicBrainz. |
| R5 | Keep every original text column unchanged. Add `track_name_clean`, `artist_name_clean`, `release_name_clean` = trimmed + Unicode **NFC** only. Do **not** lowercase, do **not** use NFKC. | Display text should match what the user submitted. NFC only fixes how accented characters are encoded. NFKC would rewrite stylised names (`𝔇𝔞𝔶𝔗𝔬𝔫𝔄`) and `…`, which are meaningful. |
| R6 | Build a grouping key `artist_key` from `artist_name_clean`: casefold, strip a trailing `" - Topic"`, then apply the alias table below. Placeholder names (`Unknown`, `[unknown]`) become missing. | Case variants (`Arthrn`/`arthrn`, `PUFFY`/`Puffy`) and YouTube auto-channels (`Alan Silvestri - Topic`) split one artist into several. A placeholder is not an artist. |
| R7 | Artist identity: `artist_id` = first MusicBrainz artist MBID when present, else `name:<artist_key>`. Multi-artist credits are expanded only in a separate bridge table (`listen_artist_bridge.csv`, one row per listen × credited MBID). | MBIDs are the reliable identity: inspection found 16 artist MBIDs that appear under more than one name string. Exploding the main table would inflate listen counts. |
| R8 | Exact duplicate rows (all 9 columns): remove. Repeated `username + listened_at`: investigate. Repeated `username + recording_msid` (replays): **keep**. | Exact copies are pipeline errors; replays are the behaviour we measure. |
| R9 | **Suspected double-scrobble**: same user and same `recording_msid` submitted < 60 s after that user's previous submission of the same recording. Flag (`suspected_double_scrobble`), keep the row, and set `is_countable = False`. | Back-to-back plays of one track are spaced by the track's length, so a gap under 60 s means a sub-minute track, which is rare. Inspection shows a gap in the distribution: 57 repeats at ≤ 40 s, 1 at 40–60 s, 31 at 60–90 s. Flagging instead of deleting keeps the event table complete and the decision reversible. |
| R10 | Missing `release_name`, `artist_mbids`, `recording_mbid`, `release_mbid`: keep the row; do not fill or infer. Add `has_artist_mbid`. | Missing IDs mean ListenBrainz couldn't match the track, not that the listen didn't happen. Guessing IDs from names would create false matches. |
| R11 | Suspicious values: flag (not drop) timestamps before 2005 or after the retrieval moment (2026-09-21 23:59:59 UTC), placeholder track/artist names, and IDs that fail R4. | "Unusual" ≠ wrong; flags let the analysis decide. |
| R12 | Different tracks submitted seconds apart (skipping) are **kept** and not flagged. | They are different recordings; a partial play still counts as discovery/exposure. Noted as a limitation. |

### Alias table (R6 exception)

| Raw `artist_name` | Mapped `artist_key` | Evidence |
|---|---|---|
| `Takanashi Yasuharu / -yaiba-` | `yasuharu takanashi / -yaiba-` | Same composer + band, name order reversed (Japanese vs Western). Both appear only for user `s_john_s`, only on *Naruto Shippuuden* soundtracks, and neither has an MBID. `Yasuharu Takanashi` (without `-yaiba-`) is kept separate because the credit differs. |

## Metrics and denominators (decided before computing)

- **Countable listens** = rows with `is_countable = True`.
- **Artist-level metrics** use rows with non-missing `artist_key`; rows with a missing key are counted and reported, not silently dropped.
- **Return rate denominator** = listener–artist pairs with ≥ 1 countable listen.
- **MBID-based metrics** (bridge table) cover only listens with `has_artist_mbid`; the report states that coverage by user.

## Planned record checks

Expected results are written in `record_checks_expected.csv` before the
cleaning script exists. The script compares actual output to that file.

## Changes to rules

| Date | Rule | Change | Reason / effect |
|---|---|---|---|
| 2026-10-17 | R7b (Phase 2) | If an `artist_key` appears with exactly one artist MBID, its rows without an MBID take that MBID as `artist_id` (`artist_id_source = key_mbid`). Applied in `kpi_analysis.py` (`derive_columns`); the Module 6 `outputs/` files are unchanged. | R7 split one artist across an MBID id and a `name:` id when only some of its listens were matched — e.g. Arthrn (125 + 57 listens). 116 rows (113 countable) change; artists 679 → 669; pair return rate 25.0% → 25.0%. Keys with 2+ MBIDs (Junior Varsity, Kenny Rogers) are left alone. |
