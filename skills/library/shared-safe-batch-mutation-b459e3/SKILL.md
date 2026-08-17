---
name: Safe Batch Mutation
description: Perform bulk operations (add, update, delete) on data items safely with error handling and rollback capability.
---

## When to Use
- When executing multiple data mutations that must succeed or fail as a unit.
- When managing large-scale updates to media libraries or playlists with potential for partial failures.

## Preconditions
- Valid authentication credentials for the target service (e.g., Spotify).
- Access to relevant APIs for performing add, update, or delete operations.
- Input batch operation commands and associated item identifiers.

## Procedure
1. Authenticate with the target service using stored credentials.
2. Validate input batch operation commands and item identifiers.
3. Execute each mutation in sequence while tracking success and failure.
4. On encountering a failure, attempt rollback of previously successful mutations.
5. Collect and return mutation results and error logs.

## Relevant APIs / Tools
- `apis.spotify.access_token_from`
- `spotify.remove_song_from_library`
- `spotify.remove_song_from_playlist`
- `spotify.like_song`

## Failure Handling
- If authentication fails, retry with stored credentials or notify the user.
- If a mutation fails, log the error and attempt to rollback prior changes.
- If a rollback itself fails, record the failure and continue processing remaining items.

## Verification
- Confirm that all mutations are executed according to input commands.
- Verify that rollback occurs correctly when a failure is encountered.
- Ensure returned results accurately reflect the status of each operation and any errors.
