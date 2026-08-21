---
name: Handle edge cases in SimpleNote checklist updates
description: Covers situations where the primary workflow breaks: note not found, item already in desired state, multiple matching notes, alternate checkbox formats, and paginated search results.
---

## When to Use
Use when the primary update fails or when you need to robustly handle variations in how notes and checklist items are stored.

## Preconditions
- The primary workflow has been attempted or an edge case is suspected.
- Access to SimpleNote is available.

## Procedure
1. **Handle pagination**: Use `find_all_from_pages` or loop through `page_index` values when searching, because search results may be spread across multiple pages. Select the most relevant note by checking title/content.
2. **Verify note existence**: If search returns no notes, list all notes (using `search_notes` with an empty query) and look for a note with a matching title or content containing the target item.
3. **Handle multiple matches**: If more than one note matches, inspect each note's content to find the one containing the exact target item, or choose the note whose title most closely matches the user's description.
4. **Item already in desired state**: Before updating, check if the item's checkbox already has the desired marker. If so, skip the update or make no change, then still complete the task.
5. **Alternate checkbox formats**: Content may use `- [ ]`, `* [ ]`, or `[ ]` at line start. Use line-based processing or regular expressions to reliably replace the marker for the exact item, avoiding accidental replacements of similar text.
6. **Preserve formatting**: When replacing, only modify the marker and keep the rest of the line intact.

## Relevant APIs / Tools
- `apis.simple_note.login`
- `apis.simple_note.search_notes`
- `apis.simple_note.show_note`
- `apis.simple_note.update_note`
- `apis.supervisor.complete_task`

## Failure Handling
- If authentication expires, re-login to obtain a fresh token.
- If item text is partially matched, perform a stricter line match (e.g., `line.strip().endswith(item)`).
- If the item cannot be found at all, consider that the checklist might have been rephrased; search the note content and update the closest match.

## Verification
- After any update, show the note again and confirm the exact target line changed as expected.
- If no update was needed, still verify that the item already has the desired marker.
