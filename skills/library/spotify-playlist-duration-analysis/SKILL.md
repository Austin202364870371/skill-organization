---
name: Spotify Playlist Duration Analysis
description: Compute the total duration (in whole minutes, rounded to the nearest integer) of the user's longest or shortest Spotify playlist.
---

## When to Use
Use this skill when the user asks for the duration of their longest or shortest Spotify playlist, and the answer should be in minutes rounded to the nearest integer (e.g., "How long is my longest playlist in minutes?").

## Preconditions
- The user's Spotify account is linked and the `spotify` app is available.
- The supervisor profile and account passwords are available to obtain an access token.
- The user has at least one playlist.

## Procedure
1. **Authenticate**
   - Get an access token using `apis.spotify.access_token_from(main_user)`, **or** manually call `apis.supervisor.show_profile()` and `apis.supervisor.show_account_passwords()`, then `apis.spotify.login(username=..., password=...)`.

2. **Get all playlists**
   - Paginate through `apis.spotify.show_playlist_library(access_token=..., page_index=...)` starting at `page_index=0` until an empty page is returned.
   - Collect all playlist objects.

3. **Compute per-playlist duration**
   - For each playlist, call `apis.spotify.show_playlist(playlist_id=..., access_token=...)` to obtain its list of songs.
   - For each song, call `apis.spotify.show_song(song_id=...)` to get its `duration` in seconds.
   - Sum the song durations to get the total playlist duration in seconds.

4. **Choose the target playlist**
   - If the question asks for the **longest**, select the playlist with the **maximum** total duration.
   - If it asks for the **shortest**, select the **minimum**.

5. **Convert to minutes**
   - Compute `round(total_seconds / 60)` to get the duration in whole minutes.

6. **Submit the answer**
   - Call `apis.supervisor.complete_task(answer=<minutes>, status="success")`.

## Relevant APIs / Tools
- `apis.supervisor.show_profile`
- `apis.supervisor.show_account_passwords`
- `apis.spotify.login`
- `apis.spotify.access_token_from`
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_playlist`
- `apis.spotify.show_song`
- `apis.supervisor.complete_task`

## Failure Handling
- **No playlists:** answer `0` and complete successfully.
- **Empty playlist:** its total duration is `0` seconds; handle it like any other playlist.
- **Missing song data:** if `apis.spotify.show_song` fails, skip that song or treat its duration as `0` and proceed.
- **Token expiration:** re-authenticate with `apis.spotify.login`.

## Verification
- Confirm that all pages of the library were fetched.
- Print each playlist's total duration to sanity-check the extremum selection.
- Ensure the final answer is an integer and equals the rounded duration of the selected playlist.
