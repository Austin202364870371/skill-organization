---
name: Handle Spotify Artist Search Pagination and Follow Errors
description: Deal with pagination, duplicate filtering, and non-fatal follow failures when bulk-following artists on Spotify.
---

## When to Use
Use this skill when the primary follow workflow faces edge cases such as multiple pages, duplicate artists, artists already followed, or failed follow requests.

## Preconditions
- The primary search/follow workflow has been started or is being planned.
- You have a valid Spotify access token.

## Procedure
1. Always loop through search result pages using `page_index`. Stop when a page returns fewer results than expected or an empty page, whichever the API indicates.
2. Deduplicate artists by `artist_id` to avoid following the same artist twice across pages.
3. Filter by genre after pagination, not only by query string, because the query may match unrelated artists.
4. Use `raise_on_failure=False` in `follow_artist` so that a single failure (e.g., already followed) does not crash the whole task.
5. Optionally, collect any failed artist IDs and retry them once.
6. Always complete the task even if some individual follows failed, as long as the workflow proceeded.

## Relevant APIs / Tools
- `apis.spotify.search_artists`
- `apis.spotify.follow_artist`
- `apis.supervisor.message`
- `apis.supervisor.complete_task`

## Failure Handling
- If `search_artists` raises an error, retry with a small backoff before giving up.
- If `follow_artist` fails, log the artist ID and continue. Do not re-raise unless every single follow fails.
- If the task is impossible (e.g., no valid credentials), call `complete_task` with a failure status.

## Verification
- Confirm that the total number of followed artists equals the number of unique qualifying artists found.
- Ensure the final completion call is made regardless of minor per-artist failures.
