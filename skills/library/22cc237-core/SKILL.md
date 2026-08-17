---
name: When to Use
description: - When tasked with generating payment requests based on data scattered across different apps. - When required to cross-reference contact information, notes, and transaction history.
---

SKILL:
---
name: Process and Aggregate Data from Multiple Apps to Generate Payment Requests
description: A procedure for retrieving, parsing, and aggregating data across multiple applications to identify users and amounts for payment requests.
---

## When to Use
- When tasked with generating payment requests based on data scattered across different apps.
- When required to cross-reference contact information, notes, and transaction history.

## Preconditions
- Access credentials for the relevant apps (e.g., phone, simple_note, venmo).
- User has appropriate permissions to access data in all involved apps.
- The system supports paginated API responses for data retrieval.

## Procedure
1. **Authenticate with each app**: Use stored credentials to log in to each application and obtain access tokens. Handle authentication failures gracefully.
2. **Search for relevant data**: Query contacts, notes, or transactions using filters like date ranges or keywords to find relevant entries.
3. **Paginate through results**: If necessary, iterate through multiple pages of search results to ensure all relevant items are retrieved.
4. **Parse detailed information**: Extract key fields from identified entries (e.g., note content, transaction descriptions).
5. **Map data into structured format**: Organize parsed data into a standardized structure (e.g., user_email_to_share mapping) for further processing.
6. **Cross-check existing transactions**: Compare against prior transaction records to prevent duplicate payment requests.
7. **Create payment requests**: For users without prior transactions, initiate new payment requests using the aggregated data.

## Relevant APIs / Tools
- Authentication endpoints for each app (e.g., `/phone/auth/token`, `/simple_note/auth/token`).
- Search APIs for contacts (`/phone/search_contacts`), notes (`/simple_note/search_notes`), and transactions (`/venmo/show_transactions`).
- Detail retrieval APIs for notes (`/simple_note/show_note`).
- Payment request creation API (`/venmo/payment_requests`).

## Failure Handling
- Retry authentication if access token fails.
- Skip incomplete or malformed entries during parsing.
- Log errors encountered during API calls for debugging.
- Implement timeout handling for slow paginated queries.

## Verification
- Confirm successful authentication by verifying returned tokens.
- Validate that parsed data matches expected formats before use.
- Ensure all generated payment requests have valid email addresses and amounts.
- Check final output against original task requirements.
