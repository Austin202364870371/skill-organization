---
name: Robust Spotify library release-date aggregation and failure handling
description: Handles edge cases in the Spotify library aggregation workflow: missing release dates, duplicate song ids, empty libraries, transient API failures, and album-vs-song release date mismatches.
---

## When to Use
Use as a complement to the primary workflow when the Spotify library aggregation needs to be robust to data quality issues, duplicates, empty results, or API errors.

## Preconditions
- An access token is available or can be obtained via `apis.spotify.login`.

## Procedure
- Prefer song-level release dates from `apis.spotify.show_song` whenever possible. Use album release dates only as a fallback, because album-level dates may differ for individual tracks.
- Always paginate until an empty page is returned to avoid missing entries; increment `page_index` each time and guard against infinite loops.
- Deduplicate song ids by keeping the most reliable release date (song-level detail over album-level date), not necessarily the first encountered.
- If a song detail call fails, catch the error, continue processing other songs, and retry the failed id later.
- If the collected dictionary is empty, report failure via `apis.supervisor.complete_task(status="failure")` or a message indicating an empty library.
- For authentication issues, retry `apis.spotify.login` with corrected credentials.

## Relevant APIs / Tools
- apis.spotify.login
- apis.spotify.show_song
- apis.spotify.show_album_library
- apis.spotify.show_playlist_library
- apis.supervisor.complete_task

## Failure Handling
- Wrap network/API calls in a retry loop with a small delay.
- If an album lacks `release_date`, call `apis.spotify.show_song` for each song_id in that album.
- If no song id can be resolved, complete the task with `status="failure"`.

## Verification
- Compare the size of `release_by_song_id` against the union of all ids from song, album, and playlist libraries to confirm full coverage.
- Re-run the min/max selection and check it matches the previously selected id.
