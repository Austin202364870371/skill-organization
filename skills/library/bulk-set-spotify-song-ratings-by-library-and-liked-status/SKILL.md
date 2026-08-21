---
name: Bulk Set Spotify Song Ratings by Library and Liked Status
description: Set a target star rating for all songs in a user's Spotify library (playlists, albums, or saved songs) that satisfies a liked/unliked filter, creating or updating the user's song reviews.
---

## When to Use
Use when the task requires rating every song in a specified Spotify library (playlist collection, album library, or saved-song library) that is either liked or not liked by the user, and the desired rating is the same for all matching songs.

## Preconditions
- Must be logged in as the main user via supervisor profile/account passwords.
- Must have a valid Spotify access token.
- The library type and liked status filter are known from the task description.

## Procedure
1. Retrieve the main user's profile (`apis.supervisor.show_profile`) and account passwords (`apis.supervisor.show_account_passwords`).
2. Obtain a Spotify access token by calling `apis.spotify.login` with the retrieved username and password.
3. Fetch the appropriate library contents using pagination:
   - If library is playlists: call `apis.spotify.show_playlist_library` and collect all `song_ids` from each playlist into a set.
   - If library is album library: call `apis.spotify.show_album_library` and collect all `song_ids` from each album into a set.
   - If library is song library: call `apis.spotify.show_song_library` and collect the `song_id` of every song into a set.
4. Fetch all liked songs with `apis.spotify.show_liked_songs` and collect their `song_id`s into a set.
5. Compute the target song IDs:
   - If the filter is "liked": target = library_song_ids ∩ liked_song_ids.
   - If the filter is "not liked": target = library_song_ids - liked_song_ids.
6. For each song_id in the target set:
   - Fetch all pages of `apis.spotify.show_song_reviews` for that song using the main user's email.
   - If at least one review exists, call `apis.spotify.update_song_review` with the first review's `song_review_id` and the target rating.
   - If no review exists, call `apis.spotify.review_song` with the song_id and the target rating.
7. Mark the task complete using `apis.supervisor.complete_task(answer=None, status="success")`.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.spotify.login
- apis.spotify.show_playlist_library
- apis.spotify.show_album_library
- apis.spotify.show_song_library
- apis.spotify.show_liked_songs
- apis.spotify.show_song_reviews
- apis.spotify.review_song
- apis.spotify.update_song_review
- apis.supervisor.complete_task

## Failure Handling
- If login fails, re-check the profile and password from supervisor before retrying.
- If any library endpoint returns an empty list, stop pagination and proceed with the data collected.
- Use sets for song IDs to avoid duplicate writes when a song appears in multiple playlists/albums.

## Verification
- After processing, confirm that every song in the target set now has a review with the exact target rating, and that no non-target songs were changed.
