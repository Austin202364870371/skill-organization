---
name: Robust Bill Split: Pagination, Receipt Selection, and Amount Parsing
description: Companion skill for the primary bill-splitting workflow. Handles edge cases such as paginated contact results, multiple or ambiguously named receipt files, non-standard amount formats in receipts, and verification that all Venmo requests were created.
---

## When to Use
Use this skill as a companion to the primary bill-splitting workflow when:
- The phone contact list has more roommates than a single page (requires pagination).
- The file system contains multiple bills or files with similar names (requires content-based selection).
- The receipt format varies (amount may appear with different labels or currency formatting).
- You need to verify that all Venmo requests were actually created.

## Preconditions
- Same as primary skill, but the data may be messier.

## Procedure
1. Paginate through all contacts until the result size is less than the page size (or use the AppWorld helper `find_all_from_pages`):
   ```python
   def all_roommates(apis, token):
       page = 0
       result = []
       while True:
           batch = apis.phone.search_contacts(
               access_token=token, query="roommate", relationship="roommate", page_index=page
           )
           result.extend(batch)
           if len(batch) < 20:  # page size
               return result
           page += 1
   ```
2. When listing files, do not rely solely on a substring; also filter for the previous month by inspecting file paths. If multiple names match, read all candidates and pick the one whose content contains the bill type.
3. Parse the total amount with a regex that handles optional currency symbols, commas, and different label formats:
   ```python
   import re
   match = re.search(r"Total (?:Amount|Bill)[^0-9]*\$?\s*([0-9,]+\.?\d*)", content)
   total = float(match.group(1).replace(",", ""))
   ```
4. Round the share to the nearest integer as required; if the instruction says to split equally, you may use `round(total / (len(emails) + 1))`.
5. After creating requests, collect the returned request objects. Verify that each has a request ID and the correct amount/email. If any request fails, retry or report the error.

## Relevant APIs / Tools
- apis.phone.search_contacts
- apis.file_system.show_directory
- apis.file_system.show_file
- apis.venmo.create_payment_request
- apis.supervisor.complete_task

## Failure Handling
- Empty contact pages: stop when an empty page is returned, do not loop forever.
- No clear "Total Amount" label: try regex patterns for "Total", "Balance", or "Amount Due".
- File selection: if the month string is missing from file names, compare the file modification date or choose the file with the most recent month present.
- Duplicate emails: deduplicate before sending requests.

## Verification
- Print or log each created request to confirm the count matches the number of unique roommate emails.
- Cross-check the sum of requested shares plus the payer's share equals the total from the receipt.
