---
name: Rank Items by Metadata Criteria
description: Rank items (songs, artists, playlists) based on specified metadata attributes such as play count, release date, or popularity.
---

## When to Use
- When tasked with sorting or ranking items from a music library or recommendations based on metadata fields.
- When the user requests items ordered by criteria like play count, release date, or popularity.

## Preconditions
- Access to a music streaming service (e.g., Spotify) with relevant APIs enabled.
- Valid authentication credentials for the service.
- User specifies ranking criteria and metadata fields.

## Procedure
1. Authenticate with the music service using stored credentials.
2. Retrieve relevant items (songs, artists, playlists) based on the specified metadata criteria.
3. For each item, fetch detailed metadata including the requested fields.
4. Sort the items according to the specified ranking criteria (ascending/descending).
5. Return the ranked list of items.

## Relevant APIs / Tools
- `apis.spotify.access_token_from`
- `apis.spotify.show_song`
- `apis.spotify.search_songs`
- `apis.spotify.show_recommendations`
- `apis.spotify.show_artist`

## Failure Handling
- If authentication fails, retry with updated credentials or notify the user.
- If no items are retrieved, return an appropriate error message.
- If metadata cannot be fetched for an item, skip it and log the issue.
- If sorting fails due to invalid criteria, notify the user with a descriptive error.

## Verification
- Confirm that items are correctly retrieved and metadata is accurately fetched.
- Verify that the ranking order matches the specified criteria (e.g., most played, earliest release).
- Ensure the output list contains the expected number of ranked items.
