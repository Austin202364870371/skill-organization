---
name: When to Use
description: - When working with APIs that return large datasets in paginated form. - When filtering results based on temporal criteria (e.g., today, yesterday) or content conditions. - When needing to perform actions (e.g., liking, posting) on specific entries that meet certain conditions.
---

---
name: Paginate and Filter API Results
setDescription: Iteratively process paginated API responses, apply date/time and content-based filters, and perform actions on matching items.
---

## When to Use
- When working with APIs that return large datasets in paginated form.
- When filtering results based on temporal criteria (e.g., today, yesterday) or content conditions.
- When needing to perform actions (e.g., liking, posting) on specific entries that meet certain conditions.

## Preconditions
- Valid authentication tokens for relevant services are available.
- Pagination parameters and filter criteria are defined.
- API endpoints support paginated responses and conditional filtering.

## Procedure
1. Authenticate and obtain necessary access tokens.
2. Initiate the first page of a paginated API call using provided pagination parameters.
3. Iterate through each page of results until all pages are processed.
4. For each item in the result set, evaluate whether it meets specified filter criteria (e.g., time range, content match).
5. If the item satisfies the filter criteria, execute the required action (e.g., like, post, update).
6. Continue to the next page until no more data is available.

## Relevant APIs / Tools
- `GET /{service}/endpoint` or similar paginated endpoints.
- `POST /{service}/action` or other action endpoints.
- Token management APIs for authentication.

## Failure Handling
- Handle rate limits by implementing exponential backoff strategies.
- Catch network errors and retry failed requests up to a configured limit.
- Skip malformed or invalid entries during iteration and log them for review.
- If no data is returned after pagination, confirm whether the dataset is empty or an error occurred.

## Verification
- Confirm that all expected pages were processed without skipping due to errors.
- Validate that filtered results strictly adhere to the defined filter criteria.
- Ensure the correct number of actions were performed on qualifying entries.
