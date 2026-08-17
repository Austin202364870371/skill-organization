---
name: Search for Artist and Sort Songs by Play Count
description: Search for an artist by name and then retrieve their songs sorted by play count in either ascending or descending order based on user request.
---

## When to Use
- When the user asks for the most or least played songs by a specific artist.

## Preconditions
- Access to Spotify API is available.
- User provides the artist's name and specifies whether they want the most or least played songs.

## Procedure
1. Use the Spotify API to search for the artist using the provided name.
2. Extract the artist ID from the first search result.
3. Determine the sort order based on user input: if "most", sort by `-play_count`; if "least", sort by `play_count`.
4. Query the Spotify API for songs by the artist ID, applying the determined sort order.
5. Return the title of the top song from the results.

## Relevant APIs / Tools
- `apis.spotify.search_artists`
- `apis.spotify.search_songs`

## Failure Handling
- If no artist is found, return an error message indicating that the artist could not be located.
- If no songs are returned for the artist, indicate that no songs were found.

## Verification
- Confirm that the artist name matches the search query.
- Validate that the sort order corresponds correctly to the user's request (most/least).
- Ensure the returned song title is from the correct artist and meets the specified criteria.
