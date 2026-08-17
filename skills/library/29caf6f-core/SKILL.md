---
name: Retrieve and Synthesize Information from Multiple Apps
description: Retrieve specific information from multiple applications by accessing tokens, searching data sources, parsing results, and synthesizing findings to generate a response.
---

## When to Use
- When a task requires gathering data from more than one application.
- When information needs to be extracted from structured or semi-structured sources like notes or messages.
- When a final output must be derived from combining data across different systems.

## Preconditions
- Access credentials or authentication methods available for required apps.
- Required apps are installed and accessible.
- Data sources such as contacts, messages, or notes exist and are searchable.

## Procedure
1. **Authenticate and retrieve access tokens** for all required apps using valid credentials.
2. **Search relevant data sources** in each app using appropriate queries.
3. **Extract and parse key information** from returned results.
4. **Combine or synthesize parsed data** to form a coherent output.
5. **Use the synthesized result** to perform an action (e.g., send a message).

## Relevant APIs / Tools
- App authentication endpoints (e.g., `/phone/auth/token`, `/simple_note/auth/token`).
- Search functions (e.g., `search_contacts`, `search_text_messages`, `search_notes`).
- Data retrieval functions (e.g., `show_note`).
- Action functions (e.g., `send_text_message`).

## Failure Handling
- If authentication fails, retry with updated credentials or notify user.
- If search returns no results, log and proceed with fallback logic if applicable.
- If parsing fails, attempt alternative parsing strategies or report error.

## Verification
- Confirm that retrieved access tokens are valid before making further calls.
- Validate that searched data matches expected criteria.
- Ensure parsed data is correctly mapped and formatted before use.

## Execution Notes
- Some apps may require additional steps to retrieve or authenticate, such as using supervisor tools or handling access restrictions.
- Always validate access tokens before calling protected APIs.
- If direct authentication is not possible, consider using pre-defined values or simulated responses where allowed by the environment.
- Ensure all actions performed align with the system’s behavior and constraints.

## Example Usage
1. Log into `simple_note` using credentials to retrieve an access token.
2. Search for notes containing a specific term.
3. Fetch detailed content of matching notes.
4. Parse relevant information from the note content.
5. Attempt to log into `phone` app if needed for sending messages.
6. Send a synthesized message using retrieved data.

## Updated Procedure Based on Feedback

1. **Authenticate and retrieve access tokens** for all required apps using valid credentials.
2. **Search relevant data sources** in each app using appropriate queries.
3. **Extract and parse key information** from returned results.
4. **Synthesize findings** into a unified output based on the task requirements.
5. **Validate and verify** the synthesized output against expected formats or content.
6. **Perform required actions**, such as completing a task or sending a message, using the synthesized data.

## Key Adjustments from Feedback
- Ensure that all necessary data is retrieved and synthesized accurately.
- Verify that actions like sending messages or modifying records are properly executed and tracked.
- Confirm that all assertions in the evaluation pass, particularly those involving data integrity and model changes.
