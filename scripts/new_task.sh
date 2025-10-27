#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 PHASE<ID>-<ISSUE> short-slug"
  echo "Example: $0 PHASE1-3 database-schema"
  exit 1
fi

ISSUE="$1"
SLUG="$2"
BRANCH="${ISSUE}-${SLUG}"
WORKTREE="../waifu-backend-fastapi-${BRANCH}"

git fetch origin
git worktree add "$WORKTREE" -b "$BRANCH" origin/main
echo "Worktree created at: $WORKTREE"
echo "Branch: $BRANCH"
echo "Next steps:"
echo "  cd $WORKTREE"
echo "  Copy .env from main worktree or create new one (see .env.example)"
echo "  Follow the assigned phase doc in docs/tasks/"
echo "  Implement → test → lint → RepoPrompt MCP review → open PR"