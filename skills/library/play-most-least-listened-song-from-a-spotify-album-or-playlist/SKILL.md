---
name: Play Most/Least Listened Song from a Spotify Album or Playlist
description: Logs into Spotify, locates a specified album or playlist, retrieves each track's play count, selects the most or least listened track, and plays it.
---

## When to Use
Use when a user asks to play the most or least listened-to song from a specific Spotify album or playlist.

## Preconditions
- A supervisor profile exists and contains the user's Spotify credentials.
- Spotify is accessible through the AppWorld APIs.
- The target collection (album or playlist) and the desired extreme (most/least) are known.

## Procedure
1. Fetch the user profile and account passwords:
   - `profile = apis.supervisor.show_profile()`
   - `passwords = apis.supervisor.show_account_passwords()`
2. Obtain a Spotify access token by logging in:
   - `token = apis.spotify.login(username=profile.username, password=passwords['spotify'])`
3. Locate the collection:
   - If it is an album, paginate through `apis.spotify.search_albums(query=<album_title>, page_index=...)` until you find the exact album.
   - If it is a playlist, paginate through `apis.spotify.show_playlist_library(access_token=token, page_index=...)` until you find the playlist by title.
4. Retrieve the `song_ids` from the matched collection.
5. For each song ID, call `apis.spotify.show_song(song_id=...)` to get its metadata, including `play_count`.
6. Select the target song:
   - For "most", pick the song with the highest `play_count`.
   - For "least", pick the song with the lowest `play_count`.
7. Play the selected song using `apis.spotify.play_music(access_token=token, song_id=<selected_song_id>)`.
8. Mark the task complete with `apis.supervisor.complete_task(status="success")`.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.spotify.login
- apis.spotify.search_albums
- apis.spotify.show_playlist_library
- apis.spotify.show_song
- apis.spotify.play_music
- apis.supervisor.complete_task

## Failure Handling
- If login fails, verify the username/password pair from the supervisor profile.
- If the collection is not found on the first page, continue paginating; if still not found, report failure via `apis.supervisor.complete_task(status="failure")`.
- If a song has no `play_count`, treat it as 0 or skip it during selection.

## Verification
- Confirm the selected song has the minimum or maximum `play_count` in the collection.
- Confirm `apis.spotify.play_music` returns a successful response.
