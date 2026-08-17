---
name: Set Aggregation Across Media Types
description: Collect and group media items (songs, albums, playlists) from various sources to compute totals, averages, or counts.
---

## When to Use
- When tasked with aggregating media items across multiple types (e.g., counting total songs, calculating average album length) from a user's library.

## Preconditions
- Valid access tokens for the media service (e.g., Spotify).
- Access to required APIs for retrieving media items and their metadata.

## Procedure
1. Authenticate with the media service using stored credentials to obtain an access token.
2. Retrieve paginated lists of specified media types (songs, albums, playlists) from the user's library.
3. Collect unique identifiers (IDs) for all retrieved items.
4. For each item, fetch detailed metadata as needed.
5. Apply the specified aggregation function (e.g., count, sum, average) to the collected data.
6. Return the aggregated result along with a statistical summary.

## Relevant APIs / Tools
- `apis.spotify.access_token_from`
- `apis.spotify.show_song_library`
- `apis.spotify.show_album_library`
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_song`
- `apis.spotify.show_album`
- `apis.spotify.show_playlist`

## Failure Handling
- If authentication fails, retry with stored credentials or notify the user.
- If any API call fails due to invalid data or network issues, skip the problematic item and log the error.
- If no items are found for a given media type, proceed with other types or return an appropriate message.

## Verification
- Confirm that all requested media types are processed correctly.
- Validate that the aggregation function is applied accurately to the collected data.
- Ensure the output includes both the aggregated result and the statistical summary.
