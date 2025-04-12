from github import Github
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import sys
import shutil

# Load environment variables
load_dotenv()

def clean_output_directory(output_dir):
    """
    Clean the output directory by deleting all its contents.

    Args:
        output_dir: Directory to clean.
    """
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)  # Remove the directory and all its contents
    os.makedirs(output_dir, exist_ok=True)  # Recreate the directory

def get_recent_branches(repo, days=220):
    """
    Fetch branches updated within the last `days` days.

    Args:
        repo: GitHub repository object.
        days: Number of days to look back for recent branches.

    Returns:
        List of branch objects updated within the specified time frame.
    """
    recent_branches = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    for branch in repo.get_branches():
        try:
            # Get the last commit date for the branch
            last_commit = branch.commit.commit.author.date
            if last_commit >= cutoff_date:
                recent_branches.append(branch)
        except Exception as e:
            print(f"Warning: Could not process branch {branch.name}: {str(e)}")
            continue

    print(f"Found {len(recent_branches)} branches updated in the last {days} days")
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
    branches = get_recent_branches(repo, days=90)
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

def save_all_user_metrics_to_csv(all_user_metrics, output_dir):
    """
    Save metrics for all users to CSV files.

    Args:
        all_user_metrics: Dictionary containing metrics for all users.
        output_dir: Directory to save the CSV files.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Save overall metrics
    overall_data = []
    for user, metrics in all_user_metrics.items():
        overall_data.append({
            "User": user,
            "Total Coding Days": len(metrics["coding_days"]),
            "Total Commits": metrics["commits"],
            "Files Changed": len(metrics["files_changed"]),
            "Lines Added": metrics["lines_added"],
            "Lines Removed": metrics["lines_removed"]
        })
    overall_df = pd.DataFrame(overall_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    overall_df.to_csv(f"{output_dir}/overall_metrics", index=False)

    # Save commits per day
    commits_per_day_data = []
    for user, metrics in all_user_metrics.items():
        for date, count in metrics["commits_per_day"].items():
            commits_per_day_data.append({
                "User": user,
                "Date": date,
                "Commits": count
            })
    commits_per_day_df = pd.DataFrame(commits_per_day_data)
    commits_per_day_df.to_csv(f"{output_dir}/commits_per_day.csv", index=False)

    print(f"Metrics for all users have been saved to '{output_dir}'")

def get_github_metrics(repo_name, token):
    """
    Get various metrics from a GitHub repository for all users.

    Args:
        repo_name (str): Repository name in format 'owner/repo'.
        token (str): GitHub personal access token.
    """
    if not token:
        print("Error: GitHub token is required for private/internal repositories")
        print("Please set GITHUB_TOKEN in your .env file")
        sys.exit(1)

    try:
        # Initialize GitHub client with token
        g = Github(token)

        # Access the repository
        repo = g.get_repo(repo_name)
        print(f"Successfully accessed repository: {repo.full_name}")

        # Clean the output directory
        output_dir = "metrics_output"
        clean_output_directory(output_dir)

        # Calculate date range for the last 220 days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=220)
        print(f"\nAnalyzing metrics for all users from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        # Get metrics for all users
        all_user_metrics = get_all_user_metrics(repo, start_date, end_date)

        # Save metrics to CSV
        save_all_user_metrics_to_csv(all_user_metrics, output_dir=output_dir)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Get repository name and token from environment variables
    repo_name = os.getenv("GITHUB_REPO", "owner/repo")
    token = os.getenv("GITHUB_TOKEN")

    get_github_metrics(repo_name, token)