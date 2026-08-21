---
name: Reply to text-message requests with movie recommendations from Simple Note
description: Handles incoming SMS requests for movie recommendations by looking up the requestor's message, extracting the requested director, finding the matching note in Simple Note, and sending a comma-separated list of movie titles back via text.
---

## When to Use
Use when a phone request asks for movie recommendations and the data lives in Simple Note, and you must reply via text message.

## Preconditions
- Supervisor profile and account passwords are accessible.
- The user has logged-in phone and simple_note apps.

## Procedure
1. Retrieve profile and credentials from supervisor.
2. Get phone access token using `apis.phone.access_token_from(main_user)` or by logging in with credentials.
3. Search contacts for the requestor's first name and get their phone number.
4. Search text messages from that phone number for a recommendation request (e.g., query containing "movie recommendation") and select the relevant message.
5. Parse the director name from the message text (e.g., text after "recommendations for a movie from").
6. Get simple_note access token.
7. Search notes for the movie recommendation note (e.g., query "movie recommendation") and fetch its content.
8. Parse the note content into a mapping from director to a list of movie titles. The note is typically structured as entries separated by blank lines; each entry has a title on the first line and " - director <name>" on the second.
9. Look up the requested director's titles.
10. Join titles with commas and send via `apis.phone.send_text_message` to the requestor's phone number.
11. Call `apis.supervisor.complete_task` with status "success".

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.phone.login
- apis.phone.search_contacts
- apis.phone.search_text_messages
- apis.phone.send_text_message
- apis.simple_note.login
- apis.simple_note.search_notes
- apis.simple_note.show_note
- apis.supervisor.complete_task

## Failure Handling
- If no contact is found, refine the query or consider the requestor may be known by another name.
- If no message is found, broaden the search query or check other phone numbers.
- If the director is not present in the note, notify the user or skip.

## Verification
- Confirm the text message was sent successfully.
- Verify the reply contains a comma-separated list of movie titles from the note's note for that director.
