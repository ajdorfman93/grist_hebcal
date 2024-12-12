import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Replace with your Grist document's API key and URL
#GRIST_API_KEY = "your_grist_api_key"
GRIST_DOC_URL = "https://lakewoodluach.getgrist.com/api/docs/mfG1uWuVC9zwM1kapuvW1U"

# Headers for Grist API requests
HEADERS = {
 #   "Authorization": f"Bearer {GRIST_API_KEY}",
    "Content-Type": "application/json"
}

def fetch_times_top_record():
    """Fetch the top record from the Times table."""
    url = f"{GRIST_DOC_URL}/tables/Times/records"
    response = requests.get(url, headers=HEADERS)

    if response.ok:
        records = response.json().get("records", [])
        if records:
            # Return the record with the lowest ID (assumed top)
            return sorted(records, key=lambda r: r["id"])[0]
    else:
        raise ValueError(f"Failed to fetch Times records: {response.text}")

def update_times_record(record_id, html_content):
    """Update the Times table's top record."""
    url = f"{GRIST_DOC_URL}/tables/Times/records/{record_id}"
    payload = {"fields": {"HtmlContent": html_content}}
    response = requests.patch(url, headers=HEADERS, json=payload)

    if not response.ok:
        raise ValueError(f"Failed to update Times record: {response.text}")

@app.route("/update-times", methods=["POST"])
def update_times():
    """Endpoint to handle updates to the Times table."""
    data = request.json
    html_content = data.get("htmlContent")

    if not html_content:
        return jsonify({"error": "Missing htmlContent"}), 400

    try:
        # Fetch the top record in the Times table
        top_record = fetch_times_top_record()
        if top_record:
            record_id = top_record["id"]
            # Update the top record with new HtmlContent
            update_times_record(record_id, html_content)
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "No records in Times table"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
