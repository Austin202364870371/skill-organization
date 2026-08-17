---
name: Authenticate and Retrieve Contact Data for Transaction Processing
description: Obtain authentication tokens for phone and venmo services, retrieve contact information, and fetch transaction data for processing.
---

## When to Use
- When needing to perform actions on behalf of contacts within a messaging or payment platform.
- When required to process transactions based on contact relationships and transaction history.

## Preconditions
- Access credentials for both phone and venmo services are available.
- The user has permission to access contact data and perform transaction actions.

## Procedure
1. Retrieve account passwords from the supervisor to obtain necessary credentials.
2. Authenticate with the phone service using the username (phone number) and password to obtain an access token.
3. Authenticate with the venmo service using the username (email) and password to obtain an access token.
4. Fetch the list of friends from venmo to identify relevant contacts.
5. For each friend, retrieve transaction data within a specified date range.
6. Process the retrieved transactions by adding comments and liking them.

## Relevant APIs / Tools
- `apis.supervisor.show_account_passwords`
- `apis.phone.login`
- `apis.venmo.login`
- `apis.venmo.search_friends`
- `apis.venmo.show_transactions`
- `apis.venmo.create_transaction_comment`
- `apis.venmo.like_transaction`

## Failure Handling
- If authentication fails, retry with valid credentials or alert the user.
- If contact data retrieval fails, attempt pagination or re-authentication.
- If transaction fetching fails, validate date parameters and retry.

## Verification
- Confirm successful token acquisition for both services.
- Ensure that friend data is correctly retrieved and processed.
- Validate that transaction data is fetched according to specified criteria.
- Verify that comments and likes are properly added to transactions.
