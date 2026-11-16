"""PostgreSQL fixtures for API integration tests.

Set ``TEST_DATABASE_URL`` to a disposable PostgreSQL database, for example the
``balance_test`` database created by ``compose.yaml``::

    TEST_DATABASE_URL=postgresql+psycopg://balance:balance@localhost:5432/balance_test

Every table in that database is dropped and recreated. Without the variable,
these tests are skipped locally; CI always sets it, so they never skip there.
"""

import os
from collections.abc import Iterator
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.api.budgets import get_now
from app.core.db import Base, get_db
from app.main import app
from app.models import Budget
from app.seed import seed_demo_data

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
DEMO_USER_ID = 1

# Wednesday, November 18, 2026 at noon: 5 days left in the week (Wed-Sun),
# 13 days left in November, and every demo "this week" row is in November.
FIXED_NOW = datetime(
    2026, 11, 18, 12, 0, tzinfo=ZoneInfo("America/Indiana/Indianapolis")
)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if TEST_DATABASE_URL:
        return
    skip = pytest.mark.skip(reason="TEST_DATABASE_URL is not set (PostgreSQL)")
    for item in items:
        if "integration" in item.path.parts:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    assert TEST_DATABASE_URL
    if not TEST_DATABASE_URL.startswith("postgresql"):
        pytest.fail("integration tests require PostgreSQL, not another database")
    test_engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE transactions, budgets RESTART IDENTITY"))
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def db(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session


@pytest.fixture
def fixed_now() -> datetime:
    return FIXED_NOW


@pytest.fixture
def demo_budget(db: Session) -> Budget:
    return seed_demo_data(db, FIXED_NOW, DEMO_USER_ID)


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    def override_db() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_now] = lambda: FIXED_NOW
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
