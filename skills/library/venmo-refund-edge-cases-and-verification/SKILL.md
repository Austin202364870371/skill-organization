---
name: venmo_refund_edge_cases_and_verification
description: Handle edge cases and verify refunds when refunding approved Venmo payment requests: missing contacts, non-approved statuses, multiple requests, or failed transactions.
---

## When to Use
Use when the standard refund workflow (see primary skill) does not complete cleanly, or when you need to verify the refund was created correctly.

## Preconditions
- The user is authenticated with Phone and Venmo apps.
- You have access to the user's account passwords from Supervisor.

## Procedure
1. **Contact not found by first name**: Search phone contacts using the full name or last name as the query. If a unique contact is still not found, look for the recipient's email in the Venmo payment request itself (`receiver.email`) if the request object provides it.
2. **No approved request found**: Call `apis.venmo.show_sent_payment_requests` without the `status` parameter or with `status='pending'` to see if the request is still awaiting approval. If the user says it is approved, check that you are looking at *sent* requests.
3. **Multiple matching requests**: Filter all approved requests for the recipient email and select the one with the most recent creation timestamp. The request object usually contains a `created_at` field; if not, select the one with the largest `id`.
4. **Transaction creation fails**: If `apis.venmo.create_transaction` returns an error, check the user's Venmo balance and the receiver's email validity. Retry once after fixing any issues.
5. **Confirm the refund**: After a successful `create_transaction` call, optionally list sent transactions (if available) to verify the new entry, or rely on the success response. Then call `apis.supervisor.complete_task`.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.phone.login
- apis.phone.search_contacts
- apis.venmo.login
- apis.venmo.show_sent_payment_requests
- apis.venmo.create_transaction
- apis.supervisor.complete_task

## Failure Handling
- If the recipient email cannot be determined, abort and do not create a transaction.
- If multiple payment requests exist with the same amount, pick the latest to match the phrase "last payment request".
- If the Venmo request status is not exactly "approved", try "completed" or check available statuses.

## Verification
- The refund amount equals the original request amount.
- The receiver email matches the contact.
- The task is marked successful only after the refund transaction is recorded.
