---
name: Update Note Content Based on Task Status
description: Update the content of a note by modifying checklist items based on whether a task is marked as done or not done.
---

## When to Use
- When a task involves updating a checklist within a note based on its completion status.

## Preconditions
- Access to the note-taking application.
- Valid authentication credentials for the note-taking service.
- The note contains a checklist with items that can be marked as done or not done.

## Procedure
1. Authenticate with the note-taking service to obtain an access token.
2. Search for the target note using a query term.
3. Retrieve the current content of the note.
4. Identify the specific checklist item to update.
5. If the task is marked as "done", replace "[ ] " with "[x] " in the relevant line.
6. If the task is marked as "not done", replace "[x] " with "[ ] " in the relevant line.
7. Save the updated note content back to the service.

## Relevant APIs / Tools
- `simple_note.access_token_from`
- `simple_note.search_notes`
- `simple_note.show_note`
- `simple_note.update_note`

## Failure Handling
- If authentication fails, retry with valid credentials or report the error.
- If the note is not found, notify the user and halt execution.
- If the note content cannot be updated, log the error and attempt recovery.

## Verification
- Confirm that the note content has been updated correctly by checking the presence of the appropriate checkbox markers.
---
