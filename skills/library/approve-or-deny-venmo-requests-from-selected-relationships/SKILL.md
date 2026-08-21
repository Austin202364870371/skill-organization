---
name: Approve or Deny Venmo Requests from Selected Relationships
description: Resolve email addresses for the requested contact relationships, then approve or deny pending Venmo payment requests from those people.
---

## When to Use
Use when the user wants to accept or reject all pending Venmo payment requests from people in one or more contact relationships, such as friends, coworkers, or roommates.

## Preconditions
- The main user has Phone and Venmo accounts.
- The target relationship labels are stated in the instruction.
- The accept/reject action is stated in the instruction.

## Procedure
1. Retrieve the main user's profile with `apis.supervisor.show_profile()`.
2. Get a Phone access token using `apis.phone.access_token_from(main_user)`.
3. Build a set of target emails:
   - For each target relationship label, call `apis.phone.search_contacts(access_token=phone_token, query=<relationship>, relationship=<relationship>, page_index=...)`.
   - Paginate until the page is empty.
   - Add every returned contact's `email` to the set.
4. Get a Venmo access token using `apis.venmo.access_token_from(main_user)`.
5. Fetch all pending received payment requests:
   - `apis.venmo.show_received_payment_requests(access_token=venmo_token, status="pending", page_index=...)`.
   - Paginate until the page is empty.
6. For each pending request, check whether `request.sender.email` is in the target email set.
7. For each matching request, perform the requested action:
   - Accept: `apis.venmo.approve_payment_request(access_token=venmo_token, payment_request_id=request.payment_request_id)`
   - Reject: `apis.venmo.deny_payment_request(access_token=venmo_token, payment_request_id=request.payment_request_id)`
8. Call `apis.supervisor.complete_task(status="success")`.

## Relevant APIs / Tools
- `apis.supervisor.show_profile`
- `apis.phone.access_token_from`
- `apis.phone.search_contacts`
- `apis.venmo.access_token_from`
- `apis.venmo.show_received_payment_requests`
- `apis.venmo.approve_payment_request`
- `apis.venmo.deny_payment_request`
- `apis.supervisor.complete_task`

## Failure Handling
- If a relationship search returns no contacts, continue with other relationship labels.
- Ignore requests whose sender email is not in the target set.
- Only act on requests with `status="pending"`.
- If an action fails, retry once and continue with other requests.

## Verification
- After processing, re-list pending requests and verify that matching requests are no longer pending.
- Ensure no unrelated payment requests were changed.
