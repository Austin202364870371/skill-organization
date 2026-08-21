---
name: handle_spotify_artist_sync_edge_cases
description: Covers edge cases and robust practices for syncing Spotify followed artists with liked songs, such as pagination continuity, multi-artist songs, idempotent updates, and graceful failure reporting.
---

## When to Use
Use this skill as a companion to the primary sync skill when any of the following are true:
- The task requires following/unfollowing artists and the result must be exactly correct.
- There may be many pages of liked songs or followed artists.
- A liked song may have multiple artists, or an artist may appear in many liked songs.
- You want to avoid duplicate API calls or handle failures cleanly.

## Preconditions
- You have already obtained a valid Spotify access token.
- You understand the data shape of artist objects (each artist has an `id`; liked songs have an `artists` list).

## Procedure
1. When paginating, always check whether the returned page is empty. Stop only when an empty list is returned, not before fetching the next page. Use a `while True` loop and break on empty.
2. When building the liked-artist set, iterate over every song's `artists` array and extract the `id` field. Do not assume each song has only one artist.
3. Compare sets instead of lists to make the operation idempotent. For follow actions, skip artist IDs already present in the followed set. For unfollow actions, skip artist IDs that are in the liked-artist set.
4. If the action is unknown or ambiguous, do not perform any mutations. Instead, call `apis.supervisor.complete_task(status="failure")` with a descriptive message.
5. If the user has no liked songs, then for an unfollow task every followed artist should be unfollowed; for a follow task no action is needed. Handle empty sets explicitly.
6. After all mutations, re-fetch the followed-artist list once and verify the final state matches the expected set. If verification fails, send a failure status.

## Relevant APIs / Tools
- apis.spotify.show_following_artists
- apis.spotify.show_liked_songs
- apis.spotify.follow_artist
- apis.spotify.unfollow_artist
- apis.supervisor.complete_task

## Failure Handling
- If a specific follow/unfollow call fails, record the artist ID and continue with the rest. At the end, if any operations failed, call `apis.supervisor.complete_task(status="failure")` rather than silently succeeding.
- If the access token expires during pagination, re-authenticate and resume from the last successful page index.
- If the API returns duplicate entries within a page, the set-based logic will naturally deduplicate them.

## Verification
- Verify that the size of the followed-artist set changes by exactly the number of expected operations (if the task is incremental).
- For unfollow tasks, confirm that no remaining followed artist has a liked song.
- For follow tasks, confirm that every liked-song artist ID is now in the followed set.
