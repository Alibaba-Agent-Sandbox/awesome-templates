# Delivery draft: Public README audience boundary

Publication is BLOCKED: GitHub authentication is unavailable. This is not an open PR.

## PR title

docs: keep template README focused on discovery and use

## Summary

The root README exposed historical acceptance matrices and implementation notes before basic
usage. Replace them with bilingual launch and credential instructions, preserve catalog entries
and statuses, and apply the documentation audience rule to repository READMEs and user guides.
Original engineering evidence remains unchanged.

## Type of change

- [x] Documentation

## Testing

- `python3 scripts/check_docs.py`: 224 documents, zero failures.
- Source table comparison: all 46 entries/statuses preserved; four managed identities retained.
- `git diff --check`: passed.
- No runtime/cloud changes or resource creation.

## Limitations

Remote checks/review and actual PR creation/merge require authenticated repository access.
