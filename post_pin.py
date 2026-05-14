import requests
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

ACCESS_TOKEN = "pina_AMAXN4QXAANT6BYAGCAOWDYOH3SBFHQBQBIQCG5CBZXTPWI2N7NSK7IY5JKB3MXBIUG7YYUH3M3WP2ETEJ4Z3SWM2NXJCVYA"
SHEET_NAME = "Pinterest Products"
BOARD_ID = "YOUR_BOARD_ID"

def connect_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

def load_from_sheet():
    sheet = connect_google_sheets()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def create_pin(board_id, title, description, link, image_url):
    url = "https://api.pinterest.com/v5/pins"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "board_id": board_id,
        "title": title,
        "description": description,
        "link": link,
        "media_source": {
            "source_type": "image_url",
            "url": image_url
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"[OK] Posted: {title}")
        return True
    else:
        print(f"[FAIL] {title} - {response.text}")
        return False

def post_all_pins():
    print("Loading products from Google Sheets...")
    try:
        df = load_from_sheet()
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print(f"Found {len(df)} products\n")
    success_count = 0
    failed_count = 0

    for index, row in df.iterrows():
        title = row.get('title', '')
        image_url = row.get('image_url', '')
        link = row.get('affiliate_link', '')
        description = row.get('description', '')

        if create_pin(BOARD_ID, title, description, link, image_url):
            success_count += 1
            time.sleep(2)
        else:
            failed_count += 1
        time.sleep(1)

    print(f"\n{'='*50}")
    print(f"COMPLETED!")
    print(f"Success: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"{'='*50}")

if __name__ == "__main__":
    print("Pinterest Auto-Poster")
    print("=" * 50)
    post_all_pins()