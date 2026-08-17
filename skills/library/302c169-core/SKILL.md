---
name: Update Alarm Time and Manage Other Alarms
description: This skill involves authenticating with the phone application, retrieving existing alarms, updating a specific alarm's time, and disabling other enabled alarms.
---

## When to Use
- When modifying an existing alarm's time and ensuring only one alarm remains enabled.

## Preconditions
- The user has valid account credentials for the phone application.
- There exists at least one alarm with a label that matches a known pattern (e.g., "Go to sleep" or "Wake Up").
- The system supports updating alarm times and enabling/disabling alarms via API.

## Procedure
1. Authenticate with the phone application using valid credentials.
2. Retrieve all alarms from the phone application using the authentication token.
3. Identify the target alarm by matching a label substring.
4. Compute the new alarm time based on whether the adjustment is later or earlier, and the metric (hours or minutes).
5. Update the identified alarm with the computed new time.
6. Fetch the updated list of alarms.
7. For each alarm in the list that is not the target alarm and is currently enabled, disable it.

## Relevant APIs / Tools
- `apis.phone.login`
- `apis.phone.show_alarms`
- `apis.phone.update_alarm`

## Failure Handling
- If authentication fails, retry with correct credentials or notify the user.
- If no matching alarm is found, log error and abort process.
- If updating the alarm fails, attempt to restore previous state if possible.

## Verification
- Confirm that the target alarm’s time has been correctly updated.
- Ensure that all non-target alarms are disabled after the update.
- Validate that only the intended fields (`time` for target alarm, `enabled` for others) have changed.
- Verify that the updated time matches the expected value.
- Ensure that all alarms marked for disabling are indeed disabled.
