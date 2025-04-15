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
        
        # author_name, author_email, author_time, commit_message = commit_info
        
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

# def print_analysis_summary(analysis):
#     """
#     Print a human-readable summary of the analysis
    
#     :param analysis: Analysis results dictionary
#     """
#     if "error" in analysis:
#         print(f"Error analyzing commit: {analysis['error']}")
#         return


#     print("\n----- CHANGED FILES -----")
#     for file_path, stats in analysis['files'].items():
#         print(f"{file_path}: +{stats['additions']} -{stats['deletions']} ({stats['changes']} changes)")
    
#     print("\n----- DIFF SUMMARY -----")
#     print(analysis['diff_summary'])
    
#     # Print a truncated version of the full diff
#     print("\n----- DIFF PREVIEW -----")
#     diff_preview = analysis['full_diff']
#     print(diff_preview)

def clone_repo(repo_owner, repo_name, repo_playground):
    if (repo_name) in os.listdir(repo_playground):
        # subprocess.run(
        #     ["rm", "-rf", f"{repo_name}"], check=True
        # )
        return
    os.makedirs(repo_name)
    try:

        print(
            f"Cloning repository from https://github.com/{repo_owner}/{repo_name}.git to {repo_playground}/{repo_name}..."
        )
        subprocess.run(
            [
                "git",
                "clone",
                f"https://github.com/{repo_owner}/{repo_name}.git",
                f"{repo_playground}/{repo_name}",
            ],
            check=True,
        )
        print("Repository cloned successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running git command: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def postprocessing(analysis, repo_name, repo_path):
    ####################### POSTPROCESSING ########################
    valid_files_fix = []
    for file_path, _ in analysis['files'].items():
        if ".py"  not in file_path or "test" in file_path:
            continue
        valid_files_fix.append(file_path)

    BASE_REPOS_EDITED_FILES_CONTENT_PATH = "repos_vul_files"
    SPECIFIC_REPOS_EDITED_FILES_CONTENT_PATH = os.path.join(BASE_REPOS_EDITED_FILES_CONTENT_PATH, repo_name)
    SPECIFIC_COMMIT_EDITED_FILES_CONTENT_PATH = os.path.join(SPECIFIC_REPOS_EDITED_FILES_CONTENT_PATH, commit_id[:7])
    if not os.path.exists(BASE_REPOS_EDITED_FILES_CONTENT_PATH):
        os.makedirs(BASE_REPOS_EDITED_FILES_CONTENT_PATH, exist_ok=True)
    if not os.path.exists(SPECIFIC_REPOS_EDITED_FILES_CONTENT_PATH):
        os.makedirs(SPECIFIC_REPOS_EDITED_FILES_CONTENT_PATH, exist_ok=True)
    # if not os.path.exists(os.path.join(BASE_REPOS_EDITED_FILES_CONTENT_PATH, repo_name, commit_id[:7])):
    os.makedirs(SPECIFIC_COMMIT_EDITED_FILES_CONTENT_PATH, exist_ok=True)
    
    for file_path in valid_files_fix:
        src_path = os.path.join(repo_path, file_path)
        dst_path = os.path.join(SPECIFIC_COMMIT_EDITED_FILES_CONTENT_PATH, file_path.split("/")[-1].split('.')[0] + "_vul.py")
        import shutil
        # copy the contents of the demo.py file to  a new file called demo1.py
        shutil.copyfile(src_path, dst_path)
        # if os.path.exists(file_path):
        #     print(file_path)
        # else:
        #     print(f"File not found: {file_path}")


# Example usage
if __name__ == "__main__":
    with open('repos_fixes/filtered_fixes.json', 'r') as f:
        repos_fixes = json.load(f)

    # path of the folder where the repositories will be cloned
    repo_playground = "."
    
    # constants to access elements in the repos_fixes list
    REPO_URL_INDEX = 2
    COMMIT_ID_INDEX = 1
    
    number = 0
    
    for repo in repos_fixes:
        repo_owner, repo_name = repo[REPO_URL_INDEX].split("/")[-2:]
        commit_id = repo[COMMIT_ID_INDEX]
        repo_path = os.path.join(".", repo_name)
        
        # Clone the repository
        clone_repo(repo_owner, repo_name, repo_playground)
        
        # Analyze the commit
        analysis = analyze_commit_changes(repo_path, commit_id)
        
        # Save analysis to file
        # save_analysis_to_file(analysis, f"{repo_name}_{commit_id[:7]}_analysis.json")
        
        subprocess.run(["git", "-C", repo_path, "checkout", "HEAD^"],
            check=True, capture_output=True)
        postprocessing(analysis, repo_name, repo_path)
        number += 1
        if (number == 2):
            break