---
name: Organize Files by Date into Category Folders
description: Move files from a source directory to category-specific subdirectories based on their creation dates. For each file, retrieve its creation date, determine the appropriate destination folder based on the month and year of the date, and move the file to that folder while preserving its original name.
---

## When to Use
- When you need to sort and organize files into categorized folders based on their metadata (specifically creation date).
- When files are stored in a single directory but should be grouped by time-based categories.

## Preconditions
- You have access to the file system and necessary credentials to authenticate.
- The source directory exists and contains files with accessible creation dates.
- Destination directories for each category exist or can be created.

## Procedure
1. Authenticate with the file system using the `login` API to obtain an access token.
2. List all files in the source directory.
3. For each file:
   a. Retrieve the file's creation date using the `show_file` API.
   b. Determine which category folder it belongs to based on the date (e.g., month and year).
   c. Construct the full destination path for the file in the appropriate category folder.
   d. Move the file from the source location to the destination folder using the `move_file` API, ensuring correct parameter names (`source_file_path`, `destination_file_path`) are used.

## Relevant APIs / Tools
- `file_system.login` – for authentication.
- `file_system.show_directory` – to list files in a directory.
- `file_system.show_file` – to get file metadata including creation date.
- `file_system.move_file` – to move files between directories.
- `file_system.create_directory` – to create category folders if needed.

## Failure Handling
- If authentication fails, retry with valid credentials or notify user.
- If a file’s metadata cannot be retrieved, skip the file and log the error.
- If moving a file fails due to permissions or invalid paths, report the failure and continue processing other files.

## Verification
- Confirm that the file has been moved from the source to the correct destination folder.
- Ensure that the file retains its original name.
- Validate that all expected files have been categorized correctly according to their dates.
- Verify that no directories were unintentionally deleted during the process.
