---
name: Retrieve and Analyze Spotify Library Data
description: Retrieve paginated Spotify library data (playlists, albums, or songs) based on user selection, collect song identifiers, fetch detailed song information, and analyze metrics (like count or play count) to determine the most or least popular song.
---

## When to Use
- When tasked with identifying the most or least liked or played song from a user's Spotify library.
- When needing to process large datasets from Spotify's paginated API endpoints.

## Preconditions
- The user has a valid Spotify account with access credentials.
- The agent has access to supervisor APIs for retrieving account details and sending responses.

## Procedure
1. Authenticate with Spotify using stored credentials via `apis.spotify.access_token_from`.
2. Determine the type of library data to retrieve (playlists, albums, or songs) based on user input.
3. Fetch data in paginated form using appropriate Spotify API calls (`show_playlist_library`, `show_album_library`, or `show_song_library`).
4. Collect unique song identifiers from the retrieved data.
5. For each song ID, call `apis.spotify.show_song` to get detailed metadata.
6. Based on user input, select a metric (e.g., like count or play count).
7. Identify the song with the highest or lowest value for that metric.
8. Return the title of the identified song.

## Relevant APIs / Tools
- `apis.spotify.access_token_from`
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_album_library`
- `apis.spotify.show_song_library`
- `apis.spotify.show_song`
- `apis.supervisor.message`
- `apis.supervisor.profile`
- `apis.supervisor.account_passwords`

## Failure Handling
- If authentication fails, retry with updated credentials or notify the user.
- If pagination returns no data, confirm whether the library is empty or if there was an error.
- If song data cannot be retrieved, log the missing IDs and continue processing other songs.

## Verification
- Confirm that the correct library type is selected before fetching data.
- Validate that all song IDs are successfully retrieved and processed.
- Ensure the final result matches the expected metric (most/least liked or played).

## Notes
- The `apis.spotify.show_song` function does not accept an `access_token` parameter; it should be called with only the required `song_id`.
- The procedure assumes that the user will provide sufficient context to determine the desired metric and library type.
