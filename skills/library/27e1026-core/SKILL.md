---
name: Retrieve and Analyze Media Library Data
description: Collect and process media items (songs, albums, playlists) from a user's library to extract metadata such as release dates or addition timestamps, then determine the oldest or newest item based on that data.
---

## When to Use
- When tasked with finding the oldest or newest media item in a user's library.
- When required to analyze a collection of media items to derive temporal information.

## Preconditions
- User has granted access to the media library (e.g., Spotify).
- The system can authenticate and retrieve library data via API.

## Procedure
1. Authenticate with the media service using stored credentials.
2. Retrieve all media items from the user's library across songs, albums, and playlists using paginated requests.
3. For each item, fetch detailed metadata including release date or addition timestamp if not already available.
4. Store metadata in a structured format (e.g., dictionary mapping IDs to dates).
5. Identify the item with the earliest or latest date based on the request.
6. Fetch full details of the identified item to return relevant information.

## Relevant APIs / Tools
- Media library listing APIs (e.g., `show_song_library`, `show_album_library`, `show_playlist_library`).
- Detailed item retrieval APIs (e.g., `show_song`, `show_album`).
- Authentication APIs (e.g., `access_token_from`).
- Supervisor APIs for messaging and status updates.

## Failure Handling
- If authentication fails, retry with updated credentials or notify user.
- If API calls fail due to rate limits or network issues, implement retries with exponential backoff.
- If no items are found in the library, report empty result.

## Verification
- Confirm that all library items are retrieved through pagination.
- Validate that release dates or addition timestamps are correctly extracted and compared.
- Ensure the final item returned matches the requested oldest/newest criteria.

## Notes
- Some media items may not have release dates directly available in their initial library listing.
- In such cases, use appropriate APIs to fetch detailed metadata for each item to obtain the required information.
- Prioritize retrieving metadata that includes release dates or addition timestamps before performing comparisons.
- If multiple types of media exist (songs, albums), compare appropriately by the specified criteria (e.g., release date for albums, added_at for songs).
