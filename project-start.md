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
