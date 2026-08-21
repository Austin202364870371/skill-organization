---
name: Create Spotify Playlist from Recommended Songs by Genre and Release Year
description: Build a Spotify playlist from the user's recommended songs, filtered by genre and a release-year criterion (this year or this/last year). Covers login, fetching recommendations and song details, filtering, creating the playlist, adding songs, and completing the task.
---

## When to Use
Use when you need to create a new Spotify playlist containing songs from the user's Spotify recommendations that match a specified genre and a release-year criterion such as "this year" or "this or last year".

## Preconditions
- The user has a Spotify account and valid credentials stored in the supervisor account passwords.
- You can access the supervisor profile and account passwords.
- The current date/time is available for computing year boundaries.

## Procedure
1. Retrieve the current user profile with `apis.supervisor.show_profile()`.
2. Retrieve the stored account passwords with `apis.supervisor.show_account_passwords()` and extract the Spotify credentials.
3. Log in to Spotify using `apis.spotify.login(username=..., password=...)` to obtain an access token.
4. Fetch all Spotify recommendations by repeatedly calling `apis.spotify.show_recommendations(access_token=..., page_index=...)` until an empty page is returned.
5. For each recommendation, fetch detailed song information with `apis.spotify.show_song(song_id=...)`.
6. Determine the threshold date:
   - For "this year" -> start of the current year (Jan 1 00:00).
   - For "this or last year" -> start of the previous year.
   Use `apis.phone.get_current_date_and_time()` (or the environment's date/time) to get today's date.
7. Filter the recommended songs by exact genre match and `release_date >= threshold_date`.
8. Create a new playlist with `apis.spotify.create_playlist(access_token=..., title=...)`.
9. Add each filtered song using `apis.spotify.add_song_to_playlist(access_token=..., playlist_id=..., song_id=...)`.
10. Mark the task complete with `apis.supervisor.complete_task(answer=None, status="success")`.

## Relevant APIs / Tools
- `apis.supervisor.show_profile`
- `apis.supervisor.show_account_passwords`
- `apis.phone.get_current_date_and_time`
- `apis.spotify.login`
- `apis.spotify.show_recommendations`
- `apis.spotify.show_song`
- `apis.spotify.create_playlist`
- `apis.spotify.add_song_to_playlist`
- `apis.supervisor.complete_task`

## Failure Handling
- If login fails, verify the credentials from the account passwords store.
- If a recommendation page is empty, stop pagination.
- If a song's genre is missing, skip it (or treat as no match).
- If no songs match, still create the playlist (possibly empty) and complete the task successfully.

## Verification
- Confirm the new playlist exists and contains exactly the songs matching the genre and release-date criterion.
- Ensure the playlist is created with the intended title and all filtered songs are added.
