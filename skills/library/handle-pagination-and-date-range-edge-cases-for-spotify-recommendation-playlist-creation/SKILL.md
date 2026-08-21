---
name: Handle Pagination and Date Range Edge Cases for Spotify Recommendation Playlist Creation
description: Covers edge cases when building Spotify recommendation playlists: paginating through all recommendations, computing 'this year' vs 'this or last year' thresholds from the current date, handling partial data, and avoiding duplicates.
---

## When to Use
Use when you need to robustly handle pagination, date thresholds, or incomplete/duplicate data while creating a Spotify playlist from recommendations.

## Preconditions
- Same as the primary skill: access to Spotify credentials and the ability to call Spotify APIs.
- The current date/time is needed to compute year boundaries.

## Procedure
1. Pagination: loop `page_index` from 0 upward, call `apis.spotify.show_recommendations(access_token=..., page_index=...)`, accumulate the items, and stop when an empty list is returned.
2. Date threshold computation:
   - Get today's date via `apis.phone.get_current_date_and_time()`.
   - Compute the start of the current year (e.g., Jan 1, 00:00).
   - For "this or last year", subtract one year from the start of the current year to get the start of the previous year.
3. Song filtering: after fetching song details with `apis.spotify.show_song(song_id=...)`, apply a combined condition: `genre == expected_genre and release_date >= threshold_date`.
4. If a song detail fetch fails for a particular ID, log the error and continue with the remaining songs.
5. De-duplicate songs before adding them to the playlist (e.g., use a set of song IDs).
6. If a song is already in the playlist, skip it to avoid duplicate entries.

## Relevant APIs / Tools
- `apis.phone.get_current_date_and_time`
- `apis.spotify.show_recommendations`
- `apis.spotify.show_song`
- `apis.spotify.add_song_to_playlist`

## Failure Handling
- If no recommendations exist, finish with an empty playlist.
- If date parsing fails, use the raw string comparison if the date format is ISO-like.
- If duplicate song IDs appear across pages, de-duplicate before adding.
- If a song lacks a genre or release date, skip it in filtering.

## Verification
- Ensure all pages of recommendations were fetched (no page left unread).
- Ensure the threshold date is correctly computed for the required year range.
- Ensure the playlist contains the expected unique songs and no duplicates.
