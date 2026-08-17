---
name: Extract and Transform Media Metadata
description: Retrieve metadata from media items (songs, albums, playlists) and transform it into a standardized format based on defined transformation rules.
---

## When to Use
- When extracting metadata from media items for downstream processing or enrichment.
- When transforming raw metadata into a consistent structure for analysis or export.

## Preconditions
- User has granted access to the media service (e.g., Spotify).
- System can authenticate and retrieve media data via API.
- Transformation rules are provided and valid.

## Procedure
1. Authenticate with the media service using stored credentials.
2. Retrieve all media items (songs, albums, playlists) from the user's library using paginated requests.
3. For each item, fetch detailed metadata if not already available.
4. Apply transformation rules to enrich or standardize the metadata.
5. Compile transformed metadata into a structured output format.

## Relevant APIs / Tools
- Media library listing APIs (e.g., `show_song_library`, `show_album_library`, `show_playlist_library`).
- Detailed item retrieval APIs (e.g., `show_song`, `show_album`, `show_playlist`).
- Authentication APIs (e.g., `access_token_from`).

## Failure Handling
- If authentication fails, retry with updated credentials or notify user.
- If API calls fail due to rate limits or network issues, implement retries with exponential backoff.
- If metadata cannot be retrieved for an item, skip it and log the failure.
- If transformation rules are invalid, return an error indicating rule misconfiguration.

## Verification
- Confirm that all items are retrieved and processed through pagination.
- Validate that metadata transformations match the specified rules.
- Ensure the final output contains correctly transformed and standardized metadata.
