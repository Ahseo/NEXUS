# /pr - Create Pull Request

Create a pull request to origin/main.

## Arguments

- `$ARGUMENTS` - Optional base branch (default: `main`)

## Workflow

1. Fetch origin and rebase on base branch
2. Push current branch to origin
3. Analyze full commit history from base branch
4. Create PR with:
   - Title: `<type>: <description>`
   - Target: `main` (or specified base)

## Example

```bash
/pr          # PR to main
/pr develop  # PR to develop
```
