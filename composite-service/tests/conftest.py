# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from databases import Database
from app.api.db import metadata, engine
import os

# Override DATABASE_URI for testing
TEST_DATABASE_URL = "sqlite:///file:mem.db?mode=memory&cache=shared&uri=true"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    # Create all tables before running tests
    metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def test_database():
    """Create a test database instance"""
    database = Database(TEST_DATABASE_URL)
    return database


@pytest.fixture(autouse=True)
async def override_dependency(monkeypatch, test_database, test_engine):
    """Override the database dependency"""
    from app.api import db

    # Create tables if they don't exist
    metadata.create_all(test_engine)

    monkeypatch.setattr(db, "database", test_database)
    monkeypatch.setattr(db, "DATABASE_URI", TEST_DATABASE_URL)
    monkeypatch.setattr(db, "engine", test_engine)

    await test_database.connect()
    yield
    await test_database.disconnect()


@pytest.fixture
def test_app(override_dependency):
    """Create a test FastAPI application"""
    from app.main import app

    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client"""
    return TestClient(test_app)


@pytest.fixture(autouse=True)
async def cleanup_database(test_database):
    """Clean up the database between tests"""
    yield
    await test_database.execute("DELETE FROM breeders")
