---
name: Robust Pagination and Partial Failure Handling for Spotify Cleanup
description: Handles edge cases in Spotify library cleanup: very large libraries, paginated endpoint failures, token expiration mid-task, and verification after removal.
---

## When to Use
Use when the Spotify cleanup touches many items, when the process may be interrupted mid-way, or when you need to guarantee that no unintended item remains. This skill complements the primary cleanup procedure by making it resilient to real-world API constraints.

## Preconditions
- The primary Spotify cleanup skill is understood.
- The task requires deleting potentially hundreds of songs or albums.
- You are prepared to handle API errors gracefully.

## Procedure
1. **Fetch all data with fault-tolerant pagination** – Write a pagination helper that stops on an empty page, but also handles the case where a page may be `None` or raise an exception. Continue from the last successful page index after retrying.
2. **Perform deletions in batches with retry** – When deleting, batch the removals. If a deletion fails, retry a few times. If it still fails, re-authenticate and retry once more.
3. **Use conservative condition checks for albums** – For albums, if `song_ids` is empty or missing, treat the album as *not downloaded* unless explicitly liked. This prevents accidentally keeping an album with incomplete data.
4. **Verification after cleanup** – Re-fetch the song and album libraries (with pagination) and assert that every remaining item satisfies the intended keep condition. Also confirm that the number of items decreased by the expected amount (this can be approximated by comparing counts before the deletion phase).

## Relevant APIs / Tools
- `apis.spotify.login`
- `apis.spotify.show_song_library`
- `apis.spotify.show_album_library`
- `apis.spotify.show_downloaded_songs`
- `apis.spotify.show_liked_songs`
- `apis.spotify.show_liked_albums`
- `apis.spotify.remove_song_from_library`
- `apis.spotify.remove_album_from_library`
- `apis.supervisor.complete_task`

## Failure Handling
- **Empty page**: Some endpoints may return an empty list when there are no more items; stop pagination.
- **None page or error**: Retry the same `page_index` up to 3 times. If still failing, log the error and abort safely, leaving already-deleted items unchanged.
- **Token expiration**: If any call returns an authentication error, call `apis.spotify.login` again to obtain a fresh token and continue.
- **Partial deletion**: If the process aborts, rerun the cleanup – it is idempotent because items already removed will simply not be found, and remaining items will be processed correctly.

## Verification
- After all deletions, re-fetch the full song and album libraries.
- Confirm that for every remaining song, `keep` is true (checked with the same AND/OR condition).
- Confirm that for every remaining album, `keep` is true using the album-level rule.
- Optionally compare the initial vs. final counts to ensure deletions were not excessive.
