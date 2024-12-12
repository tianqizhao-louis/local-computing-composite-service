import strawberry
from strawberry.types import Info
from typing import List, Optional
import httpx
from app.api.service import (
    BREEDER_SERVICE_URL,
    PET_SERVICE_URL,
    CUSTOMER_SERVICE_URL,
)

# Function to get the Authorization header
def get_auth_headers(info: Info) -> dict:
    """Retrieve the Authorization header from the request context."""
    auth_header = info.context.get("request").headers.get("Authorization")
    if not auth_header:
        raise Exception("Authorization header is required.")
    return {"Authorization": auth_header}


@strawberry.type
class Customer:
    id: str
    name: str
    email: str


@strawberry.type
class WaitlistEntry:
    id: str
    consumer: Customer
    pet_id: str
    breeder_id: str


@strawberry.type
class Pet:
    id: str
    name: str
    type: str
    price: Optional[float]
    breeder_id: str
    image_url: Optional[str]
    waitlist: List[WaitlistEntry]


@strawberry.type
class Breeder:
    id: str
    name: str
    email: str
    breeder_city: str
    breeder_country: str
    price_level: Optional[str]
    breeder_address: Optional[str]
    pets: List[Pet]


@strawberry.type
class Query:
    @strawberry.field
    async def breeder_pets_with_waitlist(self, breeder_id: str, info: Info) -> Optional[Breeder]:
        headers = get_auth_headers(info)

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Fetch breeder information
            breeder_response = await client.get(
                f"{BREEDER_SERVICE_URL}/{breeder_id}/", headers=headers
            )
            if breeder_response.status_code != 200:
                raise Exception("Breeder not found")
            breeder_data = breeder_response.json()

            # Fetch all pets and filter by breeder_id
            pets_response = await client.get(f"{PET_SERVICE_URL}/", headers=headers)
            try:
                pets_response_data = pets_response.json()
                pets_data = [
                    pet
                    for pet in pets_response_data.get("data", [])
                    if pet.get("breeder_id") == breeder_id
                ]
            except ValueError:
                raise Exception(
                    f"Invalid JSON response from pet service: {pets_response.text}"
                )

            # Fetch waitlist data for the breeder
            waitlist_response = await client.get(
                f"{CUSTOMER_SERVICE_URL}/breeder/{breeder_id}/waitlist", headers=headers
            )
            try:
                waitlist_data = waitlist_response.json()
                if not isinstance(waitlist_data, list):
                    raise Exception(f"Unexpected waitlist data format: {waitlist_data}")
            except ValueError:
                raise Exception(
                    f"Invalid JSON response from waitlist service: {waitlist_response.text}"
                )

            # Map waitlist entries to pets
            pet_waitlists = {pet["id"]: [] for pet in pets_data}  # Initialize waitlist for each pet
            for entry in waitlist_data:
                pet_id = entry.get("pet_id")
                if pet_id and pet_id in pet_waitlists:
                    pet_waitlists[pet_id].append(
                        WaitlistEntry(
                            id=entry["id"],
                            consumer=Customer(
                                id=entry["id"], name=entry["name"], email=entry["email"]
                            ),
                            pet_id=pet_id,
                            breeder_id=breeder_id,
                        )
                    )

            # Build pet data with waitlist
            pets_with_waitlist = [
                Pet(
                    id=pet["id"],
                    name=pet["name"],
                    type=pet["type"],
                    price=pet.get("price"),
                    image_url=pet.get("image_url"),
                    breeder_id=pet["breeder_id"],
                    waitlist=pet_waitlists.get(pet["id"], []),
                )
                for pet in pets_data
            ]

            # Return breeder with pets and waitlist
            return Breeder(
                id=breeder_data["id"],
                name=breeder_data["name"],
                email=breeder_data["email"],
                breeder_city=breeder_data["breeder_city"],
                breeder_country=breeder_data["breeder_country"],
                price_level=breeder_data.get("price_level"),
                breeder_address=breeder_data.get("breeder_address"),
                pets=pets_with_waitlist,
            )


schema = strawberry.Schema(Query)

