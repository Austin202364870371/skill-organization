---
name: Aggregate Financial Data from Structured Files
description: When required to compute a cumulative financial value (e.g., total bills, expenses) by processing multiple structured data files in a specific directory.
---

## Skill: Aggregate Financial Data from Structured Files

### When to Use
When required to compute a cumulative financial value (e.g., total bills, expenses) by processing multiple structured data files in a specific directory.

### Preconditions
- Access to a file system with read permissions.
- Knowledge of the directory structure containing relevant financial files.
- Ability to authenticate and retrieve file contents.

### Procedure
1. Authenticate with the file system using valid credentials to obtain an access token.
2. List all files in the designated directory.
3. For each file:
   - Retrieve the file content.
   - Extract relevant data such as date and monetary amounts.
   - Filter out data that does not meet specified criteria (e.g., year mismatch).
   - Accumulate the monetary values into a running total.
4. Return the final aggregated total as the result.

### Relevant APIs / Tools
- `file_system.auth.token`
- `file_system.directory`
- `file_system.file`
- `supervisor.message`

### Failure Handling
- If authentication fails, retry with stored credentials or notify user.
- If a file cannot be read or parsed, skip it and log the error.
- If no matching files are found, return zero as the default total.

### Verification
- Confirm that all relevant files were processed.
- Validate that the extracted data matches expected formats (e.g., numeric values, correct date ranges).
- Ensure the final sum is mathematically consistent with the inputs.
