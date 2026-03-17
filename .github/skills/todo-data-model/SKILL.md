# TODO Data Model Skill

Use this skill when reasoning about task and project semantics in GTD TODOs.

## GTD Statuses

- `inbox`: captured but not clarified.
- `next_action`: ready to do.
- `waiting_for`: blocked on someone or something else.
- `scheduled`: intended for a later date or has a due date.
- `someday_maybe`: deferred without commitment.
- `done`: completed and closed.

## Project Semantics

- Projects group related tasks.
- Tasks may exist without a project.
- Archived projects remain outside the active browsing flow.

## Due Date Semantics

- `due_date` is optional.
- The Today view compares against the current local date.
- Overdue and due-today items are distinct UI concepts.

## Recurrence Semantics

- Recurring tasks remain a single persistent task record.
- Completing a recurring task advances the same record's `due_date`.
- `last_completed_at` tracks the previous completion time.
- Non-recurring tasks may use `completed_at` when they are closed.

## Notes Semantics

- Notes are stored as raw Markdown text.
- Render notes as sanitized HTML.
- Plain text is already valid Markdown input.