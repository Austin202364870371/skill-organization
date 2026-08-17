---
name: Join App-Specific Entities Using Shared Identifiers
description: Retrieve and combine data from multiple applications using shared identifiers to create a joined dataset or merged records.
---

## When to Use
- When combining information from different apps that share common identifiers (e.g., contact names, IDs).
- When generating a unified view of related data across applications.

## Preconditions
- Access credentials or authentication methods available for required apps.
- Required apps are installed and accessible.
- Data sources in each app contain searchable entities with shared identifiers.

## Procedure
1. Authenticate and retrieve access tokens for all source applications.
2. Search relevant data sources in each app using shared identifiers.
3. Extract and parse key fields from returned results.
4. Match entities based on shared identifiers.
5. Merge matched entities into a single dataset or record structure.

## Relevant APIs / Tools
- App authentication endpoints (e.g., `/phone/auth/token`, `/simple_note/auth/token`).
- Search functions (e.g., `search_contacts`, `search_notes`).
- Data retrieval functions (e.g., `show_note`).

## Failure Handling
- If authentication fails, retry with updated credentials or notify user.
- If no matching entities are found, log and return empty or partial results.
- If parsing fails, attempt alternative parsing strategies or report error.

## Verification
- Confirm that retrieved access tokens are valid before making further calls.
- Validate that searched data matches expected criteria.
- Ensure parsed data is correctly mapped and merged based on shared identifiers.
