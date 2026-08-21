---
name: compress_subdirectories_to_archives
description: Compress each subdirectory of a given parent directory into an archive file named after the subdirectory, then delete the original subdirectories. Suitable when a photo/vacation directory contains multiple subdirectories that need to be individually archived and removed.
---

## When to Use
Use when you need to archive each subdirectory inside a parent directory (e.g., vacation spots) into its own compressed file (e.g., .zip, .tar) and then delete the original subdirectories.

## Preconditions
- You have access to the `file_system` app.
- The parent directory is known and contains subdirectories that should be archived.
- The desired archive extension is known (e.g., `zip` or `tar`).

## Procedure
1. Retrieve the current user's profile and account passwords from the supervisor to obtain credentials for the file_system app.
2. Log in to the file_system app to get an access token.
3. List the subdirectories of the target parent directory using `show_directory` with `recursive=False`. This returns the paths of immediate subdirectories (and possibly files).
4. For each subdirectory path, extract the subdirectory name (the last path component).
5. Call `compress_directory` with:
   - `directory_path` = the subdirectory's full path
   - `compressed_file_path` = the parent directory path + subdirectory name + '.' + archive extension
   - `delete_directory` = True (removes the original subdirectory after successful compression)
   - `overwrite` = True (overwrites any existing archive with the same name)
6. Repeat for every subdirectory.
7. Call `supervisor.complete_task` with `status="success"` and appropriate answer (usually None or a summary).

## Relevant APIs / Tools
- `apis.supervisor.show_profile`
- `apis.supervisor.show_account_passwords`
- `apis.file_system.login`
- `apis.file_system.show_directory`
- `apis.file_system.compress_directory`
- `apis.supervisor.complete_task`

## Failure Handling
- If login fails, verify that the correct username/password is obtained from `show_profile` and `show_account_passwords`.
- If `show_directory` returns files as well as directories, filter to only entries that are directories (e.g., by checking whether the path ends without a file extension or using available metadata).
- If a subdirectory name contains characters that are problematic in filenames, sanitize it as needed while preserving the intended archive name.
- If compression fails for one subdirectory, continue with others and retry the failed one after diagnosing the error.

## Verification
- After each `compress_directory` call, confirm the archive exists and the source subdirectory no longer exists using `show_directory` on the parent directory.
- At the end, list the parent directory and verify that no subdirectories remain and that the expected archive files are present.
