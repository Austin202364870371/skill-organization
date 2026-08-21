---
name: Spotify Recommendation Aggregation Edge-Case Handling
description: Handles pagination boundaries, empty/missing data, tie-breaking, and fallback behavior when aggregating Spotify recommendations for artist-frequency questions.
---

## When to Use
Use as a companion to the primary Spotify artist finder when the environment requires manual pagination, robust missing-data handling, or a deterministic choice among equally recommended artists.

## Preconditions
- Spotify access token is either passed in or obtained through login/helper.
- The recommendations endpoint may return multiple pages.
- Songs may have zero, one, or multiple artists.

## Procedure
1. Always iterate recommendation pages explicitly, stopping when an empty list is returned or when the total count is reached.
2. Retrieve each song with `apis.spotify.show_song(song_id=...)` and ignore songs that fail or return no artists.
3. Aggregate artist IDs in a dictionary or `Counter`, preserving insertion order for stable tie-breaking.
4. For "most", select the artist with the highest count; for "least", select the one with the lowest count. Break ties by first insertion order.
5. If the aggregated collection is empty, return a failure status via `apis.supervisor.complete_task(answer=None, status="failure")`.
6. If an artist ID cannot be resolved by `apis.spotify.show_artist`, skip it and choose the next candidate.

## Relevant APIs / Tools
- apis.spotify.show_recommendations
- apis.spotify.show_song
- apis.spotify.show_artist
- apis.supervisor.complete_task

## Failure Handling
- Empty pages: stop pagination and continue with collected data.
- Missing song details: skip the song and log/ignore it.
- Artist resolution failure: fall back to the next most/least frequent artist.
- All data missing: mark the task failed rather than guessing an artist.
- Tie-breaking: use the artist that appears first in the aggregated order to keep results deterministic.

## Verification
- Ensure all non-empty recommendation pages were traversed.
- Ensure every successfully fetched song contributed its artists to the counts.
- Ensure the returned artist name corresponds to the selected artist ID, or that failure is reported when no valid artist exists.
