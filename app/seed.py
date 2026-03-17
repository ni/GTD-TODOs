"""Seed the database with sample data for local testing."""

from datetime import date, timedelta

from sqlmodel import Session

from app.db import get_engine, init_db
from app.models import RecurrenceType, TaskStatus
from app.services.project_service import create_project
from app.services.task_service import create_task


def seed() -> None:
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        # Projects
        home = create_project(session, name="Home", description="Household tasks")
        work = create_project(session, name="Work", description="Professional tasks")
        health = create_project(session, name="Health", description="Fitness and wellness")

        today = date.today()

        # Inbox items
        create_task(session, title="Look into new podcast app")
        create_task(session, title="Research gift ideas for birthday")

        # Next actions
        create_task(
            session,
            title="Buy groceries",
            status=TaskStatus.NEXT_ACTION,
            project_id=home.id,
            notes="- Milk\n- Eggs\n- Bread\n- Vegetables",
        )
        create_task(
            session,
            title="Review pull request",
            status=TaskStatus.NEXT_ACTION,
            project_id=work.id,
            due_date=today,
        )

        # Scheduled
        create_task(
            session,
            title="Dentist appointment",
            status=TaskStatus.SCHEDULED,
            project_id=health.id,
            due_date=today + timedelta(days=7),
        )

        # Recurring tasks
        create_task(
            session,
            title="Water plants",
            status=TaskStatus.NEXT_ACTION,
            project_id=home.id,
            due_date=today,
            is_recurring=True,
            recurrence_type=RecurrenceType.WEEKLY,
        )
        create_task(
            session,
            title="Daily standup",
            status=TaskStatus.NEXT_ACTION,
            project_id=work.id,
            due_date=today,
            is_recurring=True,
            recurrence_type=RecurrenceType.DAILY,
        )
        create_task(
            session,
            title="Monthly budget review",
            status=TaskStatus.SCHEDULED,
            project_id=home.id,
            due_date=today + timedelta(days=14),
            is_recurring=True,
            recurrence_type=RecurrenceType.MONTHLY,
            notes=(
                "## Budget Review\n\nCheck:\n"
                "1. Savings goal\n2. Subscriptions\n3. Upcoming expenses"
            ),
        )

        # Waiting for
        create_task(
            session,
            title="Waiting on plumber callback",
            status=TaskStatus.WAITING_FOR,
            project_id=home.id,
        )

        # Someday/maybe
        create_task(
            session,
            title="Learn to play guitar",
            status=TaskStatus.SOMEDAY_MAYBE,
            notes="Look into beginner courses online.",
        )

        # Overdue task
        create_task(
            session,
            title="Submit expense report",
            status=TaskStatus.NEXT_ACTION,
            project_id=work.id,
            due_date=today - timedelta(days=2),
        )

    print("Seeded database: 3 projects, 11 tasks")


if __name__ == "__main__":
    seed()
