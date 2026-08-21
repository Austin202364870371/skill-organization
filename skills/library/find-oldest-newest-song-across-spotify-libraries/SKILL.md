---
name: Find oldest/newest song across Spotify libraries
description: Aggregates songs from a user's Spotify song, album, and playlist libraries, maps each song to its release date, and returns the title of the oldest or newest released song.
---

## When to Use
Use when asked to find the title of the oldest or newest released song in a Spotify account, considering saved songs, albums, and playlists.

## Preconditions
- Supervisor profile and account passwords are available.
- Spotify credentials are accessible via `apis.supervisor.show_account_passwords()`.

## Procedure
1. Get the current user profile with `apis.supervisor.show_profile()`.
2. Get account passwords with `apis.supervisor.show_account_passwords()` and extract Spotify username/password.
3. Obtain an access token with `apis.spotify.login(username=..., password=...)`.
4. Initialize an empty dictionary `release_by_song_id`.
5. Paginate `apis.spotify.show_song_library(access_token=..., page_index=i)` until an empty page is returned. For each song, call `apis.spotify.show_song(song_id=...)` and store `release_by_song_id[song_id] = song.release_date`.
6. Paginate `apis.spotify.show_album_library(...)`. For each album and each `song_id` in `album.song_ids`, set `release_by_song_id[song_id] = album.release_date`.
7. Paginate `apis.spotify.show_playlist_library(...)`. For each playlist and each `song_id` in `playlist.song_ids`, call `apis.spotify.show_song(song_id=...)` and store its release date.
8. Determine the target song id: if the task asks for oldest use `min(release_by_song_id, key=release_by_song_id.get)`; for newest use `max(...)`.
9. Fetch the song details with `apis.spotify.show_song(song_id=target_id)` and complete the task with the title using `apis.supervisor.complete_task(answer=song.title, status="success")`.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.spotify.login
- apis.spotify.show_song_library
- apis.spotify.show_album_library
- apis.spotify.show_playlist_library
- apis.spotify.show_song
- apis.supervisor.complete_task

## Failure Handling
- If login fails, re-check credentials and retry.
- If a paginated call fails, retry the same `page_index` before giving up.
- If an album has no release date, fall back to `apis.spotify.show_song` for each song in that album.

## Verification
- Confirm the chosen song has the minimum/maximum release date among all collected song ids.
- Ensure the final `apis.supervisor.complete_task` call includes the correct title and `status="success"`.
