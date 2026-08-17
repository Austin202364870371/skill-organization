---
name: Analyze Playlist Durations for Longest or Shortest
description: Retrieve all playlists from a user's Spotify library, calculate the total duration of each playlist by summing the durations of its songs, and return either the longest or shortest playlist duration based on a specified criterion.
---

## When to Use
- When tasked with determining the longest or shortest playlist duration in a Spotify library.

## Preconditions
- Access to a valid Spotify account with sufficient permissions.
- Availability of necessary API credentials (e.g., username and password).

## Procedure
1. Authenticate with Spotify to obtain an access token.
2. Fetch the list of all playlists in the user's library using pagination.
3. For each playlist, retrieve the list of songs.
4. For each song in a playlist, fetch its duration.
5. Sum the durations to compute the total playlist length.
6. Compare playlist durations to identify the longest or shortest.
7. Return the result rounded to the nearest integer.

## Relevant APIs / Tools
- `spotify.auth.token`
- `spotify.library.playlists`
- `spotify.playlists.{id}`
- `spotify.songs.{id}`

## Failure Handling
- If authentication fails, retry with stored credentials or notify the user.
- If a playlist or song cannot be retrieved, skip it and log the error.
- If no playlists exist, return an appropriate message.

## Verification
- Confirm that the returned value matches the expected longest or shortest duration.
- Validate that the total duration calculation is accurate across all playlists.
