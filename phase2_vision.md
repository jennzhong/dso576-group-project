# 1. Revised Project Vision & Use Cases

## Project Vision

Our Emerging Artist Discovery dashboard is designed to help music-streaming editorial teams identify promising emerging artists and understand which listener segments demonstrate continued engagement.

The dashboard uses ListenBrainz listening behavior and MusicBrainz artist metadata to evaluate audience growth, repeat listening, and listener engagement. It provides an evidence-based way for editorial teams to shortlist emerging artists for potential promotion.

## Target Users

Our primary users are music-streaming editorial teams responsible for discovering new talent and deciding which artists should receive additional exposure.

## Business Decision

The dashboard supports two key decisions:

- Which emerging artists show enough audience growth and continued engagement to be considered for promotion?
- Which behavioral listener segments demonstrate stronger continued engagement with those artists?

## Why the Dashboard Improves Current Practice

Instead of manually reviewing listening records and artist information separately, editorial teams can use one dashboard to compare audience growth and engagement metrics.

This makes it easier to identify promising artists, evaluate listener behavior, and create a shortlist based on consistent metrics rather than relying only on initial popularity.

## Core Use Cases

### Use Case 1: Discover Emerging Artists

**User selects/inputs:** The editorial team selects an available time period and filters artists by type or geographic area.

**Dashboard shows:** A ranked list of artists with unique listeners, audience growth, and repeat engagement metrics.

**User decides:** Which artists demonstrate promising growth and should be added to a shortlist for further evaluation.

### Use Case 2: Evaluate Audience Growth

**User selects/inputs:** The editorial team selects a specific artist from the ranking table.

**Dashboard shows:** The artist's unique listener growth over time and relevant artist details.

**User decides:** Whether the artist demonstrates sustained audience growth and deserves further consideration.

### Use Case 3: Analyze Continued Engagement

**User selects/inputs:** The editorial team selects an artist and examines listener engagement metrics.

**Dashboard shows:** Repeat listening behavior, listening activity across multiple days, and the number of distinct tracks played, including behavioral listener segments.

**User decides:** Which listener segments show stronger continued engagement and whether the artist should remain on the promotion shortlist.

## Working Definitions

**Emerging Artist:** An artist with a relatively small initial audience who demonstrates sustained growth in unique listeners during the observation period.

**Continued Engagement:** A listener demonstrates continued engagement when they return to an artist after their first observed listen, listen on multiple days, or explore multiple tracks by the same artist.

## Project Scope and Limitations

The first version focuses on observed listening behavior within the available ListenBrainz sample and uses MusicBrainz metadata for artist identification.

Because the sample contains limited and uneven listening histories, the dashboard is intended to support exploratory analysis rather than provide definitive predictions of artist success.

The final promotion decision remains with the editorial team.
