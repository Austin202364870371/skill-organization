---
name: Spotify Most/Least Recommended Artist Finder
description: Finds the artist that appears most (or least) often in the current user's Spotify recommendations by aggregating recommended songs and counting their artists.
---

## When to Use
Use when the task asks for the name of the artist most or least recommended to the current user on Spotify.

## Preconditions
- The current user profile is available via supervisor.
- Spotify credentials are accessible through supervisor account passwords.
- Spotify APIs are enabled.

## Procedure
1. Retrieve the current user's profile: `apis.supervisor.show_profile()`.
2. Fetch account credentials: `apis.supervisor.show_account_passwords()`.
3. Obtain a Spotify access token by logging in with the Spotify username/password from the credentials: `apis.spotify.login(username=..., password=...)` (or use `apis.spotify.access_token_from(main_user)` if available).
4. Fetch all Spotify recommendation pages using `apis.spotify.show_recommendations(access_token=..., page_index=...)` until an empty page is returned.
5. For each recommended song, call `apis.spotify.show_song(song_id=...)` and collect all artist IDs from the song's `artists` field.
6. Count how many times each artist ID appears across all recommendations.
7. Choose the artist with the maximum count for "most" or the minimum count for "least".
8. Resolve the artist ID to a name with `apis.spotify.show_artist(artist_id=...)`.
9. Call `apis.supervisor.complete_task(answer=artist_name, status="success")` with the resulting name.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.spotify.login
- apis.spotify.show_recommendations
- apis.spotify.show_song
- apis.spotify.show_artist
- apis.supervisor.complete_task

## Failure Handling
- If Spotify login fails, re-check the credentials from supervisor and retry once.
- If a recommendation page returns no items, stop pagination.
- If a song has no artist list, skip that song.
- If multiple artists tie, pick any one of them consistently (e.g., the first encountered).
- If the request is neither "most" nor "least", default to "most".

## Verification
- Confirm all recommendation pages were processed.
- Confirm every song returned at least one artist where expected.
- Confirm the chosen artist name matches the selected artist ID.
- Confirm `complete_task` was called with status "success" and the final answer string.
