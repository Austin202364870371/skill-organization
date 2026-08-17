---
name: Authenticate and Follow Artists by Genre
description: Obtain authentication credentials, search for artists based on genre and follower count, and follow each artist programmatically.
---

## When to Use
- When required to automate the process of following artists on Spotify based on specific criteria such as genre and minimum follower count.

## Preconditions
- Access to valid Spotify account credentials (username and password).
- Availability of Spotify API endpoints for authentication, artist search, and following.
- Required permissions to perform actions like logging in and following artists.

## Procedure
1. Retrieve user profile and account passwords from supervisor services.
2. Use retrieved credentials to authenticate with Spotify's token endpoint.
3. Perform a search for artists matching a specified genre and minimum follower count.
4. Iterate through the list of artists returned from the search query.
5. For each artist found, use the access token to make a follow request via the Spotify API.
6. Report progress or completion status back to the supervisor.

## Relevant APIs / Tools
- `supervisor.profile` - To retrieve user information.
- `supervisor.account_passwords` - To fetch account credentials securely.
- `spotify.auth.token` - To generate an access token using username and password.
- `spotify.artists` - To search for artists based on filters including genre and follower count.
- `spotify.follow_artist` - To follow individual artists using their IDs and access token.
- `supervisor.message` - To send status updates during execution.

## Failure Handling
- If authentication fails due to invalid credentials, retry with updated credentials or alert the supervisor.
- If artist search returns no results, log and report accordingly.
- If any follow action fails (e.g., already followed), continue processing remaining artists.

## Verification
- Confirm successful retrieval of access token before proceeding with searches.
- Validate that all searched artists meet the required genre and follower count criteria.
- Ensure that each artist was successfully followed by checking responses from `follow_artist` calls.
- Notify supervisor upon completion or failure of the full sequence.
