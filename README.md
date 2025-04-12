# GitHub Repository Metrics

This project fetches various metrics from a GitHub repository and provides a **React-based UI** to display the metrics. The metrics include:
- Total lines of code
- Average commits per day
- Total coding days
- Commits per day for the last 7 days
- User-specific metrics like lines added, lines removed, and files changed

## Setup

### Backend Setup
1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the same directory with your GitHub credentials:
   ```
   GITHUB_TOKEN=your_github_personal_access_token
   GITHUB_REPO=owner/repo_name
   ```

   You can create a GitHub Personal Access Token by going to:
   - GitHub Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
   - Generate a new token with the `repo` scope.

3. Run the backend:
   ```bash
   python backend.py
   ```

   The backend will start on `http://localhost:5001` by default.

---

### UI Setup
The React-based UI displays the metrics in a table format and includes a **Refresh** button to regenerate the metrics.

1. Navigate to the `metrics-ui` directory:
   ```bash
   cd metrics-ui
   ```

2. Install the required dependencies:
   ```bash
   npm install
   ```

3. Start the React app:
   ```bash
   npm start
   ```

   The React app will start on `http://localhost:3000`.

---

### Usage

1. Open the React app in your browser:
   ```
   http://localhost:3000
   ```

2. The UI will display the metrics fetched from the backend.

3. To refresh the metrics, click the **Refresh Metrics** button. This will trigger the backend to regenerate the metrics and update the UI.

---

### Output

The script and UI provide the following outputs:
- **Overall Metrics**:
  - Total coding days
  - Total commits
  - Files changed
  - Lines added
  - Lines removed
  - Net lines changed
- **Commits Per Day**:
  - A breakdown of commits per day for all users.

The metrics are saved in the `metrics_output` directory as:
- `overall_metrics.csv`: Aggregated metrics for all users.
- `commits_per_day.csv`: Daily commit counts for all users.

---

### Notes
- The script uses the GitHub API, which has rate limits.
- Using a personal access token increases the rate limit.
- The React app fetches data from the backend running on `http://localhost:5001`.
- Ensure both the backend and frontend are running simultaneously for the UI to work.

---

### Directory Structure
```
/workspace/apsara/
├── backend.py                # Flask backend to fetch and refresh metrics
├── github_metrics.py         # Script to fetch metrics from GitHub
├── metrics_output/           # Directory where metrics CSV files are saved
├── metrics-ui/               # React-based UI for displaying metrics
│   ├── src/
│   │   ├── App.js            # Main React component
│   │   ├── index.js          # React entry point
│   │   └── ...
│   ├── public/
│   │   ├── index.html        # HTML entry point
│   │   └── ...
│   └── package.json          # React app dependencies and scripts
└── README.md                 # Project documentation
```

---

### Troubleshooting

#### CORS Issues
If you encounter CORS-related errors in the browser, ensure the backend is configured to allow requests from the React app:
- The backend should include the following configuration:
  ```python
  from flask_cors import CORS
  CORS(app, origins=["http://localhost:3000"])
  ```

#### Port Conflicts
If port `5001` is already in use, change the backend port in `backend.py`:
```python
app.run(debug=True, port=<new_port>)
```
Update the React app's API URLs to match the new port.

#### Node.js Version Issues
Ensure you are using Node.js version 14 or higher to run the React app. You can check your Node.js version with:
```bash
node -v
```

---

### Future Enhancements
- Add user authentication for accessing metrics.
- Provide downloadable reports directly from the UI.
- Add visualizations for metrics (e.g., charts for commits per day).
