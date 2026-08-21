---
name: Spotify Most/Least Played Song Lookup
description: Find the title of the most or least played song for a given artist on Spotify.
---

## When to Use
Use this skill when the user asks for the most or least played song by a specific artist, or phrases it as the top/bottom song by play count.

## Preconditions
- The user has provided an artist name and a ranking direction (most/least).
- Spotify app APIs are accessible via the `apis.spotify` namespace.

## Procedure
1. (Optional) Call `apis.supervisor.show_profile()` to confirm the user context if needed.
2. Search for the artist: `apis.spotify.search_artists(query=artist_name)`.
3. Take the first search result's `artist_id`.
4. Set the sort order:
   - For "most" played, use `sort_by="-play_count"`.
   - For "least" played, use `sort_by="+play_count"`.
5. Fetch songs with `apis.spotify.search_songs(artist_id=artist_id, sort_by=sort_by)`.
6. If the first page is empty, paginate using `page_index` until a song is found.
7. Extract the `title` of the first song.
8. Return the answer via `apis.supervisor.complete_task(answer=answer, status="success")`.

## Relevant APIs / Tools
- `apis.spotify.search_artists`
- `apis.spotify.search_songs`
- `apis.supervisor.complete_task`

## Failure Handling
- If no artist is found, try a more precise query or notify the user.
- If no song is returned, iterate subsequent pages.
- If sorting fails, verify that the `sort_by` value uses the correct sign convention ("+" for ascending, "-" for descending).

## Verification
- Confirm that the answer is a non-empty string taken from a song object.
- Ensure `complete_task` was called with `status="success"`.
