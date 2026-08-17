---
name: Aggregate and Process Multi-App Data for Payment Requests
description: Retrieve, parse, and aggregate data across multiple applications to identify users and amounts for generating payment requests.
---

## When to Use
- When tasked with creating payment requests based on scattered data across different apps.
- When required to cross-reference contact info, notes, and transaction histories.

## Preconditions
- Access credentials for phone, simple_note, and venmo applications are available.
- User has appropriate permissions to access data in all involved apps.
- System supports paginated API responses for data retrieval.

## Procedure
1. Authenticate with each app using stored credentials to obtain access tokens.
2. Search for relevant data such as contacts, notes, or transactions using filters like date ranges or keywords.
3. Paginate through search results to ensure all relevant items are retrieved.
4. Parse detailed information from identified entries (e.g., note content, transaction descriptions).
5. Map extracted data into a structured format (e.g., user_email_to_share mapping).
6. Cross-check existing transactions to avoid duplicate requests.
7. Create new payment requests using aggregated data for remaining users.

## Relevant APIs / Tools
- Authentication endpoints for phone (`/phone/auth/token`), simple_note (`/simple_note/auth/token`), and venmo (`/venmo/auth/token`).
- Search APIs for contacts (`/phone/contacts`), notes (`/simple_note/notes`), and transactions (`/venmo/transactions`).
- Detail retrieval APIs for notes (`/simple_note/notes/{id}`).
- Payment request creation API (`/venmo/payment_requests`).

## Failure Handling
- Retry authentication if access token fails.
- Skip incomplete or malformed entries during parsing.
- Log errors encountered during API calls for debugging.
- Implement timeout handling for slow paginated queries.
- Notify user if no matching data is found after retries.

## Verification
- Confirm successful authentication by verifying returned tokens.
- Validate that parsed data matches expected formats before use.
- Ensure all generated payment requests have valid email addresses and amounts.
- Check final output against original task requirements.
