---
name: SKILL.md
description: - When tasked with reviewing and acting on Venmo payment requests from specific contacts. - When needing to automate approval or rejection of payment requests based on predefined conditions.
---

# SKILL.md

---
name: Process Payment Requests from Contact Emails
description: Retrieve contact emails from a phone application and process Venmo payment requests from those contacts based on user-defined action (accept or reject).
---

## When to Use
- When tasked with reviewing and acting on Venmo payment requests from specific contacts.
- When needing to automate approval or rejection of payment requests based on predefined conditions.

## Preconditions
- Access to phone and Venmo applications with valid credentials.
- Presence of known contact relationships to search for in the phone app.
- Availability of pending payment requests in Venmo.

## Procedure
1. Authenticate with the phone application using `login` to retrieve an access token.
2. Search for contact emails associated with specified relationships in the phone app.
3. Authenticate with the Venmo application using `login` to retrieve an access token.
4. Retrieve all pending payment requests from Venmo.
5. Iterate through each received payment request.
6. Check if the requester's email matches any of the retrieved contact emails.
7. If the action is to accept, approve the payment request; otherwise, reject it.

## Relevant APIs / Tools
- `apis.phone.login`
- `apis.phone.show_contact_relationships`
- `apis.phone.search_contacts`
- `apis.venmo.login`
- `apis.venmo.show_received_payment_requests`
- `apis.venmo.approve_payment_request`
- `apis.venmo.deny_payment_request`

## Failure Handling
- If authentication fails, retry with stored credentials or notify the supervisor.
- If no matching emails are found, skip processing that request.
- If API calls fail due to network or server issues, retry up to three times before logging failure.

## Verification
- Confirm successful retrieval of contact emails and payment requests.
- Validate that accepted/rejected requests are updated correctly in Venmo.
- Ensure the supervisor is notified upon completion or failure.
