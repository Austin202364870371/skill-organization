---
name: Spotify Library Cleanup by Liked/Downloaded Status
description: Cleans up a user's Spotify song and album libraries by keeping only items that match a liked/downloaded condition (AND or OR), and removing all others. Playlists are left untouched.
---

## When to Use
Use when the user wants to remove songs or albums from their Spotify library based on whether they are liked, downloaded, or both. The condition is typically phrased as 'keep only songs/albums that are liked or downloaded' or 'liked and downloaded'.

## Preconditions
- The user is the main user with an active Spotify account.
- You have access to the supervisor profile and account passwords.
- Spotify API is available.

## Procedure
1. **Authenticate** – Retrieve the user profile and Spotify credentials via `apis.supervisor.show_profile` and `apis.supervisor.show_account_passwords`. Then obtain an access token using `apis.spotify.login` with the Spotify username and password.
2. **Fetch all relevant data** – Use pagination to retrieve:
   - `apis.spotify.show_song_library` (all songs in song library)
   - `apis.spotify.show_album_library` (all albums in album library)
   - `apis.spotify.show_downloaded_songs` (all downloaded songs)
   - `apis.spotify.show_liked_songs` (all liked songs)
   - `apis.spotify.show_liked_albums` (all liked albums)
   Each endpoint takes `access_token` and `page_index`; keep paging until an empty page is returned.
3. **Build ID sets** – Create sets of `song_id` for downloaded and liked songs, and `album_id` for liked albums.
4. **Determine keep condition** – From the instruction, decide whether the required relation is `OR` (liked OR downloaded) or `AND` (liked AND downloaded). For albums, an album is considered downloaded **only if every song in the album is downloaded** (check all IDs in `album.song_ids` against the downloaded set).
5. **Clean songs** – For each song in the song library, compute `keep = (is_downloaded or is_liked)` or `keep = (is_downloaded and is_liked)` accordingly. If `not keep`, call `apis.spotify.remove_song_from_library(access_token, song_id)`.
6. **Clean albums** – For each album in the album library, compute `is_downloaded = all(sid in downloaded_song_ids for sid in album.song_ids)` and `is_liked = album.album_id in liked_album_ids`. Apply the same AND/OR rule. If `not keep`, call `apis.spotify.remove_album_from_library(access_token, album_id)`.
7. **Complete task** – After all removals, call `apis.supervisor.complete_task(answer=None, status="success")`.

## Relevant APIs / Tools
- `apis.supervisor.show_profile`
- `apis.supervisor.show_account_passwords`
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
- If `apis.spotify.login` fails, verify that the username and password are correct by re-checking `show_account_passwords`.
- If any list endpoint returns an error, retry the same page after a short pause.
- If a removal call fails because the token expired, re-authenticate and resume from the current page.

## Verification
- Re-fetch the song and album libraries after cleanup and confirm no item remains that does not satisfy the keep condition.
- Optionally verify that playlists were not modified.
