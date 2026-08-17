---
name: Iterate and Process Playlists or Artists
description: Iteratively process a list of playlists or artists, applying consistent actions such as following, reviewing, or filtering based on defined criteria.
---

## When to Use
- When required to apply uniform operations across multiple playlists or artists.
- When automating tasks like following artists based on genre or managing follow status based on user preferences.

## Preconditions
- Valid Spotify account credentials are available.
- The agent can authenticate with Spotify using stored credentials.
- Input list contains valid playlist or artist identifiers.
- Processing rules are clearly defined.

## Procedure
1. Authenticate with Spotify to obtain an access token.
2. Iterate over the input list of playlists or artists.
3. For each item, apply the defined processing rule (e.g., fetch details, check criteria, perform action).
4. Log each step of the operation for tracking and debugging purposes.
5. Return processed entities and action logs upon completion.

## Relevant APIs / Tools
- `spotify.show_playlist`
- `spotify.show_following_artists`
- `spotify.follow_artist`
- `spotify.show_playlist_library`
- `spotify.show_song`
- `supervisor.message`

## Failure Handling
- If authentication fails, retry with stored credentials; if unsuccessful, notify the user.
- If a playlist or artist cannot be accessed due to permissions or errors, skip it and log the incident.
- If an action fails (e.g., follow/unfollow), continue with other items and record the failure.

## Verification
- Confirm that the access token is valid before initiating any API calls.
- Ensure all items in the input list are processed without omission.
- Validate that actions applied match the intended processing rules.
- Deliver a complete action log and list of processed entities upon completion.
