---
name: Venmo Transaction Totals for Contact Relationships
description: Aggregates the total amount of Venmo payments sent to, received from, or exchanged with contacts matching a given phone relationship since a specified date (e.g., the start of a month in the current year).
---

## When to Use
Use when a task asks "How much money have I sent/received to/from {relationship} on Venmo since {date}" or similar, requiring summing transaction amounts for a group of contacts.

## Preconditions
- You have access to the main user's profile and credentials.
- The phone and Venmo apps are logged in (or you can obtain access tokens).
- The current date/time is available to compute thresholds like "1st of this year".

## Procedure
1. Retrieve the main user's profile (`apis.supervisor.show_profile`) and account passwords (`apis.supervisor.show_account_passwords`) if needed for login.
2. Obtain a phone access token using `apis.phone.access_token_from(main_user)` (or via `apis.phone.login` with username/password).
3. Search the phone contacts for the target relationship (e.g., "roommates") using `apis.phone.search_contacts` with `query` and `relationship` set to the relationship term. Collect all pages with `find_all_from_pages`.
4. Extract contact email addresses from the results.
5. Obtain a Venmo access token using `apis.venmo.access_token_from(main_user)` (or `apis.venmo.login`).
6. Determine the threshold date (e.g., 1st of the specified month in the current year) using `apis.phone.get_current_date_and_time` or `DateTime.today()`.
7. For each contact email:
   - If direction is "sent", call `apis.venmo.show_transactions` with `direction="sent"` and `user_email=contact_email`, `min_created_at=threshold`.
   - If direction is "received", call with `direction="received"`.
   - If direction is "both" (sent or received), call without a `direction` filter (or with `direction=None`).
   - Aggregate all pages using `find_all_from_pages`.
8. Sum the `amount` field of all collected transactions (e.g., `sum_of(transactions, "amount")`).
9. Submit the total via `apis.supervisor.complete_task(answer=total, status="success")`.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.phone.access_token_from / apis.phone.login
- apis.phone.search_contacts
- apis.phone.get_current_date_and_time
- apis.venmo.access_token_from / apis.venmo.login
- apis.venmo.show_transactions
- apis.supervisor.complete_task

## Failure Handling
- If `search_contacts` returns no contacts for the relationship, the total is 0. Do not fail.
- If `show_transactions` returns no pages, treat sum as 0.
- Ensure `min_created_at` is formatted correctly; use the same date format as the API expects (typically `YYYY-MM-DD`).

## Verification
- Verify you used the correct relationship and direction.
- Check that you summed all pages and all contact emails.
- Confirm the threshold date is in the current year and correct month/day.
