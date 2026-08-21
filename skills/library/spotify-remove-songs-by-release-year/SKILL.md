---
name: spotify_remove_songs_by_release_year
description: Removes songs from a user's Spotify library and all their playlists based on the song's release year relative to a threshold (e.g., before, after, in or before, in or after).
---

## When to Use
Use when a user asks to remove songs from their Spotify library and/or all their playlists based on the song's release year compared with a threshold year. The comparison can be "before", "after", "in or before", or "in or after" a given year.

## Preconditions
- The user's Spotify account credentials are available via `supervisor.show_account_passwords` or `supervisor.show_profile`.
- The user has a profile in the system.
- You have access to the AppWorld API collection.

## Procedure
1. Obtain the user profile and account passwords:
   ```python
   profile = apis.supervisor.show_profile()
   passwords = apis.supervisor.show_account_passwords()
   spotify_creds = passwords["spotify"]  # contains username/password
   ```
2. Authenticate to Spotify:
   ```python
   token_response = apis.spotify.login(username=spotify_creds["username"], password=spotify_creds["password"])
   access_token = token_response["access_token"]
   ```
   (Alternatively use `apis.spotify.access_token_from(main_user)` if available.)
3. Determine the threshold year and comparison mode from the user's request. For example, "before 2021" means `threshold_year=2021` and `mode="before"`. Implement a helper `should_remove(release_year)` using `<`, `>`, `<=`, or `>=` accordingly.
4. Remove matching songs from the library:
   - Paginate through `apis.spotify.show_song_library(access_token=access_token, page_index=i)` until an empty page is returned.
   - For each `song_id` in the page, call `apis.spotify.show_song(song_id=song_id)` to get `release_date`.
   - If `should_remove(song.release_date.year)`, call `apis.spotify.remove_song_from_library(access_token=access_token, song_id=song_id)`.
5. Remove matching songs from all playlists:
   - Paginate through `apis.spotify.show_playlist_library(access_token=access_token, page_index=i)` until an empty page.
   - For each playlist, call `apis.spotify.show_playlist(access_token=access_token, playlist_id=playlist.playlist_id)` to get its `songs`.
   - For each song in the playlist, get its full details with `apis.spotify.show_song(song_id=song.id)` (or `song.song_id`, depending on the response shape).
   - If `should_remove(song.release_date.year)`, call `apis.spotify.remove_song_from_playlist(access_token=access_token, playlist_id=playlist.playlist_id, song_id=song.song_id)`.
6. After all removals, call `apis.supervisor.complete_task(answer=None, status="success")`.

## Relevant APIs / Tools
- `apis.supervisor.show_profile`
- `apis.supervisor.show_account_passwords`
- `apis.spotify.login`
- `apis.spotify.show_song_library`
- `apis.spotify.show_song`
- `apis.spotify.remove_song_from_library`
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_playlist`
- `apis.spotify.remove_song_from_playlist`
- `apis.supervisor.complete_task`

## Failure Handling
- If pagination returns an error or an unexpected structure, stop and inspect the last page index.
- If a song removal fails with a 404, it likely was already removed; continue with the next item.
- If the playlist contains duplicate songs, removing one instance is enough; subsequent removals will also succeed or 404.

## Verification
- After the operation, re-run `apis.spotify.show_song_library` and `apis.spotify.show_playlist` for each playlist to confirm no songs matching the condition remain.
- Optionally compare counts before and after.
