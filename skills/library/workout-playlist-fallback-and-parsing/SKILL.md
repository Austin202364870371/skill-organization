---
name: workout_playlist_fallback_and_parsing
description: Handles edge cases and failures in the workout-playlist workflow: missing or unparseable plan content, absent playlists, insufficient playlist durations, authentication retries, and robust duration extraction. Provides fallback strategies and proper task completion signaling.
---

## When to Use
Use when the primary workout-playlist selection cannot complete due to missing notes, unparseable content, insufficient playlists, authentication issues, or when the exact weekday block is unavailable.

## Preconditions
- Same as primary, but some precondition is failing or data is not in the expected format.

## Procedure
1. Verify credentials and retry login (e.g., using `apis.supervisor.show_account_passwords` to re-fetch credentials) if authentication fails.
2. If no workout note is found, broaden the search query (e.g., "exercise", "plan", "routine"); if still missing, report failure via `apis.supervisor.complete_task` with a failure status.
3. When extracting today's duration, use a robust regex (e.g., `(\d+)\s*mins?`) and gracefully handle missing/extra whitespace.
4. If today's block is absent, fall back to the first numeric duration found in the content, or the last one if that makes more sense for the schedule.
5. If no playlist meets the required duration, compute all playlist durations and select the longest one as fallback; still attempt to start playback.
6. If Spotify has no playlists at all, clearly report that no valid playlist exists and complete the task with failure.
7. Always call `apis.supervisor.complete_task` with the appropriate status, even when the task cannot be completed successfully.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.phone.get_current_date_and_time
- apis.simple_note.login
- apis.simple_note.search_notes
- apis.simple_note.show_note
- apis.spotify.login
- apis.spotify.show_playlist_library
- apis.spotify.show_song
- apis.spotify.play_music
- apis.supervisor.complete_task

## Failure Handling
- **Authentication**: re-fetch credentials and retry login; if repeated failures, abort with failure status.
- **Pagination**: always paginate through both search results and playlist library.
- **Parsing**: use regex fallback; treat missing durations as 0 and handle `None` responses gracefully.
- **Duration comparison**: if a playlist's `song_ids` are empty, its duration is 0; skip or handle accordingly.
- **Playback errors**: if `play_music` raises, attempt the next best playlist once; if all fail, report failure.

## Verification
- Ensure the selected playlist's computed duration is >= the target, or, if falling back, confirm the longest was chosen and playback started.
- Verify that `complete_task` was called with the correct status (success or failure) and that any failure reason is clear.
