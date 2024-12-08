from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.composites import composites
from app.api.auth import auth

# from app.api.db import metadata, database, engine
from app.api.middleware import LoggingMiddleware, JWTMiddleware
from contextlib import asynccontextmanager

# code for graphql
from strawberry.fastapi import GraphQLRouter
from app.api.graphql import schema

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup code: connect to the database
#     await database.connect()
#     yield
#     # Shutdown code: disconnect from the database
#     await database.disconnect()


# metadata.create_all(engine)

app = FastAPI(
    openapi_url="/api/v1/composites/openapi.json",
    docs_url="/api/v1/composites/docs",
    # lifespan=lifespan  # Use lifespan event handler
)

origins = [
    "*",
    # "http://localhost",
    # "http://localhost:3000",
    # "http://34.120.15.105",
    # "http://34.72.253.184:8000", #breeder
    # "http://35.232.191.145:8002", #pets
    # "http://34.72.253.184",
    # "http://35.232.191.145",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    JWTMiddleware,
    excluded_paths=[
        "/api/v1/auth",
        "/api/v1/composites/openapi.json",
        "/api/v1/composites/docs",
        "/api/v1/graphql",
    ],
)

app.include_router(composites, prefix="/api/v1/composites", tags=["composites"])
app.include_router(auth, prefix="/api/v1/auth", tags=["auth"])

# Add GraphQL route
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/api/v1/graphql", tags=["graphql"])
