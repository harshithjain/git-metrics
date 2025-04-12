from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import os
import pandas as pd
import subprocess
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

METRICS_DIR = "metrics_output"
OVERALL_METRICS_FILE = os.path.join(METRICS_DIR, "overall_metrics.csv")

@app.before_request
def log_request_info():
    print(f"Headers: {request.headers}")
    print(f"Body: {request.get_data()}")

@app.route("/metrics", methods=["GET"])
def get_metrics():
    """
    Serve the overall metrics as JSON.
    """
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    if not from_date or not to_date:
        return jsonify({"error": "Both 'from' and 'to' dates are required"}), 400

    try:
        # Parse the date range
        start_date = datetime.strptime(from_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_date = datetime.strptime(to_date, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1) - timedelta(seconds=1)

        # Call the github_metrics.py script with the date range
        print(f"Fetching metrics for date range: {start_date} to {end_date}")
        subprocess.run(
            ["python3", "github_metrics.py", "--from-date", from_date, "--to-date", to_date],
            check=True,
            text=True
        )

        # Ensure the metrics file exists after running the script
        if not os.path.exists(OVERALL_METRICS_FILE):
            return jsonify({"error": "Metrics file not found after script execution."}), 404

        # Read the metrics file
        df = pd.read_csv(OVERALL_METRICS_FILE)

        # If the Date column exists, filter based on the date range
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

        # Convert the data to JSON and return it
        metrics = df.to_dict(orient="records")
        return jsonify(metrics)
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return jsonify({"error": f"Failed to fetch metrics: {str(e)}"}), 500

@app.route('/refresh', methods=['POST'])
def refresh_metrics():
    """
    API endpoint to refresh metrics based on the date range provided by the UI.
    """
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    if not from_date or not to_date:
        return jsonify({"error": "Both 'from' and 'to' dates are required"}), 400

    try:
        # Parse the date range
        start_date = datetime.strptime(from_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_date = datetime.strptime(to_date, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1) - timedelta(seconds=1)

        # Call the github_metrics.py script with the date range
        print(f"Refreshing metrics for date range: {start_date} to {end_date}")
        result = subprocess.run(
            ["python3", "github_metrics.py", "--from-date", from_date, "--to-date", to_date],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({"error": f"Failed to refresh metrics: {result.stderr}"}), 500

        return jsonify({"message": "Metrics refreshed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)