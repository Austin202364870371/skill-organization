---
name: Get Artist with Most or Least Recommendations
description: When asked to identify the artist with the highest or lowest number of song recommendations from a given source.
---

## Get Artist with Most or Least Recommendations

### When to Use
When asked to identify the artist with the highest or lowest number of song recommendations from a given source.

### Preconditions
- Access to a music streaming service (e.g., Spotify) with recommendation capabilities.
- Authentication credentials for the service.
- Ability to fetch paginated recommendations.
- Availability of artist information associated with each recommendation.

### Procedure
1. Authenticate with the music service using stored credentials.
2. Fetch a list of song recommendations, handling pagination if necessary.
3. For each recommendation, extract the associated artist information.
4. Count occurrences of each artist across all recommendations.
5. Determine the artist with the maximum or minimum count based on user request.
6. Retrieve and return the name of the identified artist.

### Relevant APIs / Tools
- `apis.spotify.access_token_from`
- `apis.spotify.show_recommendations`
- `apis.spotify.show_song`
- `apis.spotify.show_artist`
- `apis.supervisor.message`

### Failure Handling
- If authentication fails, retry with updated credentials or notify the user.
- If no recommendations are retrieved, return an appropriate error message.
- If artist data cannot be fetched, log the issue and continue processing other entries.
- If insufficient or no artist data is available to determine a result, return a fallback response indicating inability to determine.

### Verification
- Confirm that the returned artist name matches the expected result based on recommendation counts.
- Ensure all recommendations were processed and counted correctly.
- Validate that the final artist name is consistent with the specified "most" or "least" criteria.
- If the result is ambiguous or cannot be determined due to lack of data, ensure an appropriate fallback is used.
