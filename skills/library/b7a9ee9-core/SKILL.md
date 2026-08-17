---
name: Iterate Through Playlist Songs and Follow Artists by Genre
description: Retrieve all playlists from a user's library, extract songs from each playlist, identify artist IDs based on specified genre criteria, and follow those artists.
---

## When to Use
- When tasked with expanding a user's music library by following artists based on specific genres.
- When needing to process multiple playlists and their associated tracks to gather artist information.

## Preconditions
- The user has a valid Spotify account with access credentials.
- The agent can authenticate with Spotify using stored credentials.
- The target genre is defined and recognizable.

## Procedure
1. Authenticate with Spotify to obtain an access token.
2. Retrieve the list of all playlists in the user's library using pagination.
3. For each playlist, fetch its contents to get the list of songs.
4. For each song, retrieve detailed metadata including artist and genre information.
5. If the song's genre matches the target genre, collect the artist ID.
6. After processing all playlists, iterate through the collected artist IDs and follow each one using the Spotify API.

## Relevant APIs / Tools
- `apis.spotify.access_token_from`
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_playlist`
- `apis.spotify.show_song`
- `apis.spotify.follow_artist`

## Failure Handling
- If authentication fails, retry with stored credentials or notify the user.
- If a playlist or song cannot be retrieved due to permissions or errors, skip it and log the issue.
- If following an artist fails, continue with other artists and report the failure.

## Verification
- Confirm that the access token is valid before proceeding with API calls.
- Ensure all playlists are successfully fetched and processed.
- Validate that artist IDs are correctly extracted and followed without error.
- Notify the user upon completion of the operation.
