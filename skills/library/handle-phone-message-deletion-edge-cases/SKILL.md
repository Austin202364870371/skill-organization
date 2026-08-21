---
name: handle_phone_message_deletion_edge_cases
description: Handles pagination, empty results, and verification when deleting phone messages from a sender.
---

## When to Use
Use when the primary message-deletion flow needs to be robust: there may be multiple pages, no messages at all, or you need to verify that nothing remains.

## Preconditions
- You have already authenticated to the Phone app.
- The sender phone number is available as a variable.

## Procedure
1. Always paginate searches: call the search endpoint repeatedly with increasing `page_index` until an empty page is returned. Prefer a helper like `find_all_from_pages` when available.
2. Treat an empty result set as a successful no-op; do not attempt deletions.
3. When deleting, use the returned IDs only. If one ID fails, continue with the rest.
4. After deletion, run a final search for both text and voice messages from the sender to confirm the inbox is clean.
5. Only then call `apis.supervisor.complete_task` with status `success`.

## Relevant APIs / Tools
- apis.phone.search_text_messages
- apis.phone.search_voice_messages
- apis.phone.delete_text_message
- apis.phone.delete_voice_message
- apis.supervisor.complete_task

## Failure Handling
- If the search API returns an error, re-authenticate and retry.
- If a delete returns a not-found error, the message was likely already deleted; continue.
- If the final verification still shows messages, repeat the deletion loop.

## Verification
- Confirm that the last page of each search returns zero results.
