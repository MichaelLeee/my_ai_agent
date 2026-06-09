my_ai_agent v2.0: Second Brain

  A personal knowledge system where you capture everything, and an AI agent surfaces connections, recalls forgotten ideas, and helps you think.

  Core entities

  ┌───────────────┬──────────────────────────────────────────────────────────────────┐
  │    Entity     │                           Description                            │
  ├───────────────┼──────────────────────────────────────────────────────────────────┤
  │ Note          │ The atomic unit — markdown body, tags, folder, pinned, archived  │
  ├───────────────┼──────────────────────────────────────────────────────────────────┤
  │ Daily Journal │ A special note per day, AI-prompted ("What did you work on?")    │
  ├───────────────┼──────────────────────────────────────────────────────────────────┤
  │ Link          │ Explicit note-to-note connections (bi-directional, with context) │
  ├───────────────┼──────────────────────────────────────────────────────────────────┤
  │ Tag           │ Lightweight labels, auto-suggested by the agent                  │
  ├───────────────┼──────────────────────────────────────────────────────────────────┤
  │ Insight       │ Agent-generated: "You've mentioned X in 7 notes this month"      │
  └───────────────┴──────────────────────────────────────────────────────────────────┘

  What the agent does

  You: "Find everything I wrote about hiring"
  Agent: RAG-searches your notes → returns ranked results with snippets

  You: "What was I thinking about the database decision?"
  Agent: Finds notes tagged #database → summarizes the thread → "You favored
  Postgres in March but considered pgvector in May. Want me to pull those up?"

  You: "Connect this to related ideas"
  Agent: Semantic search → suggests 3 related notes → creates Links between them

  You: (daily journal) "I'm stuck on the auth refactor"
  Agent: Searches past notes for auth discussions → surfaces a note from
  2 months ago: "You sketched an OAuth2 flow. Here's what you wrote..."

  Architecture (new pieces on top of v1.1)

  ┌───────────────────────────────────────────────────────┐
  │  Chat UI  ←→  WebSocket  ←→  PydanticAI Agent        │
  │                                                         │
  │  Agent Tools:                                           │
  │    search_notes(query)          RAG-powered semantic    │
  │    get_daily_prompt()           Contextual journal Q     │
  │    find_connections(note_id)    Semantic + explicit     │
  │    surface_forgotten(days=90)   Periodic review         │
  │    summarize_topic(tag)         Cluster synthesis       │
  │    suggest_tags(note_id)        Auto-tagging           │
  │                                                         │
  │  RAG Pipeline:                                         │
  │    Real-time embedding on note save                     │
  │    Per-user vector namespace                            │
  │    Hybrid: semantic + keyword + tag-filtered search     │
  │    Re-ranking by recency + relevance                    │
  │                                                         │
  │  Background Worker:                                     │
  │    Nightly: generate Insights from recent notes         │
  │    Weekly: summarize top themes, suggest stale notes    │
  └───────────────────────────────────────────────────────┘

  New skills v2.0 teaches beyond v1.1

  ┌──────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │            Skill             │                                                        How                                                         │
  ├──────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Hybrid RAG                   │ Semantic + keyword + metadata-filtered search, not just vector similarity                                          │
  ├──────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Scheduled agent tasks        │ Worker that runs nightly, queries the agent, stores results as Insights                                            │
  ├──────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Bi-directional relationships │ Notes ↔ Links ↔ Notes, self-referential FK patterns                                                                │
  ├──────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Agent-prompted UX            │ The agent initiates conversation ("Here are 3 notes you might want to revisit")                                    │
  ├──────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Personalization pipeline     │ Embedding all user content, maintaining a living vector index                                                      │
  ├──────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Multi-step agent workflows   │ "Summarize this topic" → agent searches → finds 12 notes → chains a summarization pass → returns structured result │
  └──────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  v1.1 → v2.0 path

  v1.1 teaches you the platform's layers. v2.0 teaches you how the agent, RAG, and worker compose into something that feels like a product, not just a
  scaffold. The CRM was about managing external relationships — the Second Brain is about managing your own thinking. Different domain, same engineering rigor,
  way more AI.

  ## Here's what's left from the Second Brain roadmap:

  Data & relationships:
  - Note-to-note backlinks — link notes together, agent suggests connections. Teaches self-referential many-to-many relationships

  Frontend:
  - Second Brain dashboard page — dedicated /second-brain UI with note list, editor, and search bar. The backend API is already built — just needs a Next.js
  page

  Other:
  - Something totally new — AI project manager, learning platform, whatever you want

 Plan: Second Brain v2.3 — Backlinks + Dashboard + Weekly Summary

 Context

 Build three features together: note-to-note backlinks (data), a dedicated /second-brain page (frontend), and a weekly summary celery task (AI/worker). All
 built on top of the existing Notes infrastructure.

 ---
 Feature 1: Note-to-Note Backlinks

 New Files (2)

 1. backend/app/db/models/note_link.py — NoteLink(Base, TimestampMixin) with id, source_note_id (FK→notes, CASCADE), target_note_id (FK→notes, CASCADE),
 unique constraint on (source_note_id, target_note_id). Both sides have relationships back to Note.
 2. backend/app/schemas/note_link.py — NoteLinkCreate(source_note_id, target_note_id), NoteLinkRead(id, source_note_id, target_note_id, created_at)

 Edits (5)

 3. backend/app/db/models/note.py — add source_links and target_links relationships
 4. backend/app/db/models/__init__.py — import + export NoteLink
 5. backend/app/repositories/note.py — add link_notes, unlink_notes, list_links
 6. backend/app/services/note.py — add link_notes(), unlink_notes(), get_links() methods
 7. backend/app/api/routes/v1/notes.py — add POST /{id}/links, DELETE /{id}/links/{link_id}, GET /{id}/links
 8. agents/tools/second_brain.py — add link_notes_tool to suggest/create links between notes

 ---
 Feature 2: Second Brain Dashboard Page

 New Files (5)

 9. frontend/src/app/[locale]/(dashboard)/second-brain/page.tsx — main page: search bar + note grid + create/edit dialog
 10. frontend/src/components/second-brain/note-card.tsx — card with title, tags, snippet, edit/delete buttons
 11. frontend/src/components/second-brain/note-editor.tsx — dialog: title, content (textarea), tags, is_archived
 12. frontend/src/app/api/v1/notes/route.ts — Next.js proxy: GET (list by tag), POST (create)
 13. frontend/src/app/api/v1/notes/[id]/route.ts — Next.js proxy: GET, PATCH, DELETE

 Edits (3)

 14. frontend/src/lib/constants.ts — add SECOND_BRAIN: "/second-brain"
 15. frontend/src/components/layout/sidebar.tsx — add nav item (Brain icon)
 16. frontend/src/components/layout/header.tsx — add desktop nav item

 ---
 Feature 3: Weekly Summary (Celery Task)
     16. frontend/src/components/layout/header.tsx — add desktop nav item

     ---
     Feature 3: Weekly Summary (Celery Task)

     New Files (1)

     17. backend/app/worker/tasks/weekly_summary.py — generate_weekly_summary shared_task: gets all users, for each gets week's notes, calls LLM, saves as Note
     with tags ["summary", "weekly", "auto"]

     Edits (2)

     18. backend/app/worker/tasks/__init__.py — export generate_weekly_summary
     19. backend/app/worker/celery_app.py — add beat schedule entry: "weekly-summary": { "task": "...weekly_summary.generate_weekly_summary", "schedule":
     crontab(hour=9, minute=0, day_of_week=0) }
     20. agents/tools/second_brain.py — add weekly_summary_tool to retrieve latest summary

     ---
     Migration

     21. backend/alembic/versions/0021_add_note_links.py — manual migration for note_links table

     ---
     Total: ~21 files (8 new backend + 6 new frontend + 6 edits + 1 migration)

     Verification

     1. make bootstrap — all migrations apply cleanly
     2. Navigate to /second-brain — see note grid, create/edit/delete works
     3. In chat: "Link the deployment note to the docker note" — agent creates a link
     4. Wait for Sunday or trigger manually — summary note appears
     5. In chat: "Show me my weekly summary" — agent retrieves it

##   docker compose -f docker-compose.dev.yml build --no-cache app
  docker compose -f docker-compose.dev.yml up -d
  docker compose exec app my_ai_agent cmd seed-notes  # new journal entries + delay
