---
name: Filter and Remove Media Items Based on Download and Like Status
description: A core procedural skill for filtering and removing media items (songs or albums) from a user's library based on whether they are downloaded, liked, or both, depending on a specified logical operation (AND/OR).
---

## When to Use
- When managing a user's Spotify library by removing songs or albums that do not meet specific criteria.
- When cleaning up a media library by deleting items that are neither downloaded nor liked, or based on other boolean combinations.

## Preconditions
- The user has a valid Spotify account with access credentials.
- The agent has access to the Spotify API and necessary permissions.
- The user has provided a logical operation ("and" or "or") to determine which items to retain.

## Procedure
1. Authenticate with Spotify to obtain an access token.
2. Retrieve lists of songs and albums in the user's library, handling pagination.
3. Fetch lists of downloaded songs and liked songs/albums.
4. For each item in the library:
   - Determine if it is downloaded and/or liked.
   - Apply the logical operation (AND/OR) to decide if it should be kept.
5. If an item should not be kept, remove it from the library using the appropriate API endpoint.
6. Verify that only items matching the criteria remain in the library by checking the updated counts and comparing with expected results.

## Relevant APIs / Tools
- `apis.spotify.access_token_from`
- `apis.spotify.show_song_library`
- `apis.spotify.show_album_library`
- `apis.spotify.show_downloaded_songs`
- `apis.spotify.show_liked_songs`
- `apis.spotify.show_liked_albums`
- `apis.spotify.remove_song_from_library`
- `apis.spotify.remove_album_from_library`

## Failure Handling
- Retry failed API calls with exponential backoff.
- Log errors and notify the user if critical failures occur during authentication or removal steps.

## Verification
- Confirm that the number of items in the library decreases after deletion.
- Validate that only items matching the criteria remain in the library.
- Ensure that the exact set of removed items matches predefined expectations.
