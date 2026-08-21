---
name: Robust Pagination and Failure Handling for Spotify Genre-Follow
description: Handles edge cases in the genre-follow workflow: manual pagination when helper utilities are unavailable, duplicate artists, already-followed artists, missing genre fields, and partial follow failures.
---

## When to Use
Use when the primary workflow hits an edge case: pagination is incomplete, song metadata is missing, an artist is already followed, or a follow request fails but the overall task should continue.

## Preconditions
- Spotify access token is already available.
- At least one playlist may or may not exist.

## Procedure
1. **Manual pagination**: If `find_all_from_pages` or the `.has_next` property is not available, loop over `page_index` starting at 0 and stop when `playlists` is empty or the API signals no more pages.
2. **Deduplicate artists**: Use a `set` to collect artist IDs before following so you never attempt the same follow twice.
3. **Handle missing genre**: If `details.genre` is `None`, empty, or not the target genre, skip the song. Do not assume missing genre means match.
4. **Follow with resilience**: Call `apis.spotify.follow_artist(..., raise_on_failure=False)`. Check the returned status; if it indicates already-followed or error, move on.
5. **Complete with partial success**: If some follows fail but the remaining ones succeed, still call `apis.supervisor.complete_task(status="success")` as long as the task's main goal was achieved.

## Relevant APIs / Tools
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_playlist`
- `apis.spotify.show_song`
- `apis.spotify.follow_artist`
- `apis.supervisor.complete_task`

## Failure Handling
- **Page request fails**: Retry the same `page_index` a few times; if still failing, abort gracefully and report the failure.
- **Already followed**: The follow API may return an error; with `raise_on_failure=False`, continue to the next artist.
- **Duplicate artists across playlists**: The `set` prevents duplicate follow calls.
- **Empty library**: No playlists returned → skip all following and complete with success.

## Verification
- Verify the number of unique followed artists matches the number of unique matching song artists.
- Confirm `complete_task` was called even when some non-critical failures occurred.
