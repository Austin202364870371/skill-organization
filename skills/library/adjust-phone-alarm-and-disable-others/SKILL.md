---
name: adjust_phone_alarm_and_disable_others
description: Shift a specific phone alarm by a given duration (later or earlier) and disable all other alarms, typically for vacation or schedule changes.
---

## When to Use
Use when the user asks to move a particular phone alarm (e.g., wake-up or go-to-sleep) by a certain amount of time and disable all other alarms.

## Preconditions
- The main user profile and account passwords are accessible via supervisor APIs.
- The phone app supports listing and updating alarms.

## Procedure
1. Retrieve the main user's profile and account passwords from the supervisor.
2. Obtain a phone access token by logging in with the main user's credentials via `phone.login`.
3. List all alarms using `phone.show_alarms`, handling pagination until all alarms are retrieved.
4. Identify the target alarm by matching its label with a case-insensitive substring (the label is provided in the instruction).
5. Compute the new alarm time: parse the current time, add or subtract the requested hours/minutes, and format it as a valid time string.
6. Update the target alarm's time using `phone.update_alarm`.
7. Re-fetch all alarms. For every alarm that is enabled and is not the target, disable it using `phone.update_alarm` with `enabled=False`.
8. Complete the task with `supervisor.complete_task`.

## Relevant APIs / Tools
- apis.supervisor.show_profile
- apis.supervisor.show_account_passwords
- apis.phone.login
- apis.phone.show_alarms
- apis.phone.update_alarm
- apis.supervisor.complete_task

## Failure Handling
- If the target alarm cannot be found, re-fetch and retry. If still missing, do not disable any other alarms and complete with a failure/success status as appropriate.
- If an update fails, verify that the access token is valid and that the alarm ID is correct.

## Verification
- After all updates, fetch alarms again and confirm the target alarm has the expected new time and all other alarms are disabled.
