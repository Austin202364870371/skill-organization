---
name: Conditional Media Item Management

description: A reusable skill for conditionally adding, removing, or modifying media items (songs, albums) in a user's Spotify library based on boolean logic applied to metadata or status fields.
---

## When to Use
- When managing a user's Spotify library by applying conditional logic to filter and modify media items.
- When performing bulk operations on media items based on metadata attributes or user interaction statuses.

## Preconditions
- The user has a valid Spotify account with access credentials.
- The agent has access to the Spotify API and necessary permissions.
- Condition logic and item metadata are provided as inputs.

## Procedure
1. Authenticate with Spotify to obtain an access token.
2. Retrieve the user's media library (songs and albums) using pagination.
3. For each media item, evaluate its metadata or status fields against the provided condition logic (e.g., AND/OR combination of liked/downloaded status).
4. Based on the evaluation result, perform the corresponding action (add, remove, or modify) using the appropriate API endpoint.
5. Handle any API response errors and ensure consistency of library state.

## Relevant APIs / Tools
- `spotify.remove_album_from_library`
- `spotify.remove_song_from_library`
- `spotify.follow_artist`
- `spotify.show_song_library`
- `spotify.show_album_library`
- `spotify.show_downloaded_songs`
- `spotify.show_liked_songs`
- `spotify.show_liked_albums`
- `spotify.access_token_from`

## Failure Handling
- Retry failed API calls with exponential backoff.
- Log errors and notify the user if critical failures occur during authentication or modification steps.
- Skip individual items that fail to process while continuing with others.

## Verification
- Confirm that media items are correctly added, removed, or modified based on the condition logic.
- Validate that the final library state reflects the intended outcome of the conditional operation.
