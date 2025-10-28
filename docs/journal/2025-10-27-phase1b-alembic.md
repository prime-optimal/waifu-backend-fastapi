# Phase 1B - Alembic Journal Entry
**Date:** 2025-10-27  
**Task:** Phase 1B — Alembic Migration
**Branch:** PHASE1B
**Status:** ✅ COMPLETED

## Objectives Achieved
1. ✅ Alembic Migration from NeonDb
2. The underlying issue was that neon blocks VPNs relentlessly.
3. ✅ All required tests passing
4. ✅ Code quality verified

## Implementation Details
- Installed neon cli, neon local -- anything to get it working.  
- postgresql string ended up working.
- Installed the neon vscode extension
- Used Orbstack to login to the Neon postgres container.
- Added another user, but it didn't work because it was just a user in the system, not a postgres user.
- Uninstalled postgres@17 via homebrew
- Installed postgres v18 app which ultimately lead to further confusion because the postgres connection strings never seemed to work.

### Environment Configuration
- At one point there were 3 postgres databases muddying the waters:
  - Postgres v18
  - An older postgres container that Orbstack had lying around
  - the Neon VS Code extension that I added the API key to, but still was unable to see any of the content inside the Neon extension.  
  - I'm pretty sure part of what caused the challenge is that all 3 instances were fighting for the same port. 
  - Once I had the idea to change of the ports from 5432 to 5433, everything staretd to make mor sense. 
- **Updated .env** with required variables:
  - `DATABASE_URL`: Points to local Postgres (`postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/waifu_local`)
  - `DATABASE_URL`: Override properly configured for FastAPI
  - `PGPASSWORD`: Set for CLI operations
  - `PYTHONPATH=.`: Added as required
- **NEON_DATABASE_URL**: Maintained for production use (connection timeout from current environment)


### Database Setup


### Code Changes
#### src/db/database.py
- Alembic migration was definitely one of the hardest tasks to ever pulled off in my life. 
- Me and GPT5 mini really struggled with that one. 
- The last round he was better at listening, but this time around I kept having to babysit him. 
- Eventually he tricked Codex into giving him the approval if the tests at the end passed.
- But they didn't pass and basically it was just me at the end trying to figure out Alembic, not really knowing what it did and also not being the one that installed it. 
- But removing the alembic folder and starting over didn't really work because the files were hidden in the cahce. 
- Eventually after messing with it for FOREVER, I gave in and got GLM4.6 in debugger mode to fix it and he fixed it REAL fast. 
- Took it to Codex to review because the final command, alembic revision --autogenerate was getting cluttered up by previous database schema that we'd thrown away.
- Basically I don't know if itt was our plans that were flawed or Codex giving the approval, but to me, it seemed pretty surprising to get to the end of a phase, only to find out that NOTHING we had worked because all these errors were popping up. 
- SO I had to fix it myself, while knowing nothing about SQLAlchemy or alembic.  
- At some point, the model in RepoPrompt switched from Codex to kimi-0905 and I was surprised and impressed with how well it was able to fix something as obscure as alembic.  
- 
### Test Results
```
✅ Database Migration: SUCCESS
✅ ./scripts/reset_alembic_history.sh gave us a fresh start
✅ Code Quality: alembic upgrade head
```

### Issues Encountered & Resolved
- Neon definitely detects VPNs which is annoying.

## Next Steps Preparation
- I think for the rest of the project, it's gotta be GPT5, Claude, and GLM4.6 for debugging.

