import requests

url = "https://api.elevenlabs.io/v1/user/subscription"
headers = {
    "xi-api-key": "63e5b5c2d32d0b220d934abe009a4ec428b1eb92ae4f4aa127451d105895a81b"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    
    # Extract credit metrics
    used_characters = data.get("character_count")
    total_limit = data.get("character_limit")
    remaining_credits = total_limit - used_characters
    
    print(f"Used Credits/Characters: {used_characters}")
    print(f"Total Limit: {total_limit}")
    print(f"Remaining Credits: {remaining_credits}")
else:
    print(f"Failed to fetch data. Error code: {response.status_code}")
