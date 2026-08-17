---
name: Iterate Through Paginated API Results and Apply Conditional Logic
description: A core procedural skill for systematically iterating through paginated API responses, applying date/time and content-based filters, and performing actions on matching items.
---

## When to Use
- When working with APIs that return large datasets in paginated form.
- When filtering results based on temporal criteria (e.g., today, yesterday).
- When needing to perform actions (e.g., liking, posting) on specific entries that meet certain conditions.

## Preconditions
- Access to valid authentication tokens for relevant services.
- Knowledge of the API structure and pagination parameters.
- Defined criteria for filtering results (e.g., time range, participant list).

## Procedure
1. Authenticate and obtain necessary access tokens.
2. Initiate the first page of a paginated API call.
3. Iterate through each page of results until all pages are processed.
4. For each item in the result set, evaluate whether it meets specified conditions (e.g., time range, participant inclusion).
5. If conditions are met, execute the required action (e.g., like, post, update).
6. Continue to next page until no more data is available.

## Relevant APIs / Tools
- `GET /{service}/social_feed` or similar paginated endpoints.
- `POST /{service}/transactions/{id}/likes` or other action endpoints.
- Token management APIs for authentication.

## Failure Handling
- Handle rate limits by implementing backoff strategies.
- Catch network errors and retry failed requests.
- Gracefully skip malformed or invalid entries during iteration.

## Verification
- Confirm that all expected pages were processed.
- Validate that filtered results match the intended criteria.
- Ensure the correct number of actions were performed on qualifying entries.
