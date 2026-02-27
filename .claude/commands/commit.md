# /commit - Create Git Commit

Create a git commit following conventional commit format.

## Rules

- Maximum 4 lines total (including title)
- Use conventional prefixes: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Focus on what changed, not implementation details
- No `Co-Authored-By` trailer

## Workflow

1. Check git status and diff
2. Review recent commits for style reference
3. Stage appropriate files
4. Create commit with properly formatted message

## Example Output

```
feat: add campaign analytics dashboard

Add campaign performance chart component.
Integrate with RTK Query for data fetching.
```
