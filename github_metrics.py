from github import Github
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import argparse
import shutil

# Load environment variables
load_dotenv()

METRICS_DIR = "metrics_output"
OVERALL_METRICS_FILE = os.path.join(METRICS_DIR, "overall_metrics.csv")

def clean_output_directory(output_dir):
    """
    Clean the output directory by deleting all its contents.

    Args:
        output_dir: Directory to clean.
    """
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)  # Remove the directory and all its contents
    os.makedirs(output_dir, exist_ok=True)  # Recreate the directory

def get_recent_branches(repo, start_date, end_date):
    """
    Fetch branches updated within the specified date range.

    Args:
        repo: GitHub repository object.
        start_date: Start date for filtering activity.
        end_date: End date for filtering activity.

    Returns:
        List of branch objects updated within the specified time frame.
    """
    recent_branches = []

    for branch in repo.get_branches():
        try:
            # Get the last commit date for the branch
            last_commit = branch.commit.commit.author.date
            if start_date <= last_commit <= end_date:
                recent_branches.append(branch)
        except Exception as e:
            print(f"Warning: Could not process branch {branch.name}: {str(e)}")
            continue

    print(f"Found {len(recent_branches)} branches updated between {start_date} and {end_date}")
    return recent_branches

def process_branch(branch, repo, start_date, end_date, processed_commits):
    """
    Process a single branch to extract user activity.

    Args:
        branch: Branch object to process.
        repo: GitHub repository object.
        start_date: Start date for filtering activity.
        end_date: End date for filtering activity.
        processed_commits: Set to track already processed commit SHAs.

    Returns:
        A dictionary containing user activity for all users in the branch.
    """
    branch_activity = defaultdict(lambda: {
        "commits": 0,
        "files_changed": set(),
        "lines_added": 0,
        "lines_removed": 0,
        "coding_days": set(),
        "commits_per_day": defaultdict(int)
    })

    try:
        branch_commits = repo.get_commits(sha=branch.commit.sha, since=start_date, until=end_date)
        for commit in branch_commits:
            commit_sha = commit.sha
            commit_author = commit.author.login if commit.author else "Unknown"
            commit_date = commit.commit.author.date.date()

            # Skip duplicate commits
            if commit_sha in processed_commits:
                continue

            # Log commit details for debugging
            print(f"Processing commit: {commit_sha}, Author: {commit_author}, Date: {commit_date}")

            # Mark commit as processed
            processed_commits.add(commit_sha)

            # Update branch activity for the author
            branch_activity[commit_author]["commits"] += 1
            branch_activity[commit_author]["coding_days"].add(commit_date)
            branch_activity[commit_author]["commits_per_day"][commit_date] += 1

            try:
                files = commit.files
                for file in files:
                    branch_activity[commit_author]["files_changed"].add(file.filename)
                    if file.additions is not None:
                        branch_activity[commit_author]["lines_added"] += file.additions
                    if file.deletions is not None:
                        branch_activity[commit_author]["lines_removed"] += file.deletions
            except Exception as e:
                print(f"Warning: Could not process files in commit {commit_sha}: {str(e)}")
                continue
    except Exception as e:
        print(f"Warning: Could not process branch {branch.name}: {str(e)}")

    return branch_activity

def get_all_user_metrics(repo, start_date, end_date):
    """
    Get metrics for all users on their individual branches.

    Args:
        repo: GitHub repository object.
        start_date: Start date for filtering activity.
        end_date: End date for filtering activity.

    Returns:
        A dictionary containing metrics for all users.
    """

    print("Inside get_all_user_metrics")
    branches = get_recent_branches(repo, start_date, end_date)
    all_user_metrics = defaultdict(lambda: {
        "commits": 0,
        "files_changed": set(),
        "lines_added": 0,
        "lines_removed": 0,
        "coding_days": set(),
        "commits_per_day": defaultdict(int)
    })
    processed_commits = set()  # Track processed commits globally

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_branch, branch, repo, start_date, end_date, processed_commits) for branch in branches]
        for future in futures:
            branch_activity = future.result()
            for user, metrics in branch_activity.items():
                all_user_metrics[user]["commits"] += metrics["commits"]
                all_user_metrics[user]["files_changed"].update(metrics["files_changed"])
                all_user_metrics[user]["lines_added"] += metrics["lines_added"]
                all_user_metrics[user]["lines_removed"] += metrics["lines_removed"]
                all_user_metrics[user]["coding_days"].update(metrics["coding_days"])
                for date, count in metrics["commits_per_day"].items():
                    all_user_metrics[user]["commits_per_day"][date] += count

    return all_user_metrics

def calculate_metrics(from_date, to_date):
    """
    Calculate metrics based on the date range and save to a CSV file.
    """
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO", "owner/repo")

    # Initialize GitHub client
    g = Github(token)
    repo = g.get_repo(repo_name)

    # Get metrics for all users
    all_user_metrics = get_all_user_metrics(repo, from_date, to_date)

    # Format the metrics into a DataFrame
    metrics = []
    for user, data in all_user_metrics.items():
        metrics.append({
            "User": user,
            "Total Coding Days": len(data["coding_days"]),
            "Total Commits": data["commits"],
            "Files Changed": len(data["files_changed"]),
            "Lines Added": data["lines_added"],
            "Lines Removed": data["lines_removed"]
        })

    # Save metrics to a CSV file
    os.makedirs(METRICS_DIR, exist_ok=True)
    df = pd.DataFrame(metrics)
    df.to_csv(OVERALL_METRICS_FILE, index=False)
    print(f"Metrics saved to {OVERALL_METRICS_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate GitHub metrics.")
    parser.add_argument("--from-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to-date", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    # Parse the date range
    from_date = datetime.strptime(args.from_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    to_date = datetime.strptime(args.to_date, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(hours=23, minutes=59, seconds=59)

    # Calculate metrics
    calculate_metrics(from_date, to_date)