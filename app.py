from flask import Flask, jsonify
import requests
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN")
BOARD_ID = os.getenv("PINTEREST_BOARD_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Pinterest Products")

def connect_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # On Render, credentials come from an env variable (not a file)
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # Fallback for local development
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

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
    return response.status_code == 201, response.text

@app.route("/")
def home():
    return jsonify({"status": "Pinterest Bot is running", "usage": "POST /run to start posting"})

@app.route("/run", methods=["POST"])
def run_poster():
    if not ACCESS_TOKEN:
        return jsonify({"error": "PINTEREST_ACCESS_TOKEN not set"}), 500
    if not BOARD_ID or BOARD_ID == "your_board_id_here":
        return jsonify({"error": "PINTEREST_BOARD_ID not set"}), 500

    try:
        sheet = connect_google_sheets()
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
    except Exception as e:
        return jsonify({"error": f"Google Sheets error: {str(e)}"}), 500

    results = []
    for index, row in df.iterrows():
        title = row.get("title", "")
        image_url = row.get("image_url", "")
        link = row.get("affiliate_link", "")
        description = row.get("description", "")

        if not title or not image_url:
            results.append({"row": index + 1, "status": "skipped", "reason": "missing title or image_url"})
            continue

        success, response_text = create_pin(BOARD_ID, title, description, link, image_url)
        results.append({
            "row": index + 1,
            "title": title,
            "status": "ok" if success else "failed",
            "detail": response_text if not success else ""
        })
        time.sleep(2)

    success_count = sum(1 for r in results if r["status"] == "ok")
    failed_count = sum(1 for r in results if r["status"] == "failed")

    return jsonify({
        "total": len(df),
        "success": success_count,
        "failed": failed_count,
        "results": results
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)