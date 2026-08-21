---
name: spotify_robust_pagination_and_removal_handling
description: Handles robust pagination, idempotent removal, missing release dates, and verification when bulk-deleting songs from Spotify library and playlists.
---

## When to Use
Use this skill whenever you need to fetch large collections from Spotify (library songs or playlists) and perform removals reliably, especially when the primary workflow encounters edge cases like already-deleted items, missing metadata, or page boundaries.

## Preconditions
- You have a valid Spotify `access_token`.
- You have identified the threshold year and comparison mode.
- You understand the user's instruction regarding songs with missing release dates.

## Procedure
1. Implement a generic pagination loop that stops when an empty page is returned. Increment `page_index` by 1 each time.
2. When iterating library songs or playlist songs, always fetch full song details with `apis.spotify.show_song` before relying on `release_date`.
3. If `release_date` is missing or `None`, skip the song unless the user explicitly asks to include unknown dates. Log a warning and continue.
4. Make removals idempotent: if a `remove_song_from_library` or `remove_song_from_playlist` call raises a 404, treat it as success (the song is already gone) and continue.
5. For playlists, if `show_playlist` returns a `songs` list, iterate over it. Be aware that the song object may expose the ID as `id` or `song_id`; check both.
6. To avoid repeated `show_song` calls for the same song (e.g., duplicates across playlists), cache song details by `song_id` in a dictionary.
7. After all removals, call `apis.supervisor.complete_task(answer=None, status="success")` only if no fatal error occurred. If a critical step fails, call `complete_task(status="failure")` with an explanation in `answer`.

## Relevant APIs / Tools
- `apis.spotify.show_song_library`
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_playlist`
- `apis.spotify.show_song`
- `apis.spotify.remove_song_from_library`
- `apis.spotify.remove_song_from_playlist`
- `apis.supervisor.complete_task`

## Failure Handling
- If an API call times out or returns a 5xx, retry up to 3 times with a short backoff.
- If pagination returns a page that is not a list, break the loop and log the error.
- If a playlist cannot be fetched (404), skip it and continue with other playlists.
- If the same song appears in multiple playlists, removal from one playlist does not affect the others; remove it from each where it matches.

## Verification
- Re-fetch the library and all playlists after the operation.
- Assert that no remaining song has a `release_date.year` that satisfies the removal condition.
- Print the count of removed songs and remaining songs for logging.
