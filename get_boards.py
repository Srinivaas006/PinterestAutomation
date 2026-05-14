import requests
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN")

def get_boards():
    if not ACCESS_TOKEN:
        print("ERROR: PINTEREST_ACCESS_TOKEN not set in .env file")
        return

    url = "https://api.pinterest.com/v5/boards"
    headers = {
        "Authorization": "Bearer " + ACCESS_TOKEN
    }
    params = {"page_size": 100}

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    print("Response:", data)

    if "items" in data and len(data["items"]) > 0:
        print("\nYour Boards:")
        for board in data["items"]:
            print(f"Name: {board['name']}, ID: {board['id']}")
        print("\n👉 Copy your Board ID and paste it into your .env file as PINTEREST_BOARD_ID")
    else:
        print("\nNo boards found. Go to Pinterest and create a board first!")

if __name__ == "__main__":
    get_boards()