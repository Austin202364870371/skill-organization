---
name: Handling Missing Contacts, Empty Results, and Partial Failures in Venmo Batch Actions
description: Handles edge cases in the primary workflow: no matching contacts, contacts with no transactions in the window, and individual like/comment failures. Includes retry logic and a verification pass to ensure all intended actions completed.
---

## When to Use
Use when the primary Venmo like/comment workflow may encounter empty results or partial failures, or when you need robust verification that every intended transaction was processed.

## Preconditions
- Same as primary, but you need to be extra careful about exception handling and idempotency.
- Know the expected comment text and the number of days to be able to verify.

## Procedure
1. Obtain phone and Venmo access tokens as in the primary skill.
2. Fetch the contact list. If empty, log a warning and complete the task with a note (no work to do).
3. For each contact, fetch received transactions with the correct cutoff. If empty, skip that contact.
4. For each transaction, attempt `like_transaction` and `create_transaction_comment` independently within `try/except` blocks. This prevents one failure from stopping the other action.
5. After processing all contacts, re-fetch the same transaction sets and check whether each transaction now has the comment and like. If any are missing, retry them once.
6. Call `apis.supervisor.complete_task` only after verification passes (or after best-effort retries).

## Relevant APIs / Tools
- apis.phone.search_contacts
- apis.venmo.show_transactions
- apis.venmo.like_transaction
- apis.venmo.create_transaction_comment
- apis.supervisor.complete_task

## Failure Handling
- Use `find_all_from_pages` to avoid missing paginated results.
- If a like fails because it was already liked, treat it as success.
- If a comment fails because it already exists, treat it as success.
- If an unexpected error occurs, record the transaction ID and continue with the remaining items.
- If verification shows missing actions, retry the specific transaction once; if it still fails, include it in the final report.

## Verification
- Count of transactions acted on equals the count of transactions found.
- Each re-fetched transaction has the requested comment and a `liked` flag of `True` (or the equivalent field).
