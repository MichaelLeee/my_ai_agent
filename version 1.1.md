##Next steps:

  cd my_ai_agent

1. Environment:
  backend/.env and frontend/.env.local are pre-configured
  # Review and update settings as needed

2. Install backend dependencies:
  make install

3. Database setup:
  make docker-db        # Start PostgreSQL container
  make db-migrate       # Create initial migration
  make db-upgrade       # Apply migrations

  ⚠️  Run all commands in order: db-migrate creates the migration, db-upgrade applies it

4. Run backend:
  make run

5. Frontend setup (in new terminal):
  cd frontend
  bun install
  bun run dev

Quick start (recommended):
  make quickstart
  → install deps, start Docker, run migrations, create admin

Set LOGFIRE_TOKEN in backend/.env → https://logfire.pydantic.dev

RAG (pgvector):
  uv run my_ai_agent rag-ingest /path/to/docs/ --collection documents
  uv run my_ai_agent rag-search "your query" --collection documents
  uv run my_ai_agent rag-collections
Set TAVILY_API_KEY in backend/.env → https://tavily.com

Frontend: http://localhost:3030
API: http://localhost:8080
Docs: http://localhost:8080/docs
Run 'make help' for all available commands


## http://localhost:3030/instructions

PydanticAI agent, RAG (pgvector), WebSocket chat, Next.js dashboard, CLI commands. No example CRUD scaffold to learn from.

  Recommendation: Agent Custom Instructions

  A feature that lets users create, edit, and activate custom system prompt templates — the agent picks them up at runtime and adapts its behavior. It's the
  smallest feature that forces you through every architectural layer.

  Architecture coverage

  ┌────────────────┬──────────────────────────────────────────────────────────────────────────────────────────┐
  │     Layer      │                                    What you'll build                                     │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ DB Model       │ CustomInstruction(Base, TimestampMixin) — Mapped[], mapped_column(), ForeignKey to user  │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ Schema         │ InstructionCreate/Update/Read/List — ConfigDict(from_attributes=True), field validators  │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ Repository     │ Pure db.flush() + db.refresh() functions, keyword-only args                              │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ Service        │ InstructionService class — ownership checks, NotFoundError, deactivate_others()          │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ DI             │ InstructionSvc = Annotated[..., Depends(get_instruction_service)] in deps.py             │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ API Route      │ Full CRUD in routes/v1/custom_instructions.py — CurrentUser, response_model, status_code │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ Agent Tool     │ get_active_instructions tool — queries service, injects into system prompt via Deps      │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ WebSocket      │ Push event when instructions change (reuse existing use-websocket.ts pattern)            │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ CLI            │ commands/custom_instruction_seed.py — seed 5 default templates                           │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ Frontend pages │ instructions/page.tsx (list) + instructions/[id]/page.tsx (editor) — Next.js App Router  │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ Frontend store │ instruction-store.ts — Zustand for client state                                          │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ Frontend hook  │ use-custom-instructions.ts — TanStack Query for server state                             │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ Types          │ types/custom-instruction.ts — TypeScript interfaces                                      │
  ├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ Components     │ InstructionCard, InstructionEditor — React components                                    │
  └────────────────┴──────────────────────────────────────────────────────────────────────────────────────────┘

  The 14 files

  backend/
  ├── app/db/models/custom_instruction.py
  ├── app/schemas/custom_instruction.py
  ├── app/repositories/custom_instruction.py
  ├── app/services/custom_instruction.py
  ├── app/api/routes/v1/custom_instructions.py
  ├── app/agents/tools/custom_instruction_tool.py
  ├── app/commands/custom_instruction_seed.py
    + edits to: deps.py, routes/v1/__init__.py, agents/assistant.py, agents/prompts.py

  frontend/
  ├── src/app/[locale]/(dashboard)/instructions/page.tsx
  ├── src/app/[locale]/(dashboard)/instructions/[id]/page.tsx
  ├── src/components/custom-instructions/instruction-card.tsx
  ├── src/components/custom-instructions/instruction-editor.tsx
  ├── src/stores/instruction-store.ts
  ├── src/hooks/use-custom-instructions.ts
  ├── src/types/custom-instruction.ts

  Runtime flow

  1. User creates instruction: "Always respond like a pirate. Use nautical metaphors."
  2. Stored in DB, user activates it
  3. On next chat message → AssistantAgent.run() → _register_tools() → agent calls get_active_instructions tool → tool queries
  InstructionService.get_active_for_user() → returns instructions → injected into system prompt → agent responds like a pirate

  Why this vs alternatives

  - Document Q&A — RAG + chat already exists in the project, you'd be reimplementing existing features
  - Feedback analysis — message_rating model and admin ratings page already exist
  - Meeting notes extractor — touches the same layers but is 2-3x more complex for a first feature













  What was built — 14 new files + 9 edits

  Backend (7 new + 4 edits)

  ┌─────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                  File                   │                                              What it does                                              │
  ├─────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ db/models/custom_instruction.py         │ DB model — CustomInstruction(Base, TimestampMixin) with id, user_id (FK), name, content, is_active     │
  ├─────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ schemas/custom_instruction.py           │ Pydantic schemas — InstructionCreate, Update, Read, List                                               │
  ├─────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ repositories/custom_instruction.py      │ Data access — list_for_user, get_by_id, create, update, delete, deactivate_others, get_active_for_user │
  ├─────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ services/custom_instruction.py          │ Business logic — ownership checks, auto-deactivate on activation, domain exceptions                    │
  ├─────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ routes/v1/custom_instructions.py        │ REST API — 5 endpoints (GET list, POST create, GET by id, PATCH update, DELETE)                        │
  ├─────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ agents/tools/custom_instruction_tool.py │ Agent tool — get_active_instructions(ctx) called at conversation start                                 │
  ├─────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ commands/custom_instruction_seed.py     │ CLI — seed-instructions with 5 templates (Pirate, Concise Expert, ELI5, Code Reviewer, Socratic Tutor) │
  ├─────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ db/models/user.py (edit)                │ Added custom_instructions relationship                                                                 │
  ├─────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ api/deps.py (edit)                      │ Added InstructionSvc DI alias                                                                          │
  ├─────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ routes/v1/__init__.py (edit)            │ Registered custom_instructions router                                                                  │
  ├─────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ agents/assistant.py (edit)              │ Registered active_instructions agent tool                                                              │
  └─────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  Frontend (7 new + 5 edits)

  ┌───────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────┐
  │                         File                          │                            What it does                             │
  ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ types/custom-instruction.ts                           │ TypeScript interfaces                                               │
  ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ stores/instruction-store.ts                           │ Zustand store — state + actions for CRUD                            │
  ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ hooks/use-custom-instructions.ts                      │ React hook — wraps apiClient + store + toast                        │
  ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ components/custom-instructions/instruction-card.tsx   │ Card with activate/deactivate toggle, edit/delete buttons           │
  ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ components/custom-instructions/instruction-editor.tsx │ Dialog for create/edit with name, content textarea, active checkbox │
  ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ app/(dashboard)/instructions/page.tsx                 │ List page — grid of cards, empty state, add button                  │
  ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ app/(dashboard)/instructions/[id]/page.tsx            │ Editor page — full form, save/delete                                │
  ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ Sidebar, constants, store/hook/type indexes (edits)   │ Navigation link, route constant, barrel exports                     │
  └───────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────┘

  Next steps

  1. Unzip the changes into your project — the zip mirrors your directory structure, so extract at project root
  2. Generate and apply the migration:
  cd backend
  uv run alembic revision --autogenerate -m "add custom instructions table"
  uv run alembic upgrade head
  3. Start backend and seed templates:
  uv run my_ai_agent seed-instructions --activate
  4. Start frontend:
  cd frontend
  bun dev
  5. Test the flow: navigate to /instructions, create an instruction like "Pirate Mode", activate it, then go to /chat and verify the agent picks it up

## The Docker container exposes PostgreSQL on port 5433. Your local uv run alembic command hits localhost:5432 which has nothing. Run it inside the container:

  docker compose exec app uv run alembic revision --autogenerate -m "add custom instructions table"
  docker compose exec app uv run alembic upgrade head

  Same for the seed command and any other backend CLI:

  docker compose exec app uv run my_ai_agent seed-instructions --activate

  ## Error alembic.script.revision.ResolutionError: No such revision or branch '0ec60fc119e1'. alembic.util.exc.CommandError: Can't locate revision identified by
   The Docker database volume has a stale alembic revision from a previous run. Same issue as before with the CRM project. Wipe it:

  docker compose -f docker-compose.dev.yml down -v
  make bootstrap

  The -v removes the PostgreSQL data volume so alembic starts fresh with the current migrations.

## For the Docker exec error — uv isn't inside the container. Use the project's own CLI:

  # Run migrations (inside container)
  docker compose exec app my_ai_agent db upgrade head

  # Generate new migration
  docker compose exec app my_ai_agent db revision --autogenerate -m "add custom instructions"

  # Apply it
  docker compose exec app my_ai_agent db upgrade head

  # Seed templates
  docker compose exec app my_ai_agent cmd seed-instructions --activate

  The my_ai_agent command is the CLI bundled inside the Docker image — it wraps alembic and all project commands.

## The CLI has db migrate, not db revision. Use:
  docker compose exec app my_ai_agent db migrate "add custom instructions"
  # or docker compose exec app my_ai_agent db upgrade
  docker compose exec app my_ai_agent db upgrade

## The volume is :ro (read-only) — the db migrate command failed silently because it can't write. Generate the migration on your host directly:

  cd backend
  uv run alembic revision --autogenerate -m "add custom instructions"

  Then restart Docker (the file will be mounted read-only, but alembic can read it):

  docker compose exec app my_ai_agent db upgrade

  The volume mapping is ./backend/app → /app/app, so the migration file at backend/app/alembic/versions/ on your host appears at /app/app/alembic/versions/ inside the container. Running db upgrade will
  pick it up.

## Target database is not up to date.
    FAILED: Target database is not up to date.

  # Re-generate (make sure your DB is clean)
    cd backend
    uv run alembic revision --autogenerate -m "add custom instructions"
## Delete the broken migration file, then:

  # 1. Delete the bad file
  rm backend/alembic/versions/*add_custom*

  # 2. Stamp the DB to match what's on disk
  cd backend
  uv run alembic stamp head

  # 3. Generate a fresh migration (only custom_instructions)
  uv run alembic revision --autogenerate -m "add custom instructions"

  # 4. Apply it
  uv run alembic upgrade head

  Then make dev to restart.

## The .gitignore already covers everything heavy — .venv, node_modules, .next, __pycache__, .env, Docker stuff. Your project should push clean.

  cd ~/Downloads/Developer/my_ai_agent
  git init
  git add .
  git status            # Sanity check — should only see source files
  git commit -m "Initial commit"
  git remote add origin https://github.com/YOUR_USER/my_ai_agent.git
  git push -u origin main

  If git status shows anything unexpected (like node_modules/ or .venv/), that means the .gitignore was added after those files were already tracked. In that
  case:

  git rm -r --cached .venv node_modules .next __pycache__ 2>/dev/null
  git commit -m "Remove tracked artifacts"
  ### GitHub no longer allows passwords. Use a token or SSH.

  Option A — Token (quickest):
  1. Go to https://github.com/settings/tokens
  2. Generate a classic token with repo scope
  3. Copy the token
  4. Use it as your password:

  git push -u origin main
  ### Option B — SSH (one-time setup):

  # Check if you already have a key
  ls ~/.ssh/id_ed25519.pub

  # If not, generate one
  ssh-keygen -t ed25519 -C "your-email@example.com"

  # Copy it
  cat ~/.ssh/id_ed25519.pub

  # Add it at: https://github.com/settings/keys

  # Then switch remote to SSH
  git remote set-url origin git@github.com:MichaelLeee/my_ai_agent.git
  git push -u origin main

  Token is faster for now. Set up SSH later for convenience.
  ### Two options: refusing to allow a Personal Access Token to create or update workflow

  Quick fix — add the scope to your token:
  1. Go back to https://github.com/settings/tokens
  2. Click your token name
  3. Under Repository permissions, set Workflows to Read and write
  4. Save, then retry git push

  Or — if you don't need CI right now:

  git rm --cached .github/workflows/ci.yml
  git commit -m "Remove CI workflow"
  git push -u origin main

  The first option is the right one long-term — you'll want that workflow file in the repo eventually.

  ### Easiest way — just reset the credential:

  git config --unset credential.helper

### my_ai_agent

  # Make sure main is clean and working
  git checkout main

  # Create a branch for each feature
  git branch feature/custom-instructions
  git branch feature/second-brain
  git branch feature/daily-journal

  # Push each branch
  git push origin main feature/custom-instructions feature/second-brain feature/daily-journal

  Going forward, before building something new:

  git checkout -b feature/new-thing   # create + switch to new branch
  # ... build stuff, test it ...
  git add .
  git commit -m "Add new feature"
  git push origin feature/new-thing

  If it works and you want it in main:

  git checkout main
  git merge feature/new-thing
  git push origin main

  If it doesn't work, just switch back to main — no damage done. That's the whole workflow.

  # 1. Make sure main is committed
  git status
  git add .
  git commit -m "Custom Instructions, Second Brain, Daily Journal"

  # 2. Create branches from main
  git branch feature/custom-instructions
  git branch feature/second-brain
  git branch feature/daily-journal

  # 3. Push main first
  git push origin main

  # 4. Push the branches
  git push origin feature/custom-instructions feature/second-brain feature/daily-journal

  After that, when starting new work:

  git checkout -b feature/my-new-feature
  # ... code ...
  git add .
  git commit -m "What I built"
  git push origin feature/my-new-feature

  And to merge a completed feature back:

  git checkout main
  git merge feature/my-new-feature
  git push origin main