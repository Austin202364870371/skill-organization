---
name: Export Unique Spotify Library Songs to CSV and Delete Account
description: Exports all unique songs from a user's song library, albums, and playlists to a CSV file with 'Title' and 'Artists' columns, then terminates the Spotify account.
---

## When to Use
Use when the user asks to back up all songs from their Spotify library (songs, albums, playlists) to a CSV file with headers 'Title' and 'Artists', and optionally terminate the account afterward.

## Preconditions
- Must have supervisor credentials to obtain Spotify and file system access tokens.
- The target file path is provided by the task (e.g., '~/backups/spotify.csv').
- Account deletion should be performed only after a successful backup.

## Procedure
1. Get the main user's profile and account passwords via `apis.supervisor.show_profile` and `apis.supervisor.show_account_passwords`.
2. Log into Spotify with `apis.spotify.login(username, password)` to get an access token.
3. Fetch all pages of `apis.spotify.show_song_library`, `apis.spotify.show_album_library`, and `apis.spotify.show_playlist_library`, passing `access_token` and increasing `page_index` until an empty page is returned. Collect all song IDs from:
   - The `song_id` field of each song in the song library.
   - The `song_ids` list of each album.
   - The `song_ids` list of each playlist.
4. Deduplicate song IDs with a set.
5. For each song ID, call `apis.spotify.show_song` to get the title and artist IDs. For each artist ID, call `apis.spotify.show_artist` to get the artist name. Group artist names by song title, preserving the order returned.
6. Build the CSV content: first line `Title,Artists`, then one line per unique song title with artist names joined by `|`.
7. Log into the file system with `apis.file_system.login(username, password)` to get an access token.
8. Write the content using `apis.file_system.create_file(file_path=..., content=..., access_token=...)`.
9. After the file is written, delete the Spotify account with `apis.spotify.delete_account(access_token=spotify_access_token)`.
10. Mark the task complete with `apis.supervisor.complete_task(status='success')`.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.spotify.login
- apis.spotify.show_song_library
- apis.spotify.show_album_library
- apis.spotify.show_playlist_library
- apis.spotify.show_song
- apis.spotify.show_artist
- apis.spotify.delete_account
- apis.file_system.login
- apis.file_system.create_file
- apis.supervisor.complete_task

## Failure Handling
- If any library call returns an error, retry the call. Continue pagination until an empty page is returned.
- If a song has no artists, leave the Artists cell empty.
- If the backup file cannot be written, do not delete the account; report the failure.
- If `complete_task` is omitted, the task is not marked done.

## Verification
- Read back the file if possible to verify headers and row count.
- Ensure no duplicate song titles appear in the output.
- Verify the account deletion succeeded (further Spotify calls should fail).
