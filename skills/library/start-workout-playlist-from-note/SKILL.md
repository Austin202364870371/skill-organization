---
name: start_workout_playlist_from_note
description: Select and play a Spotify playlist that is long enough to cover today's workout duration, using a workout plan stored in Simple Note. Paginates through notes and playlists, computes total playlist duration from individual songs, starts playback, and completes the task.
---

## When to Use
Use when the user wants to start a Spotify playlist that lasts at least as long as a scheduled activity (e.g., workout) without switching playlists, and the activity plan/duration is stored in a Simple Note.

## Preconditions
- User has access to Simple Note and Spotify (credentials available via supervisor).
- A Simple Note contains the activity plan, with a schedule by weekday and a duration in minutes.
- The Spotify user has at least one playlist in their library.

## Procedure
1. Retrieve the current day of week using `phone.get_current_date_and_time` (or `DateTime.now()` in code).
2. Obtain authentication tokens for Simple Note and Spotify using `apis.simple_note.login` / `apis.spotify.login` (or the environment's convenience access-token helpers).
3. Search Simple Note for the plan using a relevant query like "workout" or "plan" via `apis.simple_note.search_notes` (paginate to get all results).
4. Open the matching note with `apis.simple_note.show_note` and parse its content. Look for a block for the current weekday and extract the `duration_mins` value.
5. List the user's Spotify playlists with `apis.spotify.show_playlist_library` (paginate).
6. For each playlist, iterate its `song_ids` and call `apis.spotify.show_song` to get each song's `duration` (in seconds). Sum durations and convert to minutes.
7. Select the first playlist whose total duration is >= the required workout duration.
8. Start playback with `apis.spotify.play_music(access_token=..., playlist_id=...)`.
9. Call `apis.supervisor.complete_task(status="success")`.

## Relevant APIs / Tools
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
- If no note is found, try alternative search terms (e.g., "exercise", "plan", "routine").
- If the current weekday is missing from the plan, fall back to searching the whole content for any duration that fits today's schedule, or ask the user for clarification.
- If the duration cannot be parsed, try a regex to extract any integer followed by "mins" from the content.
- If no playlist is long enough, select the longest available playlist as a best-effort (but note this does not satisfy the "no change" guarantee).

## Verification
- Confirm that a playlist was started by checking the response of `play_music` or querying the current playback state.
- Recalculate the chosen playlist's total duration and verify it is >= the required duration from the note.
