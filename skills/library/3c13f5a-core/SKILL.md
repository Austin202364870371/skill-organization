---
name: Process Shared Expenses with Contact and File Access
description: Retrieve contact information and financial data to calculate shared expenses and initiate payment requests.
---

## When to Use
- When required to distribute costs among multiple users based on shared resources or services.
- When needing to automate or assist with recurring bill payments or expense sharing.

## Preconditions
- User has valid credentials for phone, file system, and venmo applications.
- The user's contact list contains relevant parties (e.g., roommates).
- Financial documents exist in a specified directory that can be parsed for cost details.

## Procedure
1. Authenticate access tokens for phone, file system, and venmo using stored credentials.
2. Search the phone contact book to identify shared contacts such as roommates.
3. Navigate to the designated file system directory to locate relevant financial documents.
4. Read and parse the necessary financial document to extract total amounts.
5. Calculate individual share by dividing the total amount by the number of participants plus one.
6. For each identified contact, send a payment request via venmo using the calculated share amount.

## Relevant APIs / Tools
- apis.phone.search_contacts
- apis.file_system.show_directory
- apis.file_system.show_file
- apis.venmo.create_payment_request

## Failure Handling
- If authentication fails, retry with updated credentials or notify user.
- If no matching contacts are found, alert the user to check contact list.
- If files cannot be located or read, verify path or file permissions.

## Verification
- Confirm successful retrieval of access tokens before proceeding.
- Validate parsed financial data matches expected format.
- Ensure payment requests were sent successfully and record confirmation status.
