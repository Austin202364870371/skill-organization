---
name: Find the most or least liked/played song in a Spotify library
description: Authenticate with Spotify, gather all songs from the user's playlist, album, or saved-song library, and return the title of the song with the highest or lowest like or play count.
---

## When to Use
Use this workflow when asked to identify the song in the user's Spotify library (playlists, albums, or saved songs) with the most/least likes or plays, and return its title.

## Preconditions
- The user is the main user.
- Need to retrieve the user's Spotify credentials via the supervisor.
- The instruction names a library type: playlists, album library, or song library.

## Procedure
1. Fetch the main user's profile and account passwords using `apis.supervisor.show_profile` and `apis.supervisor.show_account_passwords`.
2. Obtain an access token by calling `apis.spotify.login` with the username and password from step 1.
3. Based on the library type in the instruction:
   - **Playlists**: paginate through `apis.spotify.show_playlist_library`, collecting `song_ids` from each playlist.
   - **Albums**: paginate through `apis.spotify.show_album_library`, collecting `song_ids` from each album.
   - **Saved songs**: paginate through `apis.spotify.show_song_library`, collecting `song_id` from each returned song.
4. Deduplicate all collected song IDs (use a set).
5. For each unique song ID, call `apis.spotify.show_song` to get detailed information.
6. Determine the metric attribute: `like_count` if the instruction says "liked", `play_count` if it says "played".
7. If the instruction asks for "most", find the song with the maximum value of that attribute; for "least", find the minimum.
8. Return the `title` of the selected song via `apis.supervisor.complete_task` with status `success`.

## Relevant APIs / Tools
- `apis.supervisor.show_profile`
- `apis.supervisor.show_account_passwords`
- `apis.spotify.login`
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_album_library`
- `apis.spotify.show_song_library`
- `apis.spotify.show_song`
- `apis.supervisor.complete_task`

## Failure Handling
- If a page request fails, retry with the same `page_index`.
- If login fails, double‑check the credentials from the supervisor and retry.
- If the library is empty, complete the task with a message stating that no songs were found.
- If multiple songs tie on the metric, any of them is acceptable; the instruction generally does not require a tie‑breaker.

## Verification
- Ensure that pagination covered all pages; stop only when a page returns no more items.
- Confirm all song IDs were fetched and deduplicated.
- Re‑evaluate the extreme by scanning all fetched songs' metric values.
- Verify the returned value is a song title and the task status is `success`.
