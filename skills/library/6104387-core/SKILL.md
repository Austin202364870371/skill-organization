---
name: SKILL.md
description: - When tasked with backing up or exporting a user's entire media library (e.g., Spotify) to a persistent storage location.
---

# SKILL.md

---
name: Aggregate and Export User Media Library Data
description: Retrieve all songs, albums, and playlists from a user's media library, extract associated artist information, compile into a structured CSV format, and save it to a file system.
---

## When to Use
- When tasked with backing up or exporting a user's entire media library (e.g., Spotify) to a persistent storage location.

## Preconditions
- The user has valid credentials for both the media service (e.g., Spotify) and the file system.
- Access tokens are available for both services.

## Procedure
1. Authenticate with the media service using stored credentials to obtain an access token.
2. Retrieve paginated lists of songs, albums, and playlists from the user's library.
3. Collect unique identifiers (IDs) for all items across these categories.
4. For each item (song), fetch detailed metadata including associated artist IDs.
5. For each artist ID, retrieve artist details to map titles to artist names.
6. Compile the collected data into a structured CSV string with headers 'Title' and 'Artists'.
7. Authenticate with the file system using stored credentials to obtain a file system access token.
8. Write the compiled CSV content to a specified file path in the file system.

## Relevant APIs / Tools
- `apis.spotify.login`
- `apis.spotify.show_song_library`
- `apis.spotify.show_album_library`
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_song`
- `apis.spotify.show_album`
- `apis.spotify.show_playlist`
- `apis.spotify.show_artist`
- `apis.file_system.login`
- `apis.file_system.create_file`

## Failure Handling
- If any API call fails due to invalid credentials or network issues, attempt re-authentication or retry based on error type.
- If a media item cannot be retrieved, log the failure and continue processing remaining items.
- If file creation fails, notify the user and retry up to a maximum number of attempts.

## Verification
- Confirm that all retrieved items have been processed and added to the dataset.
- Validate that the final CSV file contains expected columns and data entries.
- Ensure that the file is successfully written to the designated file system path.
