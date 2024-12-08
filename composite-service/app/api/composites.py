from typing import List, Dict, Optional
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    BackgroundTasks,
    Response,
    Request,
)
from fastapi.security import HTTPBearer
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

# from app.api.pubsub_manager import PubSubManager
from google.cloud import workflows_v1
from google.cloud.workflows import executions_v1
from google.cloud.workflows.executions_v1 import Execution
from google.cloud.workflows.executions_v1.types import executions
from google.oauth2 import service_account
from google.cloud.pubsub_v1 import PublisherClient, SubscriberClient


from app.api.auth import get_current_user
from app.api.middleware import get_correlation_id
import httpx
import os
import logging
import asyncio
import json
import uuid
import time
import boto3


composites = APIRouter()

URL_PREFIX = os.getenv("URL_PREFIX")


@composites.post("/", response_model=CompositeOut, status_code=201)
async def create_composite(
    payload: CompositeIn,
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    """POST is implemented asynchronously.

    - support operations on the sub-resources (POST)
    - support navigation paths.

    Protected by Bearer
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
        headers = {
            "X-Correlation-ID": get_correlation_id(),
            "Authorization": f"{request.headers.get('Authorization')}",
        }
        breeder_response = await client.post(
            f"{BREEDER_SERVICE_URL}/", json=payload_dump["breeder"], headers=headers
        )
        breeder_id = str(breeder_response.json().get("id"))

        pet_responses = []
        for pet in payload_dump["pets"]:
            # Add breeder_id to the pet data
            pet["breeder_id"] = breeder_id

            pet_response = await client.post(
                f"{PET_SERVICE_URL}/", json=pet, headers=headers
            )
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
                    email=breeder_response_json.get("email"),
                )
            ],
            links=[
                Link(rel="self", href=f"{URL_PREFIX}/composites/"),
                Link(rel="collection", href=f"{URL_PREFIX}/composites/"),
            ],
        ),
        pets=PetListResponse(
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
            ],
        ),
        links=[
            Link(rel="self", href=f"{URL_PREFIX}/composites/"),
            Link(rel="collection", href=f"{URL_PREFIX}/composites/"),
        ],
    )
    return response_data


@composites.get("/", response_model=CompositeOut)
async def get_composites(request: Request, params: CompositeFilterParams = Depends()):
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

        headers = {
            "X-Correlation-ID": get_correlation_id(),
            "Authorization": f"{request.headers.get('Authorization')}",
        }
        breeder_response = httpx.get(breeder_url, headers=headers)
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

        pet_response = httpx.get(pet_url, headers=headers)
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


@composites.get("/breeders/id/{id}/")
async def composite_get_breeder(id: str):
    """Pub/Sub implementation for composite service"""

    pubsub_credentials = service_account.Credentials.from_service_account_file(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PUBSUB"),
        scopes=["https://www.googleapis.com/auth/pubsub"],
    )
    correlation_id = str(uuid.uuid4())
            
    try:
        publisher = PublisherClient(credentials=pubsub_credentials)
        project_name = os.getenv("GCP_PROJECT_ID")
        request_topic = os.getenv("REQUEST_TOPIC")
        topic_name = f"projects/{project_name}/topics/{request_topic}"
        message_data = {
            "breeder_id": str(id),
            "correlation_id": correlation_id,
        }
        data = json.dumps(message_data).encode("utf-8")

        # Log for debugging
        # print(f"Publishing to topic: {topic_name}")
        # print(f"Message data: {message_data}")

        # Publish and await the result
        future = publisher.publish(topic_name, data)
        message_id = future.result()
        print(f"Message published with ID: {message_id}")
    except Exception as e:
        print(f"Error while publishing: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish message")
    
    try:
        print("About to initialize SubscriberClient")
        # Use SubscriberClient as a synchronous context manager
        with SubscriberClient(credentials=pubsub_credentials) as subscriber:
            response_sub = os.getenv("RESPONSE_SUBSCRIPTION_NAME")
            subscription_name = f"projects/{project_name}/subscriptions/{response_sub}"
            print(f"Listening to subscription: {subscription_name}")

            timeout = 30  # seconds
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                print(f"Polling messages from subscription: {subscription_name}")
                try:
                    # Pull messages from the subscription
                    response = subscriber.pull(
                        request={"subscription": subscription_name, "max_messages": 10}
                    )
                    print(f"Received {len(response.received_messages)} messages")

                    for msg in response.received_messages:
                        print(f"Raw message: {msg.message.data}")
                        message_data = json.loads(msg.message.data.decode("utf-8"))
                        print(f"Decoded message data: {message_data}")

                        # Check for matching correlation_id
                        if message_data.get("correlation_id") == correlation_id:
                            print(f"Correlation ID matched: {correlation_id}")

                            # Acknowledge the message
                            subscriber.acknowledge(
                                request={
                                    "subscription": subscription_name,
                                    "ack_ids": [msg.ack_id],
                                }
                            )
                            return message_data["breeder_data"]

                except Exception as e:
                    print(f"Error during message polling: {e}")

                await asyncio.sleep(1)

            print("Timeout reached while waiting for response")
            raise HTTPException(status_code=504, detail="Response timed out")
    except Exception as e:
        print(f"Error initializing SubscriberClient or processing messages: {e}")
        raise



@composites.get("/customers/id/{id}/")
async def composite_get_customer(id: str):
    """Workflow implementation for composite service"""
    try:
        workflow_credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS_WORKFLOW"),
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        project_name = os.getenv("GCP_PROJECT_ID")
        location = "us-central1"
        workflow_id = "composite-to-customer"

        execution_client = executions_v1.ExecutionsAsyncClient(
            credentials=workflow_credentials
        )
        workflow_client = workflows_v1.WorkflowsClient(credentials=workflow_credentials)
        parent = workflow_client.workflow_path(project_name, location, workflow_id)

        if os.getenv("FASTAPI_ENV") != "production":
            workflow_args = {
                "customer_id": id,
                "customer_service_url": "https://customer-661348528801.us-central1.run.app/api/v1/customers",
            }
        else:
            workflow_args = {
                "customer_id": id,
                "customer_service_url": CUSTOMER_SERVICE_URL,
            }

        execution = await execution_client.create_execution(
            request={
                "parent": parent,
                "execution": {"argument": json.dumps(workflow_args)},
            }
        )
        logging.info(f"Created execution: {execution.name}")

        # Add timeout to prevent infinite loops
        start_time = time.time()
        timeout = 30  # 30 seconds timeout

        while True:
            execution = await execution_client.get_execution(
                request={"name": execution.name}
            )

            if execution.state in [Execution.State.SUCCEEDED, Execution.State.FAILED]:
                break

            if time.time() - start_time > timeout:
                raise HTTPException(
                    status_code=408, detail="Workflow execution timed out"
                )

            await asyncio.sleep(1)  # Add delay between checks

        if execution.state == Execution.State.FAILED:
            raise HTTPException(
                status_code=500, detail=f"Workflow execution failed: {execution.error}"
            )

        result = json.loads(execution.result)
        if result.get("code") != 200:
            raise HTTPException(
                status_code=result["code"],
                detail=result.get("message", "Unknown error"),
            )

        return result["data"]

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, detail="Invalid JSON response from workflow"
        )
    except Exception as e:
        logging.error(f"Workflow execution error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Workflow execution error: {str(e)}"
        )


@composites.put("/both/{breeder_id}/{pet_id}/", response_model=None)
async def update_breeder_and_pet(
    breeder_id: str, pet_id: str, payload: CompositeUpdateBoth, request: Request
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
        headers = {
            "X-Correlation-ID": get_correlation_id(),
            "Authorization": f"{request.headers.get('Authorization')}",
        }

        breeder_exist = await client.get(f"{BREEDER_SERVICE_URL}/{breeder_id}/", headers=headers)
        if breeder_exist.status_code != 200:
            raise HTTPException(status_code=404, detail="Breeder not found")

        pet_exist = await client.get(f"{PET_SERVICE_URL}/{pet_id}/", headers=headers)
        if pet_exist.status_code != 200:
            raise HTTPException(status_code=404, detail="Pet not found")

    # Update breeder
    async with httpx.AsyncClient() as client:
        breeder_payload_dump = payload.model_dump(exclude_unset=True)["breeder"]
        breeder_response = await client.put(
            f"{BREEDER_SERVICE_URL}/{breeder_id}/", json=breeder_payload_dump, headers=headers
        )
        pet_payload_dump = payload.model_dump(exclude_unset=True)["pet"]
        # Update pet
        pet_response = await client.put(
            f"{PET_SERVICE_URL}/{pet_id}/", json=pet_payload_dump, headers=headers
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
                    email=breeder_response.json().get("email"),
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


# Function to Fetch Information from Individual Services
async def get_email_data(breeder_id: str, pet_id: str, customer_id: str, auth_header: str):
    """Fetch data from individual services asynchronously to construct the email payload."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {}
            if auth_header:
                headers["Authorization"] = auth_header  # Pass the auth header

            # Fetch breeder information
            breeder_url = f"{BREEDER_SERVICE_URL}/{breeder_id}/"
            breeder_response = await client.get(breeder_url, headers=headers)
            breeder_response.raise_for_status()
            breeder_data = breeder_response.json()

            # Fetch pet information
            pet_url = f"{PET_SERVICE_URL}/{pet_id}/"
            pet_response = await client.get(pet_url, headers=headers)
            pet_response.raise_for_status()
            pet_data = pet_response.json()

            # Fetch customer information
            customer_url = f"{CUSTOMER_SERVICE_URL}/{customer_id}/"
            customer_response = await client.get(customer_url, headers=headers)
            customer_response.raise_for_status()
            customer_data = customer_response.json()

            # Validate the fetched data
            breeder_email = breeder_data.get("email")
            customer_name = customer_data.get("name")
            customer_email = customer_data.get("email")
            pet_name = pet_data.get("name")

            if not all([breeder_email, customer_name, customer_email, pet_name]):
                raise ValueError("Missing required data for email construction")

            # Construct the email data
            email_data = {
                "breeder_email": breeder_email,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "pet_name": pet_name,
                "pet_id": pet_id,
            }
            return email_data

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500, detail=f"Error fetching data from services: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Service returned an error: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Unexpected error occurred: {str(e)}"
            )



# AWS Lambda settings
LAMBDA_FUNCTION_NAME = os.getenv("LAMBDA_FUNCTION_NAME", "SendEmailFunction")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize AWS Lambda client
lambda_client = boto3.client("lambda", region_name=AWS_REGION)


def invoke_lambda(email_data: dict):
    """Trigger the AWS Lambda function with the necessary payload using boto3."""
    try:
        # Wrap the email_data in a "body" key, as expected by the Lambda handler
        payload = {"body": json.dumps(email_data)}  # Convert to JSON string

        # Log the payload for debugging

        # Invoke the Lambda function synchronously
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),  # Send the wrapped payload
        )

        # Parse Lambda response
        response_payload = json.loads(response["Payload"].read())

        # Check for error in Lambda response
        if response_payload.get("statusCode") != 200:
            error_message = response_payload.get("body", "Unknown error")
            return {
                "status": "failure",
                "message": "Lambda function invocation failed",
                "details": error_message,
            }
        return response_payload
    except Exception as e:
        return {
            "status": "failure",
            "message": "Error invoking Lambda function",
            "details": str(e),
        }


@composites.post("/webhook", status_code=200)
async def handle_webhook(request: Request):
    """Handle incoming webhook from the customer server."""
    try:
        # Parse the webhook payload
        event_data = await request.json()

        # Validate required fields
        breeder_id = event_data.get("breeder_id")
        pet_id = event_data.get("pet_id")
        customer_id = event_data.get("consumer_id")
        if not all([breeder_id, pet_id, customer_id]):
            raise HTTPException(
                status_code=400, detail="Missing required fields in webhook payload"
            )
        
        auth_header = request.headers.get("Authorization")

        # Fetch necessary email data
        email_data = await get_email_data(breeder_id, pet_id, customer_id, auth_header)
        

        # Validate the email data
        required_keys = [
            "breeder_email",
            "customer_name",
            "customer_email",
            "pet_name",
            "pet_id",
        ]
        missing_keys = [
            key for key in required_keys if key not in email_data or not email_data[key]
        ]
        if missing_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid email data, missing keys: {missing_keys}",
            )

        # Trigger AWS Lambda function
        try:
            lambda_response = invoke_lambda(email_data)
            return {"status": "success", "lambda_response": lambda_response}
        except Exception as e:
            return {
                "status": "partial_success",
                "message": "Webhook processed, but Lambda invocation failed",
                "error": str(e),
            }

    except HTTPException as e:
        raise e
    except Exception as e:
        return {
            "status": "failure",
            "message": "Internal server error occurred",
            "details": str(e),
        }
