---
name: Retrieve and Process Payment Information for Refund
description: Retrieve payment details from a third-party service, identify a specific transaction based on criteria such as recipient and status, extract relevant data like amount, and use that information to initiate a refund or return payment.
---

## When to Use
- When needing to process a refund or return payment to a user based on previously sent transactions.
- When required to locate a specific financial transaction in a system before initiating a new one.

## Preconditions
- Access credentials for both the contact management and payment services are available.
- The system has permission to access and retrieve data from these services.
- The target user's email or identifier is known.

## Procedure
1. Authenticate with the contact management service to obtain an access token.
2. Search for the target user’s contact information using their email or name.
3. Authenticate with the payment service using appropriate credentials.
4. Retrieve a list of sent payment requests, filtering by status and recipient if needed.
5. Identify the correct transaction (e.g., latest approved payment) and extract its amount.
6. Initiate a new payment or refund using the extracted amount and recipient details.
7. Add a descriptive note to the transaction for clarity.

## Relevant APIs / Tools
- `apis.phone.access_token_from`
- `apis.phone.search_contacts`
- `apis.venmo.access_token_from`
- `apis.venmo.show_sent_payment_requests`
- `apis.venmo.create_transaction`

## Failure Handling
- If authentication fails, retry with updated credentials or notify the user.
- If no matching transaction is found, verify the search criteria or alert the user.
- If transaction creation fails due to invalid data, validate inputs and retry or log error.

## Verification
- Confirm successful authentication with both services.
- Ensure the retrieved transaction matches expected criteria (recipient, status, etc.).
- Validate that the refund/payment was created successfully and contains correct details.
