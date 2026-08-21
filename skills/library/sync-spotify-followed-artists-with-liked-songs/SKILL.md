---
name: sync_spotify_followed_artists_with_liked_songs
description: Follow or unfollow Spotify artists based on whether they have at least one liked song. Use this when the task asks to follow all artists from liked songs or unfollow all artists not in liked songs.
---

## When to Use
Use this skill when the user wants to reconcile their followed Spotify artists with the artists of their liked songs, either by:
- Following every artist who appears in at least one liked song, or
- Unfollowing every followed artist who does not appear in any liked song.

## Preconditions
- The user has a Spotify account and may have liked songs.
- You can access the supervisor profile and account passwords for the main user.

## Procedure
1. Retrieve the main user's profile and account passwords via `apis.supervisor.show_profile()` and `apis.supervisor.show_account_passwords()`.
2. Obtain a Spotify access token by calling `apis.spotify.login(username, password)` with the main user's credentials.
3. Fetch all followed artists using paginated calls to `apis.spotify.show_following_artists(access_token, page_index)`. Continue until an empty page is returned.
4. Fetch all liked songs using paginated calls to `apis.spotify.show_liked_songs(access_token, page_index)`. Continue until an empty page is returned.
5. Build the set of artist IDs from liked songs. Each song may have multiple artists, so iterate over `song.artists` and collect the `id` of each.
6. Build the set of currently followed artist IDs from the followed-artists list.
7. Based on the requested action:
   - If following: for every liked artist ID not already in the followed set, call `apis.spotify.follow_artist(access_token, artist_id)`.
   - If unfollowing: for every followed artist ID not in the liked-artist set, call `apis.spotify.unfollow_artist(access_token, artist_id)`.
8. After performing the changes, call `apis.supervisor.complete_task(answer=None, status="success")`.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.spotify.login
- apis.spotify.show_following_artists
- apis.spotify.show_liked_songs
- apis.spotify.follow_artist
- apis.spotify.unfollow_artist
- apis.supervisor.complete_task

## Failure Handling
- If `apis.spotify.login` fails, verify that the username and password are correctly retrieved from `apis.supervisor.show_account_passwords()`.
- If a paginated call returns an error, retry the same `page_index`; if errors persist, stop and report failure via `apis.supervisor.complete_task(status="failure")`.
- If the same artist appears multiple times, the set-based approach avoids redundant calls.

## Verification
- Optionally re-fetch the followed-artist list after changes and confirm that the target artists are now followed/unfollowed.
- For follow tasks, every artist of every liked song should appear in the followed list.
- For unfollow tasks, no followed artist should have an ID absent from the liked-song artist set.
