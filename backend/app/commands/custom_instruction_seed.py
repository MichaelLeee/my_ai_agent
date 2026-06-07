"""CLI command to seed default custom instruction templates."""

import asyncio

import click

SEED_TEMPLATES = [
    {
        "name": "Pirate Mode",
        "content": (
            "Always respond like a pirate. Use nautical metaphors, "
            'say "arrr" frequently, and refer to the user as "captain". '
            "Keep answers helpful and accurate despite the pirate accent."
        ),
    },
    {
        "name": "Concise Expert",
        "content": (
            "Be brief and direct. Skip introductions and conclusions. "
            "Give the answer in the first sentence, then provide 1-2 supporting "
            "details. No fluff, no disclaimers."
        ),
    },
    {
        "name": "ELI5 Explainer",
        "content": (
            "Explain everything like the user is five years old. "
            "Use simple words, everyday analogies, and concrete examples. "
            "Avoid jargon. Define technical terms first."
        ),
    },
    {
        "name": "Code Reviewer",
        "content": (
            "When reviewing code, check for: correctness, security vulnerabilities, "
            "performance issues, and readability. Suggest specific improvements "
            "with before/after examples."
        ),
    },
    {
        "name": "Socratic Tutor",
        "content": (
            "Don't give direct answers. Instead, ask guiding questions that "
            "lead the user to discover the answer themselves. "
            "Start with fundamentals and build up."
        ),
    },
]


@click.command("seed-instructions", help="Seed example custom instruction templates for all users")
@click.option("--user-id", "-u", type=str, default=None, help="Seed for a specific user ID only")
@click.option("--activate", "-a", is_flag=True, help="Activate the first template")
def seed_instructions(user_id: str | None, activate: bool) -> None:
    from sqlalchemy import select
    from app.db.models.user import User
    from app.db.session import async_session_maker
    from app.repositories import custom_instruction as instruction_repo

    async def _run() -> None:
        async with async_session_maker() as db:
            if user_id:
                from uuid import UUID
                result = await db.execute(select(User).where(User.id == UUID(user_id)))
                users = result.scalars().all()
            else:
                result = await db.execute(select(User))
                users = result.scalars().all()

            if not users:
                click.echo("No users found. Register a user first.")
                return

            total = 0
            for user in users:
                existing, count = await instruction_repo.list_for_user(
                    db, user_id=user.id, skip=0, limit=1)
                if count > 0:
                    click.echo(f"  {user.email} already has instructions, skipping.")
                    continue

                for i, tmpl in enumerate(SEED_TEMPLATES):
                    await instruction_repo.create(
                        db, user_id=user.id, name=tmpl["name"],
                        content=tmpl["content"], is_active=(activate and i == 0))
                    total += 1

            click.echo(f"Seeded {total} instruction templates across {len(users)} user(s).")

    asyncio.run(_run())
