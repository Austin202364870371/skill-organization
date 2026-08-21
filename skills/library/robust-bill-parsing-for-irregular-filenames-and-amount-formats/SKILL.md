---
name: Robust bill parsing for irregular filenames and amount formats
description: Handles edge cases in bill aggregation: missing years in filenames, mixed bill types in one directory, currency amounts with commas/decimals, and files whose year appears only in the content. Provides fallback parsing and filtering strategies.
---

## When to Use
Use when bill files have inconsistent naming or content: filenames may not contain a year, amounts may include commas/decimals, or a single directory contains multiple bill types and you must filter by a specific category.

## Preconditions
- File system access is already authenticated.
- The directory listing and file content APIs return structured data with `.content` on the file object.

## Procedure
1. Retrieve the current year from `apis.phone.get_current_date_and_time()`.
2. List the directory (possibly the parent `~/bills/` if no subdirectory is specified).
3. For each file, read content.
4. Determine the bill year by trying in order:
   - A 4-digit year in the filename.
   - A 4-digit year in the file content (e.g., a billing period).
   - If neither is found, skip.
5. If the instruction specifies a bill type (electricity/internet/cable), filter files by checking that the path or content contains that type keyword.
6. Extract amount using a robust regex that handles currency symbols, commas, and decimal points:
   `re.search(r"(?:total\s*amount|amount\s*due)[^\d]*\$?\s*([\d,]+(?:\.\d+)?)", content, re.I)`
7. Strip commas and convert to float before summing.
8. Sum only current-year bills and call `apis.supervisor.complete_task(answer=total, status="success")`.

## Relevant APIs / Tools
- `apis.file_system.login`
- `apis.file_system.show_directory`
- `apis.file_system.show_file`
- `apis.phone.get_current_date_and_time`
- `apis.supervisor.complete_task`

## Failure Handling
- **No year found**: If neither filename nor content has a year, log the file path and continue.
- **No amount found**: If the expected amount pattern is absent, try the last numeric value in the content or search for "due", "payable", or "$".
- **Multiple bill types**: If the directory mixes types, require the type keyword in the filename or content; do not sum unrelated files.
- **Different date format**: Handle `MM-DD-YYYY` or `YYYYMMDD` by using appropriate regex fallbacks.

## Verification
- Re-run the sum with only the filtered files to confirm reproducibility.
- Verify that skipped files are genuinely not applicable (wrong year/type) and not due to parsing errors.
- Ensure the final answer is a number and the task is marked `status="success"` in `complete_task`.
