import os
import random
from datetime import datetime, timedelta
from git import Repo

# Function to generate all days in a date range
def generate_dates(start_date, end_date):
    delta = timedelta(days=1)  # Increment by 1 day
    current_date = start_date
    while current_date <= end_date:
        yield current_date.strftime("%Y-%m-%d %H:%M:%S")  # Format as "YYYY-MM-DD HH:MM:SS"
        current_date += delta

# Function to create a commit for a specific date
def create_commit(repo, date, commit_number):
    # Create or modify a dummy file
    file_path = "dummy_file.txt"
    with open(file_path, "a") as file:
        file.write(f"Commit {commit_number} for {date}\n")

    # Stage the file
    repo.index.add([file_path])

    # Commit with the specific date and message
    commit_message = f"Commit {commit_number} on {date}"
    repo.index.commit(commit_message, author_date=date, commit_date=date)

# Main script
def main():
    # Path to your local Git repository
    repo_path = "/home/test/Desktop/code/my-git"

    # Initialize or open the repository
    if not os.path.exists(repo_path):
        print(f"Creating new repository at {repo_path}")
        repo = Repo.init(repo_path)
    else:
        print(f"Opening existing repository at {repo_path}")
        repo = Repo(repo_path)

    # Define the date range (e.g., January 1, 2020, to December 31, 2020)
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 1, 16)

    # Loop through all days in the date range
    for date in generate_dates(start_date, end_date):
        # Add a 1-day tolerance: Skip some days randomly (20% chance)
        if random.random() < 0.2:  # 20% chance to skip a day
            print(f"Skipping commits for {date}")
            continue

        # Generate a random number of commits (between 1 and 10)
        num_commits = random.randint(1, 6)
        print(f"Creating {num_commits} commits for {date}")

        # Create the commits
        for commit_number in range(1, num_commits + 1):
            create_commit(repo, date, commit_number)
            print(f"Commit {commit_number} created for {date}")

    # Push changes to GitHub (optional)
    try:
        origin = repo.remote(name="origin")
        origin.push()
        print("Changes pushed to GitHub.")
    except Exception as e:
        print(f"Failed to push changes to GitHub: {e}")

if __name__ == "__main__":
    main()
