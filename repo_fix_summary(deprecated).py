import os
import subprocess
import json
from collections import defaultdict

def analyze_commit_changes(repo_path, commit_id):
    """
    Analyze changes made in a specific commit compared to its parent.
    
    :param repo_path: Path to the local git repository
    :param commit_id: Commit ID to analyze
    :return: Dictionary containing detailed information about the changes
    """
    try:
        # Ensure we're at the right commit
        subprocess.run(["git", "-C", repo_path, "checkout", commit_id], 
                    check=True, capture_output=True)
        
        # Get commit details
        commit_info = subprocess.run(
            ["git", "-C", repo_path, "show", "--quiet", "--pretty=format:%an|%ae|%at|%s", commit_id],
            check=True, capture_output=True, text=True
        ).stdout.strip().split("|")
        
        author_name, author_email, author_time, commit_message = commit_info
        
        # Get list of files changed
        files_changed = subprocess.run(
            ["git", "-C", repo_path, "diff-tree", "--no-commit-id", "--name-only", "-r", commit_id],
            check=True, capture_output=True, text=True
        ).stdout.strip().split("\n")
        
        # Get stats summary
        stats_summary = subprocess.run(
            ["git", "-C", repo_path, "diff", "--stat", f"{commit_id}^", commit_id],
            check=True, capture_output=True, text=True
        ).stdout.strip()
        
        # Get detailed diff
        diff_output = subprocess.run(
            ["git", "-C", repo_path, "diff", f"{commit_id}^", commit_id],
            check=True, capture_output=True, text=True
        ).stdout

        # Parse diff to count additions and deletions by file
        file_stats = defaultdict(lambda: {"additions": 0, "deletions": 0, "changes": 0})
        current_file = None
        
        for line in diff_output.split("\n"):
            if line.startswith("diff --git"):
                # Extract the file name from the diff header
                file_path = line.split(" b/")[-1]
                current_file = file_path
            elif line.startswith("+") and not line.startswith("+++"):
                file_stats[current_file]["additions"] += 1
                file_stats[current_file]["changes"] += 1
            elif line.startswith("-") and not line.startswith("---"):
                file_stats[current_file]["deletions"] += 1
                file_stats[current_file]["changes"] += 1
        
        # Calculate totals
        total_additions = sum(stats["additions"] for stats in file_stats.values())
        total_deletions = sum(stats["deletions"] for stats in file_stats.values())
        total_changes = total_additions + total_deletions
        
        # Determine file types changed
        file_extensions = defaultdict(int)
        for file in files_changed:
            if "." in file:
                ext = file.split(".")[-1].lower()
                file_extensions[ext] += 1
            else:
                file_extensions["no_extension"] += 1
        
        # Get commit date in readable format
        date_readable = subprocess.run(
            ["git", "-C", repo_path, "show", "-s", "--format=%ci", commit_id],
            check=True, capture_output=True, text=True
        ).stdout.strip()
        
        # Assemble results
        result = {
            "commit_id": commit_id,
            "author": {
                "name": author_name,
                "email": author_email
            },
            "date": {
                "timestamp": author_time,
                "readable": date_readable
            },
            "message": commit_message,
            "stats": {
                "files_changed": len(files_changed),
                "total_additions": total_additions,
                "total_deletions": total_deletions,
                "total_changes": total_changes,
                "file_extensions": dict(file_extensions)
            },
            "files": {
                file: stats for file, stats in file_stats.items()
            },
            "files_list": files_changed,
            "diff_summary": stats_summary,
            "full_diff": diff_output
        }
        
        return result
        
    except subprocess.CalledProcessError as e:
        print(f"Git command error: {e}")
        return {"error": str(e), "stdout": e.stdout, "stderr": e.stderr}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": str(e)}

def save_analysis_to_file(analysis, output_file):
    """
    Save the analysis results to a JSON file
    
    :param analysis: Analysis results dictionary
    :param output_file: Path to output file
    """
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"Analysis saved to {output_file}")

def print_analysis_summary(analysis):
    """
    Print a human-readable summary of the analysis
    
    :param analysis: Analysis results dictionary
    """
    if "error" in analysis:
        print(f"Error analyzing commit: {analysis['error']}")
        return
        
    print("\n===== COMMIT ANALYSIS =====")
    print(f"Commit: {analysis['commit_id']}")
    print(f"Author: {analysis['author']['name']} <{analysis['author']['email']}>")
    print(f"Date: {analysis['date']['readable']}")
    print(f"Message: {analysis['message']}")
    print("\n----- STATISTICS -----")
    print(f"Files changed: {analysis['stats']['files_changed']}")
    print(f"Lines added: {analysis['stats']['total_additions']}")
    print(f"Lines deleted: {analysis['stats']['total_deletions']}")
    print(f"Total changes: {analysis['stats']['total_changes']}")
    
    print("\n----- FILE TYPES -----")
    for ext, count in analysis['stats']['file_extensions'].items():
        print(f".{ext}: {count} files")
    
    print("\n----- CHANGED FILES -----")
    for file_path, stats in analysis['files'].items():
        print(f"{file_path}: +{stats['additions']} -{stats['deletions']} ({stats['changes']} changes)")
    
    print("\n----- DIFF SUMMARY -----")
    print(analysis['diff_summary'])
    
    # Print a truncated version of the full diff
    print("\n----- DIFF PREVIEW -----")
    diff_preview = analysis['full_diff']
    print(diff_preview)

# Example usage
if __name__ == "__main__":
    # ('CVE-2012-4520', '9305c0e12d43c4df999c3301a1f0c742264a657e', 'https://github.com/django/django')
    repo_playground = "."
    repo_name = "django"
    commit_id = "9305c0e12d43c4df999c3301a1f0c742264a657e"

    repo_path = os.path.join(repo_playground, repo_name)
    
    # Analyze the commit
    analysis = analyze_commit_changes(repo_path, commit_id)
    
    # Save analysis to file
    save_analysis_to_file(analysis, f"{repo_name}_{commit_id[:7]}_analysis.json")
    
    # Print a summary
    print_analysis_summary(analysis)