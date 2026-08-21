---
name: Handling ambiguous, missing, or malformed movie recommendation data
description: Covers edge cases in the movie recommendation reply workflow: pagination, ambiguous matches, missing contacts/messages/notes, and non-standard note formatting.
---

## When to Use
Use when the primary workflow encounters ambiguity, missing data, or non-standard formatting in the request or note.

## Preconditions
- Same as primary; you are already in the skills execution context.

## Procedure
1. Use the generic finder `find_one_from_pages` to handle pagination for contacts, messages, and notes. If multiple matches exist, select the one that best matches the request (e.g., by exact name or recency).
2. When parsing the director, handle multiple possible phrasings: search for tokens like "from", "director", "movie", etc., and fall back to regex extraction.
3. When parsing the note, handle missing " - director" prefixes by attempting to infer the director from the message context or skip that entry.
4. If the requested director has no movies in the note, send a polite fallback text (e.g., "No recommendations found") or complete without sending.
5. If sending fails, retry once, then report an error.

## Relevant APIs / Tools
- `apis.phone.search_contacts`
- `apis.phone.search_text_messages`
- `apis.phone.send_text_message`
- `apis.simple_note.search_notes`
- `apis.simple_note.show_note`
- `apis.supervisor.complete_task`

## Failure Handling
- Contact not found: try searching with last name or full name.
- Message not found: query `phone.search_text_messages` with different keywords (e.g., "recommendation", "suggestion", "movie").
- Note not found: try alternate queries, or check pinned notes with `dont_reorder_pinned=True`.
- Note content unparseable: split by blank lines; if entries have more/fewer lines, still use line 0 as title and search line 1 for the director substring.

## Verification
- Ensure you did not send an empty reply.
- Verify the sent reply is well-formed and derived only from the Simple Note data.
