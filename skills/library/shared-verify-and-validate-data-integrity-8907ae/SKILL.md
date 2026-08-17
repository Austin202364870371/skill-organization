---
name: Verify and Validate Data Integrity
description: Check and validate the integrity of retrieved data against expected schemas or business rules before further processing.
---

## When to Use
- When required to ensure data consistency and correctness prior to downstream operations.
- When integrating or aggregating data from multiple sources that must conform to specific formats or constraints.

## Preconditions
- Access to the data source and validation rules.
- Valid credentials for accessing the data source.
- Defined schema or business rules to validate against.

## Procedure
1. Retrieve data from the specified data source.
2. Apply defined validation rules to check data format, presence of required fields, and adherence to business logic.
3. Flag any data items that fail validation.
4. Generate a validation report summarizing passed and failed items.
5. Return integrity flags and validation report.

## Relevant APIs / Tools
- `file_system.show_file`
- `simple_note.show_note`
- `spotify.show_song`

## Failure Handling
- If data retrieval fails, log the error and return an empty validation report.
- If validation rules cannot be applied due to missing or unexpected data structures, mark affected items as invalid and continue processing.
- If a data item fails validation, record the failure reason and proceed with other items.

## Verification
- Confirm that all retrieved data items are checked against the validation rules.
- Validate that the returned integrity flags accurately reflect the state of each item.
- Ensure the validation report includes all relevant data points and failure reasons.
