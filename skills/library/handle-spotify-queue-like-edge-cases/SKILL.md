---
name: handle_spotify_queue_like_edge_cases
description: Handles edge cases and alternative success paths for liking played Spotify songs: empty queue, current song absent from queue, queue only containing upcoming songs, and already-liked songs.
---

## When to Use
Use this skill when the primary workflow for liking played Spotify songs fails or when the queue structure is unexpected (e.g., queue starts with upcoming songs, current song is missing, or some songs are already liked).

## Preconditions
- Spotify access token is available.
- `show_current_song` and `show_song_queue` can be called.

## Procedure
1. Fetch the current song and the song queue.
2. Determine where the current song appears in the queue.
   - If the current song is the first element, it means no songs have played before it, so only like the current song.
   - If the queue is empty, there is nothing to like; complete the task successfully.
   - If the current song is not found in the queue, assume the whole queue represents played songs and like all entries.
3. For each target song, call `apis.spotify.like_song` with `raise_on_failure=False` so already-liked songs do not cause errors.
4. Verify that at least one song was liked (if there were any songs). If all like calls failed, report status="failure".

## Relevant APIs / Tools
- apis.spotify.show_current_song
- apis.spotify.show_song_queue
- apis.spotify.like_song
- apis.supervisor.complete_task

## Failure Handling
- If the queue is empty, call `apis.supervisor.complete_task(status="success")` with no likes.
- If the current song is not in the queue, fall back to liking the entire queue.
- Always pass `raise_on_failure=False` to `like_song` to ignore individual already-liked failures.

## Verification
- After execution, confirm that all intended song IDs were processed. If any like returned an error, review the API response and decide whether to retry.
