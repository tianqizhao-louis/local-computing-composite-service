import os
import httpx

BREEDER_SERVICE_URL = os.getenv("BREEDER_SERVICE_URL")
PET_SERVICE_URL = os.getenv("PET_SERVICE_URL")


def is_breeder_route_present():
    url = os.environ.get("BREEDER_SERVICE_URL") or BREEDER_SERVICE_URL
    r = httpx.get(f"{url}/")
    return True if r.status_code == 200 else False


def is_pet_route_present():
    url = os.environ.get("PET_SERVICE_URL") or PET_SERVICE_URL
    r = httpx.get(f"{url}/")
    return True if r.status == 200 else False
