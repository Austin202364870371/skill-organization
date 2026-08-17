---
name: Manage Song Reviews Based on Library Content and Liked Status

description: This skill involves retrieving a user's music library content (playlists, albums, songs, or liked songs), filtering the content based on whether the songs are liked or not, and then either updating existing reviews or writing new reviews for those songs based on a target rating.
---

## When to Use
- When tasked with reviewing or re-reviewing songs from a user's Spotify library.
- When the task specifies a condition such as "review only liked songs" or "review only unliked songs".
- When the goal is to update or add ratings to specific songs in the user's collection.

## Preconditions
- The user has a valid Spotify account with access credentials.
- The agent can authenticate with Spotify to retrieve library data.
- There is a defined target rating to apply for reviews.
- The agent has access to the relevant API endpoints for managing song reviews.

## Procedure
1. Authenticate with Spotify using stored credentials to obtain an access token.
2. Retrieve the user's music library content (playlists, albums, songs, or liked songs) using pagination if needed.
3. Collect all song IDs from the retrieved library items.
4. If required, filter the song IDs based on the liked status (e.g., only liked songs or only unliked songs).
5. For each song ID in the filtered list:
   - Check if the user has already reviewed the song using the show_song_reviews API.
   - If a review exists, update the rating using the update_song_review API.
   - If no review exists, write a new review using the review_song API with the specified target rating.

## Relevant APIs / Tools
- `apis.spotify.access_token_from`
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_album_library`
- `apis.spotify.show_song_library`
- `apis.spotify.show_liked_songs`
- `apis.spotify.show_song_reviews`
- `apis.spotify.update_song_review`
- `apis.spotify.review_song`

## Failure Handling
- If authentication fails, retry with stored credentials or notify the user.
- If any API call returns an error, log the failure and attempt to continue processing other songs.
- If pagination fails, retry the page request or skip the remaining pages.

## Verification
- Confirm that all song IDs from the library were processed.
- Validate that each song received either a new review or updated review with the correct rating.
- Ensure no duplicate or orphaned reviews are created.
