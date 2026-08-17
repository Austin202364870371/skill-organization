---
name: "Retrieve and Filter Financial Transactions by Contact and Time Range"
description: "Given a list of contacts and a time range, retrieve financial transactions (sent or received) for each contact within that range."
---

## When to Use
Use this skill when you need to analyze financial activity (e.g., Venmo transactions) for specific individuals over a defined period.

## Preconditions
- Access tokens are available for both phone and venmo services.
- A list of contact emails is provided.
- A time range is specified (typically starting from the first day of a given month in the current year).
- The direction of transactions (sent/received/all) is known.

## Procedure
1. Authenticate with the venmo service to access transaction data using login credentials.
2. For each contact email:
   - Determine the start date of the time range (first day of the specified month in the current year).
   - Fetch venmo transactions for the contact matching the direction and time range.
3. Aggregate results across all contacts.

## Relevant APIs / Tools
- `apis.venmo.login`
- `apis.venmo.show_transactions`

## Failure Handling
- If authentication fails, retry with updated credentials or report failure.
- If no transactions are found for a contact, continue processing other contacts.
- If API calls fail due to rate limits or timeouts, implement retry logic with exponential backoff.

## Verification
- Confirm that the retrieved transactions match the expected time range and contact.
- Validate that the correct transaction direction (sent/received) was applied.
- Ensure all contacts were processed and that the final result includes aggregated data as expected.
