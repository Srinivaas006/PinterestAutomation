import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import os
import json
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN")
BOARD_ID = os.getenv("PINTEREST_BOARD_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Pinterest Products")

def connect_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

def create_pin(title, description, link, image_url):
    url = "https://api.pinterest.com/v5/pins"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "board_id": BOARD_ID,
        "title": title,
        "description": description,
        "link": link,
        "media_source": {
            "source_type": "image_url",
            "url": image_url
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 201, response.text

def run():
    if not ACCESS_TOKEN or not BOARD_ID:
        print("ERROR: Missing PINTEREST_ACCESS_TOKEN or PINTEREST_BOARD_ID in environment")
        return

    print("Connecting to Google Sheets...")
    sheet = connect_google_sheets()

    rows = sheet.get_all_values()
    if len(rows) < 2:
        print("Sheet is empty or has no data rows.")
        return

    headers = rows[0]
    print(f"Columns found: {headers}")

    # Map your exact column names
    # A=title, B=price, C=image_url, D=description, E=affiliate_link, F=asin, G=added_on, H=posted, I=status
    try:
        status_col = headers.index("status") + 1    # Column I
        posted_col = headers.index("posted") + 1    # Column H
    except ValueError as e:
        print(f"ERROR: Column not found in sheet — {e}")
        print(f"Your columns: {headers}")
        return

    posted_count = 0
    skipped_count = 0

    for i, row in enumerate(rows[1:], start=2):
        # Pad short rows
        row += [""] * (len(headers) - len(row))
        row_dict = dict(zip(headers, row))

        # Skip if already posted — check BOTH 'posted' and 'status' columns
        posted_val = row_dict.get("posted", "").strip().lower()
        status_val = row_dict.get("status", "").strip().lower()

        if posted_val == "yes" or status_val == "posted":
            skipped_count += 1
            continue

        title       = row_dict.get("title", "").strip()
        image_url   = row_dict.get("image_url", "").strip()
        link        = row_dict.get("affiliate_link", "").strip()
        description = row_dict.get("description", "").strip()
        price       = row_dict.get("price", "").strip()
        asin        = row_dict.get("asin", "").strip()

        if not title or not image_url:
            print(f"Row {i}: Skipping — missing title or image_url")
            sheet.update_cell(i, status_col, "skipped - missing data")
            continue

        # Append price to description if available
        full_description = description
        if price:
            full_description = f"{description} | Price: {price}".strip(" |")

        print(f"Row {i}: Posting '{title}'...")
        success, response_text = create_pin(title, full_description, link, image_url)

        if success:
            sheet.update_cell(i, posted_col, "yes")       # Column H = yes
            sheet.update_cell(i, status_col, "posted")    # Column I = posted
            print(f"Row {i}: ✅ Posted '{title}'")
            posted_count += 1
        else:
            sheet.update_cell(i, status_col, f"failed: {response_text[:80]}")
            print(f"Row {i}: ❌ Failed '{title}' — {response_text}")

        time.sleep(2)  # Pinterest rate limit

    print(f"\nDone — {posted_count} posted, {skipped_count} already posted and skipped.")

if __name__ == "__main__":
    run()