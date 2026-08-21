---
name: Handle pagination, deduplication, and edge cases in Spotify library song analysis
description: Complements the primary skill by covering full pagination, deduplication of song IDs from playlists/albums, handling of missing metric values, and robust verification of the extreme-value result.
---

## When to Use
Use this secondary skill together with the primary when the data is large, spread across multiple pages, contains duplicate songs (e.g., a song in several playlists or albums), or when the metric values might be missing or zero.

## Preconditions
- Same authentication as in the primary skill.
- The library source is already identified.

## Procedure
1. Implement a complete pagination loop: start with `page_index = 0`, call the appropriate library endpoint, collect items, increment page index, and continue until an empty page is returned.
2. For playlists and albums, flatten the `song_ids` from each container into a single set to automatically remove duplicates.
3. For saved‑song libraries, collect all `song_id` values into a set as well.
4. When fetching song details, skip or retry any song that raises an error; do not let a single failure stop the entire process.
5. When comparing metric values, treat missing values as 0 or skip that song; be consistent.
6. If the library yields no songs, return a clear message via `apis.supervisor.complete_task` that no songs exist.
7. If several songs share the same extreme value, select the first one encountered; this is usually acceptable.

## Relevant APIs / Tools
- `apis.spotify.show_playlist_library`
- `apis.spotify.show_album_library`
- `apis.spotify.show_song_library`
- `apis.spotify.show_song`
- `apis.supervisor.complete_task`

## Failure Handling
- **Pagination overrun**: if the API does not indicate a next page, stop when the number of items in a page is less than the expected page size or zero.
- **Duplicate songs**: always use a set when collecting IDs.
- **Missing song details**: log the failure, continue with other songs, and if the final result is affected, consider re-fetching the failed ID.
- **Tie-breaking**: if the instruction does not specify, any tied song is acceptable; document the chosen one in your reasoning.

## Verification
- Log the number of pages and the total distinct song IDs fetched; verify they match.
- After selecting the extreme song, sort all songs by the metric in the appropriate order and confirm the selected song is at the boundary.
- If the result seems surprising, re-read the instruction to ensure the correct library type and metric were used.
- Always call `apis.supervisor.complete_task` exactly once with the final answer.
