---
name: Sum utility bills for current year from file system
description: Reads bill files from a file-system directory, filters by the current calendar year using the phone's current date, parses each bill's total amount, and returns the sum via supervisor.complete_task. Generic across bill types (electricity, internet, cable).
---

## When to Use
Use when a user asks to calculate the total amount of bills (e.g., electricity, internet, cable) for the current calendar year, with bill files stored in a local file system directory.

## Preconditions
- Supervisor profile and account passwords are accessible via `apis.supervisor.show_profile()` and `apis.supervisor.show_account_passwords()`.
- The file_system app is available and credentials can be obtained from the supervisor.
- The current date/time can be retrieved via `apis.phone.get_current_date_and_time()`.

## Procedure
1. Get the current user's profile and the account passwords for `file_system`.
2. Log in to file_system: `token = apis.file_system.login(username=..., password=...)`.
3. Get the current year: `now = apis.phone.get_current_date_and_time()`; use `now.year`.
4. Form the directory path: `path = "~/bills/" + <bill_type>` where `<bill_type>` is the category from the instruction (electricity, internet, cable).
5. List files: `files = apis.file_system.show_directory(directory_path=path, access_token=token)`.
6. For each file:
   - Read content: `content = apis.file_system.show_file(file_path=file, access_token=token).content`.
   - Extract a year from the file name (e.g., `re.search(r"(20\\d{2})", file)`). If missing or not equal to current year, skip.
   - Extract the total amount from the content (e.g., `re.search(r"Total Amount\\s*=>?\\s*\\$(\\d+)", content)`). If found, add to total.
7. Call `apis.supervisor.complete_task(answer=total, status="success")` with the summed total.

## Relevant APIs / Tools
- `apis.supervisor.show_profile`
- `apis.supervisor.show_account_passwords`
- `apis.file_system.login`
- `apis.file_system.show_directory`
- `apis.file_system.show_file`
- `apis.phone.get_current_date_and_time`
- `apis.supervisor.complete_task`

## Failure Handling
- If login fails, verify credentials from `show_account_passwords`.
- If a file cannot be parsed (no year or no amount), skip it and continue.
- If the directory does not exist, check the exact path and try listing `~/bills/` to see available subdirectories.
- If the token expires, re-login and retry.

## Verification
- Confirm the answer is a numeric total.
- Ensure only files from the current year were included.
- Confirm that all files in the target directory were visited (or explicitly skipped).
