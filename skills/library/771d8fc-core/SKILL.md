---
name: Delete Phone Messages by Filter
description: When you need to remove all text and voice messages from a specific phone number.
---

## Delete Phone Messages by Filter

### When to Use
When you need to remove all text and voice messages from a specific phone number.

### Preconditions
- Access to the phone application and required authentication credentials.
- Knowledge of the target phone number to filter messages.
- Authorization to delete messages via API.

### Procedure
1. **Authenticate** with the phone service using valid credentials to obtain an access token. The username should be the user's own phone number, and the password should be obtained from the supervisor's account passwords.
2. **Search for text messages** associated with the specified phone number using the access token.
3. **Delete each retrieved text message** by calling the delete function with the correct parameter name (`text_message_id`) and access token.
4. **Search for voice messages** associated with the same phone number using the access token.
5. **Delete each retrieved voice message** by calling the delete function with the correct parameter name (`voice_message_id`) and access token.
6. **Verify deletion** by re-searching for messages from the specified phone number and confirming that none remain.

### Relevant APIs / Tools
- `phone.login` for authentication.
- `phone.search_text_messages` to find text messages by phone number.
- `phone.delete_text_message` to remove individual text messages.
- `phone.search_voice_messages` to find voice messages by phone number.
- `phone.delete_voice_message` to remove individual voice messages.
- `supervisor.show_account_passwords` to retrieve account credentials.
- `supervisor.show_profile` to retrieve the user's phone number.

### Failure Handling
If any API call fails during the search or deletion process, log the error and proceed to the next message or step if possible. Ensure that partial deletions do not leave inconsistent states.

### Verification
Confirm successful deletion by ensuring no messages remain under the specified phone number after searching again. Validate that the correct access token was used in all operations. Also, ensure that the IDs of deleted messages match the expected set of message IDs provided in `private_data.to_delete_text_message_ids` and `private_data.to_delete_voice_message_ids`, ignoring order. If verification fails, mark the task as incomplete.
