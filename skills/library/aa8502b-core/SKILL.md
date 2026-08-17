---
name: Manage Artist Follow Status Based on Liked Songs
description: This skill enables an agent to manage the follow status of artists based on a user's liked songs. It retrieves the list of currently followed artists and liked songs, then either follows or unfollows artists depending on the specified action and the overlap between liked and followed artists.
---

## When to Use
- When a user wants to synchronize their Spotify artist follows with their liked songs.
- When automating social media actions based on user preferences.

## Preconditions
- The agent has access to a valid Spotify account with appropriate permissions.
- The user has granted necessary scopes for reading followed artists and liked songs.

## Procedure
1. Obtain the Spotify access token for the user.
2. Retrieve the list of all artists the user is currently following using pagination.
3. Retrieve the list of all songs the user has liked using pagination.
4. Extract the artist IDs from the liked songs.
5. Based on the desired action ("Follow" or "Unfollow"), iterate through the relevant artist lists:
   - If action is "Follow": For each liked artist not already followed, initiate a follow request.
   - If action is "Unfollow": For each followed artist not in the liked list, initiate an unfollow request.
6. Report the outcome via a supervisor message.

## Relevant APIs / Tools
- `apis.spotify.access_token_from`
- `apis.spotify.show_following_artists`
- `apis.spotify.show_liked_songs`
- `apis.spotify.follow_artist`
- `apis.spotify.unfollow_artist`
- `apis.supervisor.message`

## Failure Handling
- If any API call fails, log the error and attempt to continue with remaining operations.
- If the access token is invalid or expired, re-authenticate the user before proceeding.

## Verification
- Confirm that the correct number of artists were followed or unfollowed.
- Ensure no duplicate or unnecessary API calls are made.
- Validate that the final state of followed artists matches the expected outcome based on the action and liked songs.
