# import pytest
# from fastapi.testclient import TestClient
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# from app.main import app  # Assuming your FastAPI app is in app/main.py
# from app.api.db_manager import database
# from app.api.db_manager import metadata

# # Use an in-memory SQLite database for testing
# DATABASE_URL = "sqlite:///:memory:"

# # Create a new test engine and bind it to metadata
# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# @pytest.fixture(scope="function", autouse=True)
# async def setup_db():
#     """Set up the database before each test."""
#     # Create all tables
#     metadata.create_all(bind=engine)
#     # Ensure the connection to the database is established
#     await database.connect()
#     yield
#     # Teardown: Drop all tables after the test
#     await database.disconnect()
#     metadata.drop_all(bind=engine)

# client = TestClient(app)

# def test_create_breeder():
#     """Test creating a new breeder"""
#     test_breeder = {
#         "name": "Test Breeder",
#         "breeder_city": "Test City",
#         "breeder_country": "Test Country",
#         "price_level": "Medium",
#         "breeder_address": "123 Test Street"
#     }

#     response = client.post("/api/v1/breeders/", json=test_breeder)
#     assert response.status_code == 200
#     assert response.json()["name"] == test_breeder["name"]

# def test_get_breeders():
#     """Test getting all breeders"""
#     response = client.get("/api/v1/breeders/")
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
