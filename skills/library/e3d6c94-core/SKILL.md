---
name: CreateFilteredPlaylistFromRecommendations
description: Create a new playlist and populate it with song recommendations that match specific criteria such as release year and genre.
---

## When to Use
- When tasked with generating a personalized playlist based on user's music preferences and filtering conditions.

## Preconditions
- Access to Spotify account credentials.
- User has provided criteria for filtering songs (e.g., year requirement, genre).
- User has specified a title for the new playlist.

## Procedure
1. Authenticate with Spotify using stored credentials to obtain an access token.
2. Fetch paginated lists of recommended songs.
3. For each recommendation, apply filters based on release date and genre.
4. Create a new playlist with the specified title.
5. Add filtered songs to the newly created playlist.

## Relevant APIs / Tools
- `spotify.login`
- `spotify.show_recommendations`
- `spotify.create_playlist`
- `spotify.add_song_to_playlist`
- `supervisor.show_account_passwords`
- `supervisor.show_profile`

## Failure Handling
- If authentication fails, retry with updated credentials or notify user.
- If no songs meet the filter criteria, inform the user and skip adding songs.
- If playlist creation fails, attempt to use an existing playlist or notify the user.

## Verification
- Confirm successful login and valid access token.
- Ensure all retrieved songs pass the filtering logic.
- Validate that the playlist was created and contains the expected songs.

## Notes
- The skill assumes that the user provides valid filtering criteria and a unique playlist title.
- The filtering logic should be robust enough to handle cases where detailed song metadata (e.g., genre) is not directly available in initial recommendations.
- Ensure that the final playlist includes only those songs that satisfy both the genre and release year requirements, as defined by the user.
