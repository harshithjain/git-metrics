from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import os
import pandas as pd
import subprocess

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
    if not os.path.exists(OVERALL_METRICS_FILE):
        response = make_response(jsonify({"error": "Metrics file not found"}), 404)
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        return response

    try:
        df = pd.read_csv(OVERALL_METRICS_FILE)
        response = make_response(jsonify(df.to_dict(orient="records")))
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        return response
    except Exception as e:
        response = make_response(jsonify({"error": str(e)}), 500)
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        return response

@app.route("/refresh", methods=["POST"])
def refresh_metrics():
    """
    Run the Python script to refresh the metrics.
    """
    try:
        # Run the Python script to generate metrics
        subprocess.run(["python3", "github_metrics.py"], check=True)
        response = make_response(jsonify({"message": "Metrics refreshed successfully"}))
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        return response
    except subprocess.CalledProcessError as e:
        response = make_response(jsonify({"error": f"Failed to refresh metrics: {str(e)}"}), 500)
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        return response

if __name__ == "__main__":
    app.run(debug=True, port=5001)