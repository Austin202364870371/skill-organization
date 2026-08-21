---
name: organize_files_by_date_into_category_folders
description: Moves all files in a directory into subfolders named after categories (e.g., vacation spots) based on the file creation month and year, preserving original filenames.
---

## When to Use
Use when a user asks to arrange/organize files in a directory by moving them into subfolders according to their creation date (e.g., month) and a provided mapping between dates and categories.

## Preconditions
- You have access to the `file_system` app credentials via the supervisor profile.
- The source directory exists and contains the files to organize.
- The destination subfolder names (category names) are provided in the task or in `public_data`.

## Procedure
1. Retrieve the current user's profile and account passwords from the supervisor to obtain file_system login credentials.
2. Log in to `file_system` and obtain an access token.
3. List the contents of the source directory using `apis.file_system.show_directory`.
4. For each file path returned:
   - Get file metadata with `apis.file_system.show_file` to read the `created_at` timestamp.
   - Extract the file name from the path (`path.split("/")[-1]`).
   - Determine the correct destination folder by comparing the creation month and year to the category mapping provided in the task (e.g., `public_data.month_1 <-> public_data.vacation_spot_1`, etc.). If a file does not match any specific month, use the default/remaining category.
   - Build the destination path as `f"{source_dir}/{category_folder}/{file_name}"`.
   - Call `apis.file_system.move_file` with the source and destination paths.
5. After all moves, call `apis.supervisor.complete_task(answer=None, status="success")`.

## Relevant APIs / Tools
- `apis.supervisor.show_profile`
- `apis.supervisor.show_account_passwords`
- `apis.file_system.login`
- `apis.file_system.show_directory`
- `apis.file_system.show_file`
- `apis.file_system.move_file`
- `apis.supervisor.complete_task`

## Failure Handling
- If login fails, verify the username/password from the supervisor profile.
- If a file cannot be moved (e.g., destination path already exists or invalid), skip it and report in the final status.
- If `public_data` keys are missing, fall back to parsing the task instruction for month-to-folder mappings.

## Verification
- After each move, the `move_file` call confirms success.
- Optionally re-list the source directory to confirm no files remain at the top level.
- Confirm all files now reside in their expected category subdirectory with unchanged names.
