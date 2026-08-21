---
name: like_venmo_feed_transactions_for_contacts
description: Likes Venmo transactions from the user's social feed that involve contacts matching a specific relationship (e.g., roommates, siblings, coworkers) and fall within a specified time window (today, yesterday, or both).
---

## When to Use
Use this skill when the user asks to like/reaction Venmo transactions from their social feed involving people with a certain relationship, possibly filtered by a date range such as today, yesterday, or yesterday/today.

## Preconditions
- Supervisor access is available to fetch profile and account passwords.
- Phone and Venmo apps are accessible and credentials exist.
- The relationship and time window are explicitly stated or can be inferred.

## Procedure
1. **Fetch profile and credentials**
   - Call `apis.supervisor.show_profile()` to get the main user's identifier.
   - Call `apis.supervisor.show_account_passwords()` to retrieve login credentials for phone and Venmo.

2. **Login to phone**
   - Use `apis.phone.login(username=..., password=...)` to obtain the phone access token.

3. **Find contacts by relationship**
   - Call `apis.phone.search_contacts(access_token=..., query=relation, relationship=relation)` repeatedly with increasing `page_index` until an empty page is returned.
   - Collect the `email` field from all contacts found.

4. **Determine the target time window**
   - Use `apis.phone.get_current_date_and_time()` (or system date) to get today's date.
   - Compute `start` and `end` datetime boundaries:
     - `today`: start = today 00:00:00, end = today 23:59:59
     - `yesterday`: start = yesterday 00:00:00, end = yesterday 23:59:59
     - `yesterday or today`: start = yesterday 00:00:00, end = today 23:59:59

5. **Login to Venmo**
   - Use `apis.venmo.login(username=..., password=...)` to obtain the Venmo access token.

6. **Iterate over the social feed**
   - Call `apis.venmo.show_social_feed(access_token=..., page_index=...)` repeatedly until all pages are consumed.
   - For each feed entry (transaction):
     - Skip if `created_at` is not within the computed window.
     - Skip if neither `sender.email` nor `receiver.email` is in the collected contact emails.
     - Otherwise call `apis.venmo.like_transaction(transaction_id=entry.transaction_id, access_token=venmo_access_token)`.

7. **Complete the task**
   - Call `apis.supervisor.complete_task(status="success")` after all matching transactions have been liked.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.phone.login
- apis.phone.search_contacts
- apis.phone.get_current_date_and_time
- apis.venmo.login
- apis.venmo.show_social_feed
- apis.venmo.like_transaction
- apis.supervisor.complete_task

## Failure Handling
- If the search for contacts returns no results, verify the relationship spelling or try a broader query before giving up.
- If the social feed endpoint returns an empty page, stop pagination.
- If a transaction entry lacks sender/receiver email, skip it.
- If `like_transaction` fails due to already been liked, ignore the error and continue.

## Verification
- Count the number of like calls made and confirm they match the filtered transactions.
- Ensure no transaction outside the time window or involving non-matching contacts was liked.
- Confirm `supervisor.complete_task` is called once at the end.
