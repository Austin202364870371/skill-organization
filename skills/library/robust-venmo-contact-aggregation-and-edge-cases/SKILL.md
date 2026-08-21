---
name: Robust Venmo Contact Aggregation and Edge Cases
description: Handles edge cases when aggregating Venmo transactions for phone contacts: direction semantics, empty results, date computation, pagination, and safe task completion.
---

## When to Use
Use as a companion to the primary skill when the task involves nuances like "sent or received", missing contacts, or requiring the threshold to be derived from the current date.

## Preconditions
- Primary workflow is understood.
- API pagination helpers (`find_all_from_pages`) are available.
- Date utilities (`DateTime`) are available.

## Procedure
1. Always determine the current date using `phone.get_current_date_and_time` before computing thresholds.
2. Convert month names to numbers if the task gives a month abbreviation ("Jan" -> 1, etc.).
3. Build the threshold date as the first day of that month in the current year.
4. For "sent or received", do not pass a `direction` parameter; the API returns both directions. Do not accidentally filter by only one direction.
5. When paginating, always use `find_all_from_pages` to collect all pages; the API returns paged results.
6. If no contacts match the relationship, complete the task with `0` and status `"success"` rather than erroring out.
7. If a particular contact has no transactions, the sum for that contact is 0; continue with other contacts.

## Relevant APIs / Tools
- apis.phone.get_current_date_and_time
- apis.phone.search_contacts
- apis.venmo.show_transactions
- apis.supervisor.complete_task

## Failure Handling
- Invalid date format: use `DateTime` to format as `YYYY-MM-DD`.
- Missing contact emails: skip contacts that lack an email.
- API errors: retry once, then complete with status "failure" if the task cannot be answered.

## Verification
- Compare the sum against a manual sample of transactions.
- Ensure both sent and received amounts are included only when requested.
- Verify the date cutoff is inclusive (transactions on or after the threshold).
