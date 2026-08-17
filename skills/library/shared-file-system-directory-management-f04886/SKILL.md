---
name: Manage File System Directories
description: Reusable procedure for organizing and managing directories by moving, archiving, or deleting files based on properties like date or type.
---

## When to Use
- When you need to sort, compress, or clean up directories based on file attributes.
- When organizing large collections of files into structured layouts.

## Preconditions
- Access to the file system with appropriate permissions.
- Presence of source directories and target locations where applicable.
- Valid authentication credentials for file system and phone services.

## Procedure
1. Authenticate with the file system and/or phone service to obtain an access token.
2. Identify and list relevant files or directories based on input criteria (e.g., date, type).
3. Perform one of the following actions depending on task requirements:
   - Move files to categorized folders based on metadata (e.g., creation date).
   - Compress subdirectories into archives and delete originals.
   - Delete messages from a specific phone number.
4. Confirm successful completion of each operation.

## Relevant APIs / Tools
- `file_system.access_token_from`
- `file_system.move_file`
- `file_system.compress_directory`
- `phone.delete_text_message`
- `file_system.show_directory`
- `file_system.show_file`
- `phone.search_text_messages`
- `phone.search_voice_messages`

## Failure Handling
- If authentication fails, retry with updated credentials or notify user.
- If a file or directory cannot be accessed or manipulated, log the error and skip it.
- If a deletion or move operation fails due to permission issues, report failure and continue.
- In case of partial success during batch operations, ensure state consistency and notify user.

## Verification
- Verify that files were moved to correct destination folders.
- Confirm that directories were compressed and deleted appropriately.
- Validate that messages were successfully removed from the specified phone number.
- Ensure that all expected operations completed without leaving inconsistent states.
