import os
import sys
import random
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from git import Repo

# Function to generate all days in a date range
def generate_dates(start_date, end_date):
    """Generate all dates in a range with time component."""
    delta = timedelta(days=1)
    current_date = start_date
    while current_date <= end_date:
        # Add random time to make commits look more natural
        hour = random.randint(9, 18)  # Working hours
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        date_with_time = current_date.replace(hour=hour, minute=minute, second=second)
        yield date_with_time.strftime("%Y-%m-%d %H:%M:%S")
        current_date += delta

# Function to create a commit for a specific date
def create_commit(repo, date, commit_number, file_path="dummy_file.txt"):
    """Create a commit for a specific date."""
    try:
        # Create or modify the dummy file
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(f"Commit {commit_number} for {date}\n")

        # Stage the file
        repo.index.add([file_path])

        # Commit with the specific date and message
        commit_message = f"Commit {commit_number} on {date}"
        repo.index.commit(commit_message, author_date=date, commit_date=date)
        return True
    except Exception as e:
        print(f"Error creating commit {commit_number} for {date}: {e}")
        return False

# Function to load configuration from file
def load_config(config_path="config.json"):
    """Load configuration from JSON file."""
    default_config = {
        "start_date": "2025-01-01",
        "end_date": "2025-01-16",
        "skip_probability": 0.2,
        "min_commits": 1,
        "max_commits": 6,
        "auto_push": False,
        "repo_path": None  # None means use current directory
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Merge with defaults
                default_config.update(config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}. Using defaults.")
    
    return default_config

# Main script
def main():
    parser = argparse.ArgumentParser(
        description="Automated git commit generator for date ranges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use defaults (current directory, date range from config)
  python commiter.py

  # Specify date range
  python commiter.py --start 2025-01-01 --end 2025-01-31

  # Use custom repository path
  python commiter.py --repo "D:\\my project\\my-git"

  # Auto-push after commits
  python commiter.py --push

  # Use config file
  python commiter.py --config my_config.json
        """
    )
    
    parser.add_argument("--repo", type=str, help="Path to git repository (default: current directory)")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--skip-prob", type=float, help="Probability of skipping a day (0.0-1.0)")
    parser.add_argument("--min-commits", type=int, help="Minimum commits per day")
    parser.add_argument("--max-commits", type=int, help="Maximum commits per day")
    parser.add_argument("--push", action="store_true", help="Push changes to remote after commits")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making commits")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Determine repository path
    if args.repo:
        repo_path = Path(args.repo)
    elif config.get("repo_path"):
        repo_path = Path(config["repo_path"])
    else:
        # Use current directory
        repo_path = Path.cwd()
    
    # Convert to absolute path for cross-platform compatibility
    repo_path = repo_path.resolve()
    
    print(f"Repository path: {repo_path}")
    
    # Initialize or open the repository
    try:
        if not repo_path.exists():
            if args.dry_run:
                print(f"[DRY RUN] Would create repository at {repo_path}")
                repo = None
            else:
                print(f"Creating new repository at {repo_path}")
                repo = Repo.init(repo_path)
        else:
            if args.dry_run:
                print(f"[DRY RUN] Would open repository at {repo_path}")
                repo = None
            else:
                print(f"Opening existing repository at {repo_path}")
                repo = Repo(repo_path)
                
                # Check if it's a valid git repo
                if not repo.bare:
                    print(f"Repository branch: {repo.active_branch.name}")
    except Exception as e:
        print(f"Error initializing repository: {e}")
        sys.exit(1)
    
    # Parse date range
    start_date_str = args.start or config.get("start_date", "2025-01-01")
    end_date_str = args.end or config.get("end_date", "2025-01-16")
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError as e:
        print(f"Error parsing dates: {e}. Use format YYYY-MM-DD")
        sys.exit(1)
    
    if start_date > end_date:
        print("Error: Start date must be before end date")
        sys.exit(1)
    
    # Get configuration values
    skip_probability = args.skip_prob if args.skip_prob is not None else config.get("skip_probability", 0.2)
    min_commits = args.min_commits if args.min_commits is not None else config.get("min_commits", 1)
    max_commits = args.max_commits if args.max_commits is not None else config.get("max_commits", 6)
    auto_push = args.push or config.get("auto_push", False)
    
    print(f"\nConfiguration:")
    print(f"  Date range: {start_date_str} to {end_date_str}")
    print(f"  Skip probability: {skip_probability * 100:.1f}%")
    print(f"  Commits per day: {min_commits}-{max_commits}")
    print(f"  Auto-push: {auto_push}")
    print(f"  Dry run: {args.dry_run}")
    print()
    
    if args.dry_run:
        print("[DRY RUN MODE - No actual commits will be made]\n")
    
    # Change to repository directory if needed
    original_cwd = Path.cwd()
    if not args.dry_run and repo:
        try:
            os.chdir(repo_path)
        except Exception as e:
            print(f"Warning: Could not change to repo directory: {e}")
    
    total_commits = 0
    skipped_days = 0
    
    try:
        # Loop through all days in the date range
        for date_str in generate_dates(start_date, end_date):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            
            # Skip some days randomly
            if random.random() < skip_probability:
                print(f"Skipping commits for {date_str}")
                skipped_days += 1
                continue

            # Generate a random number of commits
            num_commits = random.randint(min_commits, max_commits)
            print(f"Creating {num_commits} commits for {date_str}")

            # Create the commits
            if not args.dry_run:
                for commit_number in range(1, num_commits + 1):
                    if create_commit(repo, date_str, commit_number):
                        print(f"  ✓ Commit {commit_number}/{num_commits} created")
                        total_commits += 1
                    else:
                        print(f"  ✗ Failed to create commit {commit_number}/{num_commits}")
            else:
                total_commits += num_commits
                print(f"  [DRY RUN] Would create {num_commits} commits")
        
        print(f"\n{'Summary (DRY RUN):' if args.dry_run else 'Summary:'}")
        print(f"  Total commits: {total_commits}")
        print(f"  Skipped days: {skipped_days}")
        
        # Push changes to remote (optional)
        if auto_push and not args.dry_run and repo:
            try:
                origin = repo.remote(name="origin")
                print("\nPushing changes to remote...")
                origin.push()
                print("✓ Changes pushed successfully.")
            except Exception as e:
                print(f"⚠ Failed to push changes: {e}")
                print("  You can push manually later with: git push")
        elif auto_push and args.dry_run:
            print("[DRY RUN] Would push changes to remote")
            
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user. Some commits may have been created.")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Restore original working directory
        if not args.dry_run:
            try:
                os.chdir(original_cwd)
            except:
                pass

if __name__ == "__main__":
    main()
