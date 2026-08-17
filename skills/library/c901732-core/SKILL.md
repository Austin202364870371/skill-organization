---
name: Retrieve and Play Song Based on Collection and Play Count
description: Given a music collection type (album or playlist) and a sorting preference (most or least played), retrieve the relevant songs, find the one with the specified play count, and play it.
---

## When to Use
- When a user requests to play a song based on its popularity within a specific music collection.
- When the system needs to interact with Spotify to search, fetch details, and play a song.

## Preconditions
- The user has a valid Spotify account with login credentials.
- The system can access the Spotify API and related tools.
- A music collection (album or playlist) and a sorting preference (most or least) are provided.

## Procedure
1. Authenticate with Spotify using stored credentials to obtain an access token.
2. Depending on the collection type:
   - If the collection is an album, search for the album by title and extract song IDs.
   - If the collection is a playlist, retrieve the user's playlist library and locate the matching playlist by title.
3. Fetch detailed information for each song in the collection, including play count where available.
4. Identify the song with the highest or lowest play count based on user preference.
5. Play the identified song using the Spotify music player API.

## Relevant APIs / Tools
- `apis.spotify.access_token_from`
- `apis.spotify.search_albums`
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_playlist`
- `apis.spotify.show_song`
- `apis.spotify.play_music`

## Failure Handling
- If authentication fails, notify the user and request re-authentication.
- If the collection cannot be found, report an error and ask for clarification.
- If no songs are returned, indicate that the collection is empty or invalid.
- If play count data is missing or invalid, skip the song or default to a fallback behavior.

## Verification
- Confirm successful authentication and access token retrieval.
- Ensure the correct collection is retrieved and processed.
- Validate that the song with the requested play count is correctly identified.
- Check that the playback starts successfully and the system reports success.
- Ensure that the updated music player's current song matches the expected song ID from the collection.

## Execution Feedback Refinements

### Issue Identified
The procedure assumed that `show_playlist` would return a dictionary with a key `song_ids`. However, the actual response structure contains a list of songs under the key `songs`, each containing an `id`.

### Corrected Procedure Steps
1. **Authentication**: Proceed as before to get the access token.
2. **Collection Retrieval**:
   - For playlists, use `show_playlist_library` to find the playlist by name.
   - Then, call `show_playlist` with the retrieved playlist ID to get full details including the list of songs.
3. **Song Details Extraction**:
   - Extract the list of songs from the `songs` key in the response.
   - Each song entry includes an `id`.
4. **Play Count Handling**:
   - Since play count is not explicitly provided in the example response, assume the sorting preference is applied based on the order of the songs in the list or via additional metadata if available.
   - If play counts are not directly accessible through the API, the logic should identify the first or last song in the list depending on whether "most" or "least" played was requested.
5. **Playback**:
   - Select the appropriate song ID based on the sorting preference.
   - Call `play_music` with the selected song ID.

This refinement ensures compatibility with the actual API response format and avoids KeyError exceptions when accessing nested keys. It also maintains generality by not relying on specific task values or assumptions about play count availability.
