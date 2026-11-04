# Discovery Atlas: 4–5 minute demo recording script

Record the real app while making these selections. Read at a conversational
pace, pausing to let each result update. Begin with defaults: all five
listeners, full UTC date range, no artist exclusions, and default shortlist
criteria. Use the verified public app once deployed. This is a recording
script, not a completed video; add the final viewable video link to README.

## 0:00–0:35 — The user and decision

**Screen:** Shortlist, default filters and headline cards.

“I am a playlist editor deciding which artists to investigate for a discovery
playlist. High play totals alone can favor already established names. Discovery
Atlas instead helps me inspect repeat engagement: whether sampled listeners
return to an artist, how many days they listen, and how that engagement develops.
It gives me a shortlist to investigate, not a prediction of commercial success.”

## 0:35–1:20 — Overview and units

**Screen:** Point to the seven cards, then scroll to the ranked table.

“This frozen sample contains 1,940 logged listening events from five public
ListenBrainz listeners. After the team's double-scrobble rule, there are 1,882
countable listens. Artist analysis identifies 669 artists and 677 distinct
listener–artist combinations.

The pair return rate is about 25 percent. It means a quarter of these
listener–artist pairs appear on at least two different UTC days within the
selected period. It does not mean a quarter of all music listeners returned.
The artist-return card uses artists, rather than pairs, as its denominator.
Only 48 artists have enough evidence for a return-momentum estimate.”

## 1:20–2:00 — Make a useful shortlist

**Action:** Open Shortlist filters and set Min avg active days to **2**.

“I want evidence that goes beyond a single day, so I raise average active days
to two. The shortlist falls from 669 to 168 artists. These units are listening
days per listener for an artist. The headline cards stay unchanged because
they describe the date and listener selection; this control narrows only my
candidate list. I can also exclude established names and inspect artists with
or without MusicBrainz identities. The ranking favors return rate and listening
depth rather than ranking artists by the number of sampled listeners.”

## 2:00–3:00 — Investigate an artist before deciding

**Action:** Select rank-one **Arthrn** in the table, then open Artist detail.

“Arthrn has 182 countable listens, one sampled listener, 19 active days, and
52 distinct tracks. Its 100 percent return rate refers to that one listener.
The breadth across days and tracks gives me a reason to investigate this artist,
but the audience here is very small.

Return momentum is a unitless difference from the listener's own late-window
activity baseline. A value around positive 0.10 is roughly a ten-percentage-point
stronger late-window share. It is not ten percent market growth.

The monthly chart shows whether plays are concentrated or sustained. Its
caption says MBID-matched, all logged listens, because this analysis has
different coverage from the countable M4 metrics. The 30-day return measure
can include a later play on the same day, while the main return rate requires
distinct UTC days. The listener and track tables help me check who and what
are driving the result before deciding whether to shortlist the artist.”

## 3:00–3:40 — Change the sample and understand coverage

**Action:** Set the top Listeners control to **H-music** only. Open Listeners.

“Now I change the listener selection, which affects every view. The cards
recompute to one listener and 443 countable listens. The listener table shows
500 logged listens because it includes all events before the double-scrobble
exclusion. This distinction is labeled.

H-music is marked capped: the extract reached 500 listens, so the last observed
play does not prove engagement ended. Each listener has an individual daily
activity chart with their own dates. The monthly coverage chart describes
which sampled listeners were active, not growth in an artist's audience.”

## 3:40–4:15 — Demonstrate a difficult case

**Action:** Clear the top Listeners selection. Open each view if useful.

“With no listeners selected, the app says there are no listens in the period
and explains how to recover: select a listener and broaden the UTC dates.
There are no stale artist results or unexplained blank charts. An overly strict
shortlist similarly explains how to relax its criteria. Missing momentum is
shown as n/a rather than zero; artists without MBIDs remain available in the
main analysis.”

## 4:15–4:45 — Decision, limitation, and next step

**Action:** Restore all five listeners; return to Shortlist.

“My next step is to investigate artists with sustained listening depth, check
their music, and consider them for a playlist. The most important limitation is
the five-listener sample with different observation windows. It cannot support
claims about market popularity, and we do not have external popularity data to
prove that an artist is emerging. A future version should use a larger,
consistent observation panel while preserving these clear metric definitions.”

## Before sharing the recording

- Show both the controls and their updated results; wait for each rerun.
- Keep usernames and data discussion limited to the project's public sample.
- Test the video link without signing in, and add it beside the live-app link
  in README and in the team's Gradescope submission.
- Keep course showcase preference at **Decide later** until the team confirms
  whether every member agrees to optional public promotion.
