---
name: Filter and Remove Media by Release Year
description: Remove media items (songs) from a user's Spotify library and playlists based on their release year relative to a specified target year.
---

## When to Use
- When a user wants to delete songs from their library or playlists that were released before, after, or around a specific year.

## Preconditions
- The user has a valid Spotify account with access credentials.
- The system has access to the Spotify API and necessary authentication tokens.

## Procedure
1. Authenticate with Spotify to obtain an access token.
2. Retrieve the user's entire song library using pagination.
3. For each song, fetch its release date using the song ID.
4. Compare the song's release year against the target year based on the filter criteria (before, after, in or before, in or after).
5. If the condition is met, remove the song from the library.
6. Retrieve the user's playlist library using pagination.
7. For each playlist, fetch the list of songs.
8. For each song in the playlist, fetch its release date.
9. Apply the same filtering logic to determine if the song should be removed.
10. If the condition is met, remove the song from the playlist.

## Relevant APIs / Tools
- `spotify.auth.token`
- `spotify.library.songs`
- `spotify.songs.{id}`
- `spotify.library.songs.{id}`
- `spotify.library.playlists`
- `spotify.playlists.{id}`
- `spotify.playlists.{id}.songs.{id}`

## Failure Handling
- If authentication fails, retry with stored credentials or prompt user for correct details.
- If API calls fail due to rate limits, implement exponential backoff.
- If a song or playlist cannot be accessed, log error and continue processing remaining items.

## Verification
- Confirm successful removal of songs from both library and playlists by verifying no longer present in respective lists.
- Ensure that only songs matching the filter criteria are removed.
