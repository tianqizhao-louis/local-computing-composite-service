import requests
import random
import string

# URL of your API endpoint
url = "http://localhost:8080/api/v1/breeders/"

# Function to generate random dummy data
def generate_dummy_breeder():
    cities = ['New York', 'Los Angeles', 'Paris', 'Berlin', 'Tokyo', 'Moscow', 'Mumbai', 'Sydney', 'Rio de Janeiro', 'Cape Town']
    countries = ['USA', 'France', 'Germany', 'Japan', 'Russia', 'India', 'Australia', 'Brazil', 'South Africa']
    price_levels = ['low', 'medium', 'high']

    # Generate random name
    name = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=10))
    
    # Choose random city and country
    breeder_city = random.choice(cities)
    breeder_country = random.choice(countries)
    
    # Randomly select a price level
    price_level = random.choice(price_levels)
    
    # Generate a random breeder address
    breeder_address = f"{random.randint(1, 999)} {''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=10))} Street"

    return {
        "name": name,
        "breeder_city": breeder_city,
        "breeder_country": breeder_country,
        "price_level": price_level,
        "breeder_address": breeder_address
    }

# Loop to add 20 dummy data
for _ in range(20):
    dummy_breeder = generate_dummy_breeder()

    # Sending the POST request
    response = requests.post(url, json=dummy_breeder)

    # Checking if the request was successful
    if response.status_code == 201:
        print(f"Successfully added breeder: {dummy_breeder['name']}")
    else:
        print(f"Failed to add breeder: {dummy_breeder['name']} - Status Code: {response.status_code}")
