from pydantic import BaseModel
from typing import List, Optional


# Model to represent a hypermedia link
class Link(BaseModel):
    rel: str
    href: str


class BreederIn(BaseModel):
    name: str
    breeder_city: str
    breeder_country: str
    price_level: str
    breeder_address: str


class BreederOut(BreederIn):
    id: str
    # Add links field to support the HATEOAS concept
    links: Optional[List[Link]] = None


class BreederListResponse(BaseModel):
    data: List[BreederOut]
    links: Optional[List[Link]] = None


class PetIn(BaseModel):
    name: str
    type: str
    price: float
    breeder_id: str


class PetInAdd(BaseModel):
    name: str
    type: str
    price: float


class PetOut(PetIn):
    id: str
    links: Optional[List[Link]] = None


class PetListResponse(BaseModel):
    data: List[PetOut]
    links: Optional[List[Link]] = None


class CompositeIn(BaseModel):
    breeder: BreederIn
    pets: List[PetInAdd]


class CompositeOut(BaseModel):
    breeders: BreederListResponse
    pets: PetListResponse
    links: Optional[List[Link]] = None


class CompositeFilterParams(BaseModel):
    breeder_limit: Optional[int] = None
    breeder_offset: Optional[int] = None
    pet_limit: Optional[int] = None
    pet_offset: Optional[int] = None
    breeder_city: Optional[str] = None
    type: Optional[str] = None


class BreederUpdate(BaseModel):
    name: Optional[str] = None
    breeder_city: Optional[str] = None
    breeder_country: Optional[str] = None
    price_level: Optional[str] = None
    breeder_address: Optional[str] = None


class PetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    price: Optional[float] = None
    breeder_id: Optional[str] = None


class CompositeUpdateBoth(BaseModel):
    breeder: Optional[BreederUpdate] = None
    pet: Optional[PetUpdate] = None


# class BreederFilterParams(BaseModel):
#     limit: Optional[int] = None
#     offset: Optional[int] = None
#     breeder_city: Optional[str] = None


# class BreederDelayResponse(BaseModel):
#     name: str
#     breeder_city: str
#     breeder_country: str
#     price_level: str
#     breeder_address: str
#     status_url: str
#     # Add links field for HATEOAS support
#     links: Optional[List[Link]] = None


# class BreederListResponse(BaseModel):
#     data: List[BreederOut]
#     links: Optional[List[Link]] = None
