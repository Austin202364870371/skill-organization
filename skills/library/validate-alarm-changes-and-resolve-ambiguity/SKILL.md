---
name: validate_alarm_changes_and_resolve_ambiguity
description: Handle missing or duplicate target alarms, verify time arithmetic across day boundaries, and ensure the final alarm state is correct.
---

## When to Use
Use when the target alarm label might match multiple alarms, when the target alarm could be disabled, or when you need to validate that time shifts and disable operations were applied correctly.

## Preconditions
- You already have a valid phone access token.
- You have a way to list alarms (phone.show_alarms) with pagination.

## Procedure
1. Fetch all alarms into a single list using pagination.
2. Find all alarms whose label contains the target substring.
3. If no matches are found, do not make any changes and complete the task (e.g., report success with no action).
4. If multiple matches exist, prefer an enabled alarm; if several enabled, pick the one with the smallest alarm_id.
5. When computing the new time, use a time utility that handles day wrap-around (e.g., the `Time` class). Verify the result is in a valid 24-hour format.
6. When disabling other alarms, only disable alarms that are currently enabled and whose ID differs from the selected target.
7. After updates, re-fetch alarms and assert:
   - The target alarm's time equals the expected new time.
   - Every other alarm has `enabled` set to `False`.

## Relevant APIs / Tools
- apis.phone.show_alarms
- apis.phone.update_alarm
- apis.supervisor.complete_task

## Failure Handling
- If multiple alarms match but none are enabled, choose the first one in the list.
- If an update returns an error, check the access token and alarm ID; retry once before failing.
- If pagination is incomplete, continue fetching pages until the list is exhausted.

## Verification
- Re-fetch alarms and programmatically confirm the target alarm time and the disabled state of all other alarms before completing the task.
