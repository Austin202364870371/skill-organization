---
name: "Temporal Filtering of Transactions"
description: "Filter financial or messaging data based on a specified time range to isolate relevant transactions or messages."
---

## When to Use
Use this skill when you need to isolate transactions or messages within a specific time range for analysis or action.

## Preconditions
- Access tokens are available for phone and venmo services.
- A valid time range is provided (start and end timestamps).
- A data source is specified (e.g., venmo transactions).

## Procedure
1. Authenticate with the phone service to access contact information.
2. Search the contact book to extract relevant email addresses.
3. Authenticate with the venmo service to access transaction data.
4. For each contact email:
   - Determine the start and end dates of the time range.
   - Fetch venmo transactions for the contact matching the time range.
5. Aggregate results across all contacts.

## Relevant APIs / Tools
- `phone.get_current_date_and_time`
- `phone.search_contacts`
- `venmo.show_transactions`

## Failure Handling
- If authentication fails, retry with updated credentials or report failure.
- If no transactions are found for a contact, continue processing other contacts.
- If API calls fail due to rate limits or timeouts, implement retry logic with exponential backoff.

## Verification
- Confirm that the retrieved transactions match the expected time range.
- Validate that all contacts were processed and the final result includes aggregated data as expected.
