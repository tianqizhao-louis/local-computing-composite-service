# from typing import Optional
# from app.api.models import BreederIn, BreederOut
# from app.api.db import breeders, database


# async def add_breeder(payload: BreederIn, breeder_id: str):
#     query = breeders.insert().values(id=breeder_id, **payload.model_dump())

#     return await database.execute(query=query)


# async def get_all_breeders(
#     breeder_city: Optional[str], limit: Optional[int], offset: Optional[int]
# ):
#     query = breeders.select()

#     if breeder_city:
#         query = query.where(breeders.c.breeder_city == breeder_city)

#     if limit is not None:
#         query = query.limit(limit)

#     if offset is not None:
#         query = query.offset(offset)

#     return await database.fetch_all(query)


# async def get_breeder(id):
#     query = breeders.select().where(breeders.c.id == id)
#     return await database.fetch_one(query=query)


# async def delete_breeder(id: int):
#     query = breeders.delete().where(breeders.c.id == id)
#     return await database.execute(query=query)


# async def update_breeder(id: int, payload: BreederIn):
#     query = breeders.update().where(breeders.c.id == id).values(**payload.model_dump())
#     return await database.execute(query=query)


# async def delete_all_breeders():
#     query = breeders.delete()  # This will delete all records from the breeders table
#     return await database.execute(query=query)
