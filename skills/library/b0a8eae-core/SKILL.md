---
name: Retrieve and Process User Data to Trigger External Actions
description: A core procedural skill for retrieving user data from one application, processing it to derive actionable information, and triggering actions in another application based on that information.
---

## When to Use
- When a task requires gathering and interpreting user-specific data from one service (e.g., notes, calendar) to make decisions.
- When the outcome depends on comparing data or performing calculations before executing an action in a different service (e.g., playing music).

## Preconditions
- Access tokens or authentication credentials for both source and target applications are available.
- Required APIs for reading data and performing actions are accessible.
- The user has granted necessary permissions for both services.

## Procedure
1. Authenticate and retrieve an access token for the source application.
2. Fetch relevant data items (e.g., notes, playlists) using search or listing APIs.
3. Identify and extract specific data points (e.g., workout duration, song durations).
4. Perform any required computations or comparisons (e.g., total playlist time vs. workout time).
5. If conditions are met, authenticate and trigger the desired action in the target application (e.g., play a playlist).

## Relevant APIs / Tools
- Authentication APIs for both apps (e.g., `simple_note.login`, `spotify.login`).
- Data retrieval APIs (e.g., `simple_note.search_notes`, `spotify.show_playlist_library`).
- Data parsing and computation logic.
- Action-triggering APIs (e.g., `spotify.play_music`).

## Failure Handling
- If authentication fails, retry with stored credentials or notify user.
- If data retrieval fails, log error and attempt fallback strategies (e.g., retry or skip).
- If computed condition is not satisfied, proceed without triggering the action.

## Verification
- Confirm successful authentication and access to both services.
- Validate that retrieved data matches expected format and content.
- Ensure that triggered action executes correctly (e.g., verify playback started).
