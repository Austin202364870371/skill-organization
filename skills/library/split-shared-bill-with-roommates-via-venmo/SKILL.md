---
name: Split Shared Bill with Roommates via Venmo
description: Use when the main user has paid a shared household bill and wants to request an equal share from each roommate via Venmo. The workflow reads the bill receipt from the file system, finds roommate emails in phone contacts, computes the per-person share, and sends Venmo payment requests.
---

## When to Use
Use this workflow when a user (the main user) has paid a household bill (e.g., electricity, internet, cable) and wants to request an equal share from each roommate using Venmo. The bill receipt is stored in the file system and roommate email addresses are in the phone contacts.

## Preconditions
- The supervisor profile and account passwords are accessible for the main user.
- Phone contacts contain entries with relationship "roommate".
- The file system contains the bill receipt with a recognizable file name/substring and a line like "Total Amount => $<amount>".
- Venmo account exists for the main user.

## Procedure
1. Retrieve the main user's profile and account passwords:
   ```python
   profile = apis.supervisor.show_profile()
   passwords = apis.supervisor.show_account_passwords()
   ```
2. Log in to the phone app and retrieve access token:
   ```python
   phone_token = apis.phone.login(password=..., username=...)['access_token']
   # or use apis.phone.access_token_from(main_user) if available
   ```
3. Search for all roommates using paginated contact search:
   ```python
   roommates = []
   page = 0
   while True:
       contacts = apis.phone.search_contacts(access_token=phone_token, query="roommate", relationship="roommate", page_index=page)
       roommates.extend(contacts)
       if len(contacts) < PAGE_SIZE: break
       page += 1
   roommate_emails = {c['email'] for c in roommates}
   ```
   (In AppWorld, `find_all_from_pages` handles this.)
4. Log in to file system and list candidate bill files:
   ```python
   fs_token = apis.file_system.login(password=..., username=...)['access_token']
   files = apis.file_system.show_directory(directory_path="~/", entry_type="files", substring=public_data.bill_type, access_token=fs_token)
   ```
5. Select the receipt file for the previous month by matching the month string in the file path:
   ```python
   import datetime
   last_month = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")
   file_path = next(f for f in files if last_month in f)
   content = apis.file_system.show_file(file_path=file_path, access_token=fs_token).content
   ```
6. Parse the total amount from the content:
   ```python
   total = float(content.split("Total Amount => $")[1].strip())
   ```
7. Compute each share:
   ```python
   share = round(total / (len(roommate_emails) + 1))
   ```
8. Log in to Venmo and send a request to each roommate:
   ```python
   venmo_token = apis.venmo.login(password=..., username=...)['access_token']
   for email in roommate_emails:
       apis.venmo.create_payment_request(access_token=venmo_token, user_email=email, amount=share, description=public_data.note)
   ```
9. Complete the task:
   ```python
   apis.supervisor.complete_task(answer=None, status="success")
   ```

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.phone.login
- apis.phone.search_contacts
- apis.file_system.login
- apis.file_system.show_directory
- apis.file_system.show_file
- apis.venmo.login
- apis.venmo.create_payment_request
- apis.supervisor.complete_task

## Failure Handling
- If no roommates are found, check that the contact query and relationship filter are correct; make sure pagination is handled.
- If no bill file matches, broaden the substring or inspect the directory listing.
- If the expected month string is not in the file name, try to find the most recent file by sorting or listing all files.
- If the amount cannot be parsed, search for alternative delimiters (e.g., "Total Amount: $").

## Verification
- Confirm that a successful Venmo request (with unique request id) is returned for every roommate email.
- Re-check the computed share by dividing the total by the number of people.
- Confirm that the task is marked complete with `supervisor.complete_task`.
