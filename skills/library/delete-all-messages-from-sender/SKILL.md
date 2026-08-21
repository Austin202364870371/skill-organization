---
name: delete_all_messages_from_sender
description: Deletes every text and voice message in the Phone app received from a specified phone number.
---

## When to Use
Use when the instruction says to delete all phone text messages and/or voice messages from a particular phone number (spam or otherwise).

## Preconditions
- You have access to the supervisor profile and account passwords to obtain the phone account credentials.
- You know the sender phone number to filter by.

## Procedure
1. Retrieve the current user's profile and account passwords from the supervisor to get the phone account credentials.
2. Obtain a Phone access token by logging in with those credentials (`apis.phone.login`).
3. Search text messages from the target sender, iterating through all pages until no more results (`apis.phone.search_text_messages`).
4. Delete each returned text message by its ID (`apis.phone.delete_text_message`).
5. Search voice messages from the same sender, iterating through all pages (`apis.phone.search_voice_messages`).
6. Delete each returned voice message by its ID (`apis.phone.delete_voice_message`).
7. Mark the task complete with `apis.supervisor.complete_task(answer=None, status="success")`.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.phone.login
- apis.phone.search_text_messages
- apis.phone.delete_text_message
- apis.phone.search_voice_messages
- apis.phone.delete_voice_message
- apis.supervisor.complete_task

## Failure Handling
- If login fails, confirm you are using the password for the main user's phone account.
- If a message was already deleted, skip or ignore deletion errors.

## Verification
- Re-run searches for the sender number and confirm both text and voice message lists are empty.
