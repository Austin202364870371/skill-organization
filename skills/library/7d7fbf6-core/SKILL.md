---
name: Compress and Clean Up Directory Structure
description: A reusable procedure for compressing subdirectories within a parent directory into archive files, then deleting the original directories. This skill enables efficient organization and cleanup of file structures by consolidating content into compressed formats.
---

## When to Use
- When multiple subdirectories need to be archived and cleaned up.
- When organizing large collections of files into compressed archives for storage or transfer.
- When preparing directories for migration or backup processes.

## Preconditions
- Access to the file system with appropriate permissions.
- Presence of a parent directory containing subdirectories to compress.
- Availability of authentication credentials for file system operations.

## Procedure
1. Obtain an access token for file system operations using user credentials.
2. List all subdirectories within the target directory.
3. For each subdirectory:
   a. Generate a compressed file path based on the subdirectory's name.
   b. Compress the subdirectory into the generated archive path.
   c. Delete the original subdirectory after successful compression.
4. Confirm completion of all operations.

## Relevant APIs / Tools
- `file_system.access_token_from` - To authenticate and obtain access token.
- `file_system.show_directory` - To list contents of a directory.
- `file_system.compress_directory` - To compress a directory into an archive.
- `supervisor.message` - To report status updates.

## Failure Handling
- If authentication fails, retry with updated credentials or notify user.
- If compression fails, log error and skip that directory, continue with others.
- If deletion fails, attempt manual cleanup or alert user.

## Verification
- Ensure that each subdirectory has been successfully compressed into an archive.
- Confirm that original subdirectories are deleted post-compression.
- Validate that the compressed files are accessible and correctly named.
