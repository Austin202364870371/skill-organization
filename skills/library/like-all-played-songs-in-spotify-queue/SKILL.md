---
name: like_all_played_songs_in_spotify_queue
description: Likes every song in the Spotify playback queue that has already played, including the currently playing song. Works when the queue contains the current song and past songs.
---

## When to Use
Use this skill when the user asks to like all songs played so far in their Spotify music player queue, including the current one.

## Preconditions
- The user's Spotify account credentials are available via `apis.supervisor.show_account_passwords`.
- The user's Spotify profile is accessible via `apis.supervisor.show_profile`.
- An access token can be obtained for the main user.

## Procedure
1. Retrieve the main user's profile and account passwords from the supervisor.
2. Obtain a Spotify access token for the main user (e.g., `apis.spotify.access_token_from(main_user)` or via `apis.spotify.login` with the retrieved credentials).
3. Fetch the current song with `apis.spotify.show_current_song(access_token=access_token)`.
4. Fetch the song queue with `apis.spotify.show_song_queue(access_token=access_token)`.
5. Iterate over the queue in order, collecting song IDs until you reach the current song's ID (inclusive of the current song).
6. Call `apis.spotify.like_song(access_token=access_token, song_id=song_id)` for each collected song ID. Use `raise_on_failure=False` to avoid aborting if a song is already liked.
7. Call `apis.supervisor.complete_task(status="success")`.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.spotify.login
- apis.spotify.show_current_song
- apis.spotify.show_song_queue
- apis.spotify.like_song
- apis.supervisor.complete_task

## Failure Handling
- If the current song or queue cannot be fetched, retry once; if it still fails, report status="failure".
- If the current song is not found in the queue, like the entire queue as a fallback.
- If `like_song` raises for an individual song, continue with the next song.

## Verification
- After liking, optionally re-fetch the queue and confirm each expected song appears in the liked songs or that no error was raised.
