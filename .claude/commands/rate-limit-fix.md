# Claude Code 429 Rate Limit Recovery

## When you hit 429 errors:
1. STOP all current work
2. git add -A && git commit -m "wip: checkpoint before rate limit pause"
3. git push origin [current-branch]
4. Switch to a DIFFERENT branch for independent work
5. Wait 10-15 minutes before resuming

## Prevention
- Sequential worktrees for Claude API calls, NOT parallel
- Commit and push after EVERY prompt
- Use Redis caching to reduce API calls
