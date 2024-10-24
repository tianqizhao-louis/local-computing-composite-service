import pytest


@pytest.mark.asyncio
async def test_database_connection(test_database):
    """Test that we're using SQLite in memory database"""
    # Check if the connection is SQLite
    assert str(test_database.url).startswith("sqlite:")
    assert "memory" in str(test_database.url)

    # Verify we can execute a simple query
    query = (
        "SELECT 1;"  # Changed to a simpler query that works in both SQLite and Postgres
    )
    result = await test_database.fetch_one(query)
    assert result is not None


@pytest.fixture
def sample_breeder():
    return {
        "name": "Test Breeder",
        "breeder_city": "Test City",
        "breeder_country": "Test Country",
        "price_level": "$$$",
        "breeder_address": "123 Test Street",
    }


@pytest.fixture
def updated_breeder():
    return {
        "name": "Updated Breeder",
        "breeder_city": "Updated City",
        "breeder_country": "Updated Country",
        "price_level": "$$",
        "breeder_address": "456 Updated Street",
    }


@pytest.mark.asyncio
async def test_get_breeders(test_client):
    """Test GET /api/v1/breeders/ endpoint"""
    response = test_client.get("/api/v1/breeders/")
    assert response.status_code == 200
    assert response.json()["links"] is not None


@pytest.mark.asyncio
async def test_create_and_get_breeder(test_client, sample_breeder):
    """Test POST and GET /api/v1/breeders/ endpoints"""
    # Create a breeder
    response = test_client.post("/api/v1/breeders/", json=sample_breeder)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == sample_breeder["name"]
    assert data["breeder_city"] == sample_breeder["breeder_city"]
    assert data["breeder_country"] == sample_breeder["breeder_country"]
    assert data["price_level"] == sample_breeder["price_level"]
    assert data["breeder_address"] == sample_breeder["breeder_address"]
    assert "id" in data

    # Verify it was created
    get_response = test_client.get("/api/v1/breeders/")
    assert get_response.status_code == 200
    assert len(get_response.json()["data"]) == 1

    # Get specific breeder
    get_one_response = test_client.get(f"/api/v1/breeders/{data['id']}")
    assert get_one_response.status_code == 200
    assert get_one_response.json() == data


@pytest.mark.asyncio
async def test_update_breeder(test_client, sample_breeder, updated_breeder):
    """Test PUT /api/v1/breeders/{id} endpoint"""
    # First create a breeder
    create_response = test_client.post("/api/v1/breeders/", json=sample_breeder)
    assert create_response.status_code == 201
    breeder_id = create_response.json()["id"]

    # Update the breeder
    update_response = test_client.put(
        f"/api/v1/breeders/{breeder_id}", 
        json=updated_breeder
    )
    assert update_response.status_code == 200
    
    updated_data = update_response.json()
    assert updated_data["id"] == breeder_id
    assert updated_data["name"] == updated_breeder["name"]
    assert updated_data["breeder_city"] == updated_breeder["breeder_city"]
    assert updated_data["breeder_country"] == updated_breeder["breeder_country"]
    assert updated_data["price_level"] == updated_breeder["price_level"]
    assert updated_data["breeder_address"] == updated_breeder["breeder_address"]

    # Verify the update
    get_response = test_client.get(f"/api/v1/breeders/{breeder_id}")
    assert get_response.status_code == 200
    assert get_response.json() == updated_data


@pytest.mark.asyncio
async def test_update_breeder_invalid_id(test_client, updated_breeder):
    """Test PUT with invalid breeder ID"""
    response = test_client.put(
        "/api/v1/breeders/invalid-id",
        json=updated_breeder
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_breeder(test_client, sample_breeder):
    """Test DELETE /api/v1/breeders/{id} endpoint"""
    # First create a breeder
    create_response = test_client.post("/api/v1/breeders/", json=sample_breeder)
    assert create_response.status_code == 201
    breeder_id = create_response.json()["id"]

    # Delete the breeder
    delete_response = test_client.delete(f"/api/v1/breeders/{breeder_id}")
    assert delete_response.status_code == 200

    # Verify the breeder was deleted
    get_response = test_client.get(f"/api/v1/breeders/{breeder_id}")
    assert get_response.status_code == 404

    # Verify the breeder is not in the list
    list_response = test_client.get("/api/v1/breeders/")
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 0


@pytest.mark.asyncio
async def test_delete_breeder_invalid_id(test_client):
    """Test DELETE with invalid breeder ID"""
    response = test_client.delete("/api/v1/breeders/invalid-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_breeder_invalid_data(test_client):
    """Test GET with invalid data"""
    response = test_client.get("/api/v1/breeders/123")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cleanup_between_tests(test_client, test_database):
    """Verify that the database is clean between tests"""
    # This should be empty as it's a fresh database
    response = test_client.get("/api/v1/breeders/")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 0
