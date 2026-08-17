---
name: Cross-App Entity Resolution
description: Resolve entities (e.g., users, contacts) across different apps by comparing identifiers and merging relevant information.
---

## When to Use
- When resolving ambiguous or incomplete entity identifiers across multiple applications.
- When merging user profiles, contact details, or transaction records from disparate systems.

## Preconditions
- Access credentials or authentication methods available for required apps.
- Required apps are installed and accessible.
- Data sources such as contacts, transactions, or payment requests exist and are searchable.

## Procedure
1. Authenticate and retrieve access tokens for all required apps.
2. Search relevant data sources in each app using appropriate queries.
3. Extract and parse key identifiers (e.g., email, phone number) and related attributes from returned results.
4. Match entities across apps based on common identifiers.
5. Merge relevant information from matched entities into a unified representation.
6. Return resolved entities and merged data.

## Relevant APIs / Tools
- App authentication endpoints (e.g., `/phone/auth/token`, `/venmo/auth/token`).
- Search functions (e.g., `search_contacts`, `show_received_payment_requests`, `show_transactions`).

## Failure Handling
- If authentication fails, retry with updated credentials or notify user.
- If no matching identifiers are found between apps, log and return partial results or empty set.
- If parsing or merging fails, attempt alternative strategies or report error.

## Verification
- Confirm that retrieved access tokens are valid before making further calls.
- Validate that searched data matches expected criteria.
- Ensure parsed identifiers correctly map across apps.
- Verify that merged data maintains integrity and avoids duplication.
