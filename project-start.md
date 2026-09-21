# Project Starting Point

## Selected project area

Emerging Artist Discovery Through Listening Behavior

## Why our team is interested in it

Our team is interested in how music-streaming platforms can identify promising artists before they become widely popular. We want to explore whether listening behavior, especially growth in unique listeners and repeat engagement, can provide useful signals for identifying artists who may deserve additional exposure. This topic also connects data analytics to practical business decisions involving limited promotional space on streaming platforms.

## Candidate Vision A

An Editorial Programming Manager at Spotify must decide which emerging artists should receive additional exposure through playlists, recommendations, or other promotional features.

## Candidate Vision B

A Personalization Product Manager at Spotify must decide which listener segments should receive recommendations for selected emerging artists in order to encourage continued engagement.

## Core data source we confirmed we can access

Our primary proposed data source is ListenBrainz, which provides public listening-history data. The listening data can help us examine user listening activity, artist exposure, repeat listening, and changes in engagement over time.

We also plan to use MusicBrainz as a supporting metadata source. MusicBrainz provides artist and music metadata that can help us connect listening behavior with information about artists, recordings, and releases.

We confirmed that these public data sources are available for us to begin exploring, and our next step is to test a small sample before working with larger amounts of data.

## Three questions we still need to resolve

1. How should we define an "emerging artist" using measurable criteria from the available listening and artist metadata?

2. Does the available ListenBrainz data provide enough users and time coverage to measure listener growth and repeat engagement reliably?

3. How reliably can ListenBrainz listening records be connected to MusicBrainz artist and release metadata?


## Phase 1 Final Vision
### Our Project Vision and Usage Example
A music-streaming editorial team must decide which emerging artists should receive additional exposure and which listener segments are most likely to continue engaging with those artists after discovery.

The editorial team uses the dashboard to discover new talent. They look for artists with small initial audiences. These musicians must show steady growth in unique listeners. Next, the team examines listener behavior. They check if fans return after discovering an artist. They also observe whether people explore multiple tracks. Sometimes, the team monitors listening habits across several days. Ultimately, the dashboard simplifies this entire process. It helps the team build a shortlist of promising emerging artists. The tool also pinpoints the most loyal listener segments.

### Work Definition
Working definition of an emerging artist: An artist with a relatively small initial audience who demonstrates sustained growth in unique listeners over the observation period.

### Working definition of continued engagement
A listener demonstrates continued engagement when they return to an artist after initial discovery, such as listening again within a defined time window, listening on multiple days, or exploring multiple tracks by the same artist.

# Member 2: Andy Chen — ListenBrainz Data Exploration Lead

## Source

ListenBrainz public API (https://api.listenbrainz.org), endpoint
`GET /1/user/{username}/listens`. No authentication is required; ListenBrainz
publishes listen data under CC0.

We did not use the bulk data dumps at https://listenbrainz.org/data/, which
contain every listen ever submitted to ListenBrainz and which ListenBrainz's
own documentation describes as a large download that is hard to manage.
Sampling through the API keeps the extract small: it returns a maximum of 100
listens per request and can be paged backwards in time with the `max_ts`
parameter. Users were found through the ListenBrainz user-search endpoint
(`GET /1/search/users/`) and filtered to those with at least 50 listens.
Retrieved 21 September 2026.

## What One Row Represents

One listen event: a single user playing a single track at a single point in
time. Rows are not unique per user or per track — a user who plays the same
track three times produces three rows, distinguished by `listened_at`.

## Sample Size, Listeners, and Artists

| Measure | Value |
|---|---|
| Listens (rows) | 1,940 |
| Columns | 9 |
| Unique listeners | 5 |
| Unique artists (by `artist_name`) | 756 |
| Unique artists (by resolved MBID) | 437 |

The two artist counts differ because 39% of listens carry no MusicBrainz
identifier, and because `artist_name` is free text that varies between
submissions. The sample contains "Takanashi Yasuharu / -yaiba-" and "Yasuharu
Takanashi / -yaiba-" as separate names for the same artist, so the 756 figure
is an upper bound rather than a true artist count.

Listens per user:

| User | Listens |
|---|---|
| iliekcomputers | 500 |
| H-music | 500 |
| s_john_s | 500 |
| John V | 226 |
| music_af | 214 |

Three users hit the 500-listen ceiling we requested, so their histories extend
further back than this extract captures.

## Date Range

Overall timestamps run from **7 March 2019 to 21 September 2026**. This is not
continuous coverage. Each user contributes a separate window of recent
activity, and those windows fall in different years:

| User | First listen | Last listen | Days covered | Distinct months |
|---|---|---|---|---|
| music_af | 2025-09-17 | 2026-03-25 | 189 | 7 |
| H-music | 2019-07-15 | 2019-11-15 | 123 | 5 |
| iliekcomputers | 2024-11-16 | 2024-12-16 | 30 | 2 |
| s_john_s | 2019-03-07 | 2019-03-20 | 13 | 1 |
| John V | 2026-09-17 | 2026-09-21 | 4 | 1 |

There is no time period during which all five users are observed together.

## Relevant Columns

| Column (source) | What it contains | How it supports the analysis |
|---|---|---|
| `username` (listens) | ListenBrainz user who submitted the listen | Identifies the listener; basis for counting distinct listeners |
| `listened_at` (listens) | Unix timestamp of the play, converted to datetime | Orders listens in time; supports time-based grouping and gaps between listens |
| `track_name` (listens) | Track title as submitted | Counting distinct tracks per listener and artist |
| `artist_name` (listens) | Artist name as submitted (free text) | Display label; grouping where no identifier exists |
| `release_name` (listens) | Album or release title | Release-level context |
| `recording_msid` (listens) | ListenBrainz's own identifier for the submitted recording | Present on every row; identifies the listen's recording within ListenBrainz |
| `artist_mbids` (listens, within `mbid_mapping`) | MusicBrainz artist identifiers, as a list | Identifies artists more consistently than free-text names |
| `recording_mbid` (listens, within `mbid_mapping`) | MusicBrainz recording identifier | Identifies specific recordings |
| `release_mbid` (listens, within `mbid_mapping`) | MusicBrainz release identifier | Identifies specific releases |

The last three come from the `mbid_mapping` object inside each listen record,
not from `additional_info`. ListenBrainz documentation notes that
`mbid_mapping` values are resolved by ListenBrainz itself, while
`additional_info` values are submitted by the user's listening client and are
not validated. `mbid_mapping` is absent entirely when ListenBrainz cannot
resolve a listen, which is why these three columns share a similar missing rate.

## Missing Values

| Column | Missing | % of sample |
|---|---|---|
| `username` | 0 | 0% |
| `listened_at` | 0 | 0% |
| `track_name` | 0 | 0% |
| `artist_name` | 0 | 0% |
| `recording_msid` | 0 | 0% |
| `recording_mbid` | 728 | 38% |
| `release_name` | 754 | 39% |
| `artist_mbids` | 759 | 39% |
| `release_mbid` | 759 | 39% |

The four core fields are complete on every row. The identifier fields are not,
and the gap is concentrated by user rather than spread evenly:

| User | Listens with a resolved artist MBID |
|---|---|
| music_af | 213/214 (100%) |
| iliekcomputers | 388/500 (78%) |
| s_john_s | 353/500 (71%) |
| H-music | 191/500 (38%) |
| John V | 36/226 (16%) |

Any analysis restricted to rows with identifiers will therefore contain a very
different mix of users than the full extract.

## Reproducing This

`pull_listenbrainz_sample.py` retrieves the sample and writes
`listenbrainz_sample.csv`. `explore_sample.py` produces every figure reported
above. The CSV is excluded from version control via `.gitignore`.


# Member 3 Shivanee Kooner – MusicBrainz & Data Column Lead

## MusicBrainz Artist Metadata

MusicBrainz will serve as the supporting metadata source for the project. While ListenBrainz provides the behavioral information needed to study listening activity over time, MusicBrainz provides standardized information that identifies and describes the artists, recordings, and releases connected to those listens.

The most relevant MusicBrainz artist fields for this project are:

| Field | What it contains | Why it matters for our project |
|---|---|---|
| `artist_mbid` / MBID | Unique MusicBrainz identifier for an artist | Primary key for reliably linking an artist across ListenBrainz and MusicBrainz |
| `name` | Official artist name | Used for dashboard display and artist identification |
| `sort_name` | Standardized name used for sorting | Helps keep artist names organized consistently |
| `type` | Person, group, orchestra, choir, character, or other | Can be used to describe or filter artists |
| `area` / `country` | Geographic area associated with the artist | Adds geographic context and can support dashboard filters |
| `begin_date` | Birth date for a person or formation date for a group | Adds background information about the artist |
| `end_date` | Death date for a person or dissolution date for a group | Indicates whether an artist or group has ended |
| `gender` | Gender field for applicable artist types | Additional descriptive metadata |
| `disambiguation` | Short comment used to distinguish artists with similar names | Helps prevent incorrect artist matches |

## How MusicBrainz Connects to ListenBrainz

ListenBrainz listening records can contain a server-resolved `mbid_mapping` field. This mapping may include `artist_mbids`, `recording_mbid`, `release_mbid`, and `release_group_mbid`. These identifiers correspond directly to entities in MusicBrainz.

For this project, the primary connection should be:

**ListenBrainz listen → `artist_mbids` → MusicBrainz artist MBID → artist metadata**

This is stronger than matching on artist name because the MBID is a unique identifier. If a recording contains multiple credited artists, the `artist_mbids` array can be expanded so each artist can be connected to its own MusicBrainz record.

We should prefer the server-resolved `mbid_mapping` values when available. ListenBrainz documentation explains that MBIDs in `additional_info` may be submitted by a user's listening client and are not necessarily validated, while `mbid_mapping` contains the identifiers resolved by ListenBrainz against MusicBrainz. If ListenBrainz cannot resolve a listen, `mbid_mapping` is absent.

## Proof of Connection Using Official Documentation

ListenBrainz documentation provides an example listen for Rick Astley that contains the artist MBID `db92a151-1ac2-438b-bc43-b82e149ddd50`. MusicBrainz's API documentation uses that same MBID for Rick Astley and returns artist metadata such as the artist name, sort name, type, gender, and disambiguation comment. This demonstrates that the MBID can function as a direct join key between the two sources.

The same logic also applies at the recording and release levels. A `recording_mbid` can identify the exact recording in MusicBrainz, while `release_mbid` and `release_group_mbid` can connect a listen to release-level metadata.

## Relevance to the Project Vision

Our project defines an emerging artist as an artist with a relatively small initial audience who demonstrates sustained growth in unique listeners over the observation period. The growth and engagement measures themselves should therefore come from ListenBrainz listening behavior. MusicBrainz does not replace those behavioral measures; instead, it enriches them with consistent artist identity and descriptive metadata.

This combination supports the dashboard by allowing the editorial team to measure listener growth and repeat engagement from ListenBrainz while using MusicBrainz to identify the correct artist and provide useful context such as artist type, geographic area, and active dates.

## One-Sentence Addition for the Vision / Usage Example

The dashboard links ListenBrainz listening behavior to MusicBrainz artist metadata through MusicBrainz identifiers (MBIDs), allowing the editorial team to evaluate listener growth and repeat engagement while consistently identifying artists and enriching them with descriptive information.

## Recommended Join Logic

```python
# Example structure once the ListenBrainz sample is available

# Expand artist_mbids because a recording can have more than one credited artist
lb_artists = listenbrainz.explode("artist_mbids")

# Rename for a clear join key
lb_artists = lb_artists.rename(columns={"artist_mbids": "artist_mbid"})

# Join ListenBrainz behavioral records to MusicBrainz artist metadata
combined = lb_artists.merge(
    musicbrainz,
    on="artist_mbid",
    how="left"
)
```

## Source Notes

- ListenBrainz JSON Documentation: explains `mbid_mapping`, artist/recording/release MBIDs, and the difference between server-resolved mappings and user-submitted `additional_info`.
- MusicBrainz Artist Documentation: defines artist properties including name, sort name, type, area, begin/end dates, gender, MBID, and disambiguation.
- MusicBrainz API Documentation and Examples: shows how an entity can be looked up by MBID and provides a documented Rick Astley example using the same artist MBID shown in ListenBrainz documentation.
