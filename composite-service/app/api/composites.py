from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Response
from app.api.models import (
    BreederIn,
    BreederOut,
    PetIn,
    PetOut,
    CompositeIn,
    CompositeOut,
    CompositeFilterParams,
    BreederListResponse,
    PetListResponse,
    Link,
    CompositeUpdateBoth,
)
from app.api import db_manager
from app.api.service import (
    is_breeder_route_present,
    is_pet_route_present,
    BREEDER_SERVICE_URL,
    PET_SERVICE_URL,
    CUSTOMER_SERVICE_URL,
)

import httpx
import os

import strawberry 
from strawberry.types import Info

composites = APIRouter()
URL_PREFIX = os.getenv("URL_PREFIX")


@composites.post("/", response_model=CompositeOut, status_code=201)
async def create_composite(payload: CompositeIn, response: Response):
    """POST is implemented asynchronously.

    - support operations on the sub-resources (POST)
    - support navigation paths.
    """

    # Check if the breeder service is available
    if not is_breeder_route_present:
        raise HTTPException(status_code=404, detail=f"Breeder service not found")

    # Check if the pet service is available
    if not is_pet_route_present:
        raise HTTPException(status_code=404, detail=f"Pet service not found")

    payload_dump = payload.model_dump()

    # Create a breeder record
    async with httpx.AsyncClient() as client:
        breeder_response = await client.post(
            f"{BREEDER_SERVICE_URL}/", json=payload_dump["breeder"]
        )
        breeder_id = str(breeder_response.json().get("id"))

        pet_responses = []
        for pet in payload_dump["pets"]:
            # Add breeder_id to the pet data
            pet["breeder_id"] = breeder_id

            pet_response = await client.post(f"{PET_SERVICE_URL}/", json=pet)
            pet_responses.append(pet_response.json())

    # Include Location header for the created resource
    composite_url = f"{URL_PREFIX}/composites/{breeder_id}/"
    response.headers["Location"] = composite_url

    # Include Link header for self and collection navigation
    response.headers["Link"] = (
        f'<{composite_url}>; rel="self", <{URL_PREFIX}/composites/>; rel="collection"'
    )

    breeder_response_json = breeder_response.json()

    # Include link sections in the response body
    response_data = CompositeOut(
        breeders=BreederListResponse(
            data=[
                BreederOut(
                    id=breeder_response_json.get("id"),
                    name=breeder_response_json.get("name"),
                    breeder_city=breeder_response_json.get("breeder_city"),
                    breeder_country=breeder_response_json.get("breeder_country"),
                    price_level=breeder_response_json.get("price_level"),
                    breeder_address=breeder_response_json.get("breeder_address"),
                )
            ],
            links=[
                Link(rel="self", href=f"{URL_PREFIX}/composites/"),
                Link(rel="collection", href=f"{URL_PREFIX}/composites/"),
            ],
        ),
        pets = PetListResponse(
            # iterate
            data=[
                PetOut(
                    id=pet["id"],
                    name=pet["name"],
                    type=pet["type"],
                    price=pet["price"],
                    breeder_id=pet["breeder_id"],
                    image_url=pet.get("image_url"),  # Include image_url here
                    links=pet["links"],
                )
                for pet in pet_responses
            ],
            links=[
                Link(rel="self", href=f"{URL_PREFIX}/composites/"),
                Link(rel="collection", href=f"{URL_PREFIX}/composites/"),
            ]
        ),
        links=[
            Link(rel="self", href=f"{URL_PREFIX}/composites/"),
            Link(rel="collection", href=f"{URL_PREFIX}/composites/"),
        ],
    )
    return response_data


@composites.get("/", response_model=CompositeOut)
async def get_composites(params: CompositeFilterParams = Depends()):
    """GET is implemented synchronously.

    - support operations on the sub-resources (GET)
    - support navigation paths, including query parameters.
    """

    if not is_breeder_route_present:
        raise HTTPException(status_code=404, detail=f"Breeder service not found")

    if not is_pet_route_present:
        raise HTTPException(status_code=404, detail=f"Pet service not found")

    try:
        breeder_url = f"{BREEDER_SERVICE_URL}/"

        breeder_params = []

        if params.breeder_limit:
            breeder_params.append(f"limit={params.breeder_limit}")
        if params.breeder_offset:
            breeder_params.append(f"offset={params.breeder_offset}")
        if params.breeder_city:
            breeder_params.append(f"breeder_city={params.breeder_city}")

        # If any query parameters exist, join them with "&" and append to the URL
        if breeder_params:
            breeder_url += "?" + "&".join(breeder_params)

        breeder_response = httpx.get(breeder_url)
        breeder_data = breeder_response.json()

        ##### PET SERVICE #####

        pet_url = f"{PET_SERVICE_URL}/"

        pet_params = []

        if params.pet_limit:
            pet_params.append(f"limit={params.pet_limit}")
        if params.pet_offset:
            pet_params.append(f"offset={params.pet_offset}")
        if params.type:
            pet_params.append(f"type={params.type}")

        # If any query parameters exist, join them with "&" and append to the URL
        if pet_params:
            pet_url += "?" + "&".join(pet_params)

        pet_response = httpx.get(pet_url)
        pet_data = pet_response.json()

        return {
            "breeders": breeder_data,
            "pets": pet_data,
            "links": [
                Link(rel="self", href=f"{URL_PREFIX}/composites/"),
                Link(rel="collection", href=f"{URL_PREFIX}/composites/"),
            ],
        }
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


@composites.get("/{id}/", response_model=BreederOut)
async def get_breeder(id: str):
    breeder = await db_manager.get_breeder(id)
    if not breeder:
        raise HTTPException(status_code=404, detail="Breeder not found")

    # Include link to self and collection in the response
    response_data = BreederOut(
        id=breeder["id"],
        name=breeder["name"],
        breeder_city=breeder["breeder_city"],
        breeder_country=breeder["breeder_country"],
        price_level=breeder["price_level"],
        breeder_address=breeder["breeder_address"],
        links=[
            Link(rel="self", href=f"{URL_PREFIX}/composites/{id}/"),
            Link(rel="collection", href=f"{URL_PREFIX}/composites/"),
        ],
    )
    return response_data


@composites.put("/both/{breeder_id}/{pet_id}/", response_model=None)
async def update_breeder_and_pet(
    breeder_id: str, pet_id: str, payload: CompositeUpdateBoth
):
    """PUT is implemented asynchronously.

    - support operations on the sub-resources (PUT)
    - support navigation paths.
    """
    if not is_breeder_route_present:
        raise HTTPException(status_code=404, detail=f"Breeder service not found")

    # Check if the pet service is available
    if not is_pet_route_present:
        raise HTTPException(status_code=404, detail=f"Pet service not found")

    # check if breeder and pet exists
    async with httpx.AsyncClient() as client:
        breeder_exist = await client.get(f"{BREEDER_SERVICE_URL}/{breeder_id}/")
        if breeder_exist.status_code != 200:
            raise HTTPException(status_code=404, detail="Breeder not found")

        pet_exist = await client.get(f"{PET_SERVICE_URL}/{pet_id}/")
        if pet_exist.status_code != 200:
            raise HTTPException(status_code=404, detail="Pet not found")

    # Update breeder
    async with httpx.AsyncClient() as client:
        breeder_payload_dump = payload.model_dump(exclude_unset=True)["breeder"]
        breeder_response = await client.put(
            f"{BREEDER_SERVICE_URL}/{breeder_id}/", json=breeder_payload_dump
        )
        pet_payload_dump = payload.model_dump(exclude_unset=True)["pet"]
        # Update pet
        pet_response = await client.put(
            f"{PET_SERVICE_URL}/{pet_id}/", json=pet_payload_dump
        )

    # Include link sections in the response body
    response_data = CompositeOut(
        breeders=BreederListResponse(
            data=[
                BreederOut(
                    id=breeder_response.json().get("id"),
                    name=breeder_response.json().get("name"),
                    breeder_city=breeder_response.json().get("breeder_city"),
                    breeder_country=breeder_response.json().get("breeder_country"),
                    price_level=breeder_response.json().get("price_level"),
                    breeder_address=breeder_response.json().get("breeder_address"),
                    links=breeder_response.json().get("links"),
                )
            ],
            links=[
                Link(rel="self", href=f"{URL_PREFIX}/composites/"),
                Link(rel="collection", href=f"{URL_PREFIX}/composites/"),
            ],
        ),
        pets=PetListResponse(
            data=[
                PetOut(
                    id=pet_response.json().get("id"),
                    name=pet_response.json().get("name"),
                    type=pet_response.json().get("type"),
                    price=pet_response.json().get("price"),
                    breeder_id=pet_response.json().get("breeder_id"),
                    links=pet_response.json().get("links"),
                )
            ],
        ),
        links=[
            Link(rel="self", href=f"{URL_PREFIX}/composites/"),
            Link(rel="collection", href=f"{URL_PREFIX}/composites/"),
        ],
    )
    return response_data


# # Helper function to generate breeder URL
# def generate_breeder_url(breeder_id: str):
#     return f"{URL_PREFIX}/composites/{breeder_id}/"


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
    async def breeder_pets_with_waitlist(self, breeder_id: str) -> Optional[Breeder]:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Fetch breeder information
            breeder_response = await client.get(f"{BREEDER_SERVICE_URL}/{breeder_id}")
            if breeder_response.status_code != 200:
                raise Exception("Breeder not found")
            breeder_data = breeder_response.json()

            # Fetch all pets and filter by breeder_id
            pets_response = await client.get(f"{PET_SERVICE_URL}")
            try:
                pets_response_data = pets_response.json()
                pets_data = [
                    pet for pet in pets_response_data.get("data", [])
                    if pet.get("breeder_id") == breeder_id
                ]
            except ValueError:
                raise Exception(f"Invalid JSON response from pet service: {pets_response.text}")

            # Fetch waitlist data for the breeder
            waitlist_response = await client.get(f"{CUSTOMER_SERVICE_URL}/breeder/{breeder_id}/waitlist")
            try:
                waitlist_data = waitlist_response.json()
                if not isinstance(waitlist_data, list):
                    raise Exception(f"Unexpected waitlist data format: {waitlist_data}")
            except ValueError:
                raise Exception(f"Invalid JSON response from waitlist service: {waitlist_response.text}")

            # Map waitlist entries to pets
            pet_waitlists = {}
            for entry in waitlist_data:
                pet_id = entry.get("pet_id")
                if pet_id:
                    if pet_id not in pet_waitlists:
                        pet_waitlists[pet_id] = []
                    pet_waitlists[pet_id].append(
                        WaitlistEntry(
                            id=f"{breeder_id}_{pet_id}_{entry['id']}",
                            consumer=Customer(
                                id=entry["id"],
                                name=entry["name"],
                                email=entry["email"]
                            ),
                            pet_id=pet_id,
                            breeder_id=breeder_id
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
                    waitlist=pet_waitlists.get(pet["id"], [])
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
                pets=pets_with_waitlist
            )



schema = strawberry.Schema(Query)
