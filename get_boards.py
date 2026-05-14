import requests

ACCESS_TOKEN = "pina_AMAXN4QXAANT6BYAGCAOWD6FBA7CLHQBQBIQC4GQAXGZ47MAGZZJQUQJJ4RK76HQTV3WFH74CBWVTPNTPCECVT3SU5XRY4YA"

def get_boards():
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
    else:
        print("\nNo boards found. Go to Pinterest and create a board first!")

if __name__ == "__main__":
    get_boards()