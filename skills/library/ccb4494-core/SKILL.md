---
name: Manage Spotify Playlist by Liking Previous Songs
description: Retrieve the current playing song and song queue from Spotify, identify previous songs in the queue, and like them using the Spotify API.
---

## When to Use
- When tasked with liking all previously played songs in the current Spotify playback queue.

## Preconditions
- The user has a valid Spotify account with active credentials.
- The Spotify app is accessible and integrated with the system.
- The user is currently playing music on Spotify.

## Procedure
1. Authenticate with Spotify using stored credentials to obtain an access token.
2. Fetch the currently playing song to determine the context of the queue.
3. Retrieve the full song queue from Spotify.
4. Identify and collect the IDs of all songs that appear before the currently playing song in the queue.
5. For each identified song ID, send a request to like the song using the Spotify API.

## Relevant APIs / Tools
- `apis.spotify.login`
- `apis.spotify.show_current_song`
- `apis.spotify.show_song_queue`
- `apis.spotify.like_song`

## Failure Handling
- If authentication fails, prompt for updated credentials or notify the user.
- If fetching the current song or queue fails, retry the operation or alert the user.
- If any individual like request fails, log the error and continue with other songs.

## Verification
- Confirm that the access token is valid before making API calls.
- Ensure that the current song is correctly identified and that the queue is retrieved.
- Validate that all prior songs in the queue were successfully liked.
