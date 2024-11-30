import os
import httpx

BREEDER_SERVICE_URL = os.getenv("BREEDER_SERVICE_URL")
PET_SERVICE_URL = os.getenv("PET_SERVICE_URL")
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL")


def is_breeder_route_present():
    url = os.environ.get("BREEDER_SERVICE_URL") or BREEDER_SERVICE_URL
    r = httpx.get(f"{url}/")
    return True if r.status_code == 200 else False


def is_pet_route_present():
    url = os.environ.get("PET_SERVICE_URL") or PET_SERVICE_URL
    r = httpx.get(f"{url}/")
    return True if r.status == 200 else False

def is_customer_route_present():
    """Check if customer service is available."""
    try:
        url = os.environ.get("CUSTOMER_SERVICE_URL") or CUSTOMER_SERVICE_URL
        r = httpx.get(f"{url}/", timeout=5)
        return r.status_code == 200
    except httpx.RequestError as e:
        print(f"Customer service unavailable: {e}")
        return False
