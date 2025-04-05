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
        
        current_file = None
        current_class = None
        current_method = None
        old_line_num = None
        new_line_num = None
        
        lines = diff_output.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Extract file name
            if line.startswith("diff --git"):
                file_path = line.split(" b/")[-1]
                current_file = file_path
                current_class = None
                current_method = None
            
            # Extract line numbers from the @@ markers
            elif line.startswith("@@"):
                line_info = line.split("@@")[1].strip()
                line_numbers = line_info.split(" ")
                old_range = line_numbers[0]
                new_range = line_numbers[1]
                
                # Extract starting line numbers
                old_line_num = abs(int(old_range.split(",")[0]))
                new_line_num = int(new_range.split(",")[0])
                
                # Reset context tracking
                current_class = None
                current_method = None
                
                # Look ahead for class/method context
                context_index = i + 1
                context_lines = []
                while context_index < i + 20 and context_index < len(lines):
                    context_line = lines[context_index]
                    if not context_line.startswith("+") and not context_line.startswith("-"):
                        context_lines.append(context_line)
                    context_index += 1
                
                # Check for class/method definitions in context
                for ctx_line in context_lines:
                    # Handle Python class definitions
                    if "class " in ctx_line and ":" in ctx_line:
                        class_match = ctx_line.split("class ")[1].split("(")[0].split(":")[0].strip()
                        current_class = class_match

            # Track line numbers and changes
            elif line.startswith("+") and not line.startswith("+++"):
                file_stats[current_file]["additions"] += 1
                file_stats[current_file]["changes"] += 1
                
                if new_line_num is not None:
                    change_info = {
                        "type": "addition",
                        "line_number": new_line_num,
                        "content": line[1:],
                        "class": current_class,
                        "method": current_method
                    }
                    file_stats[current_file]["line_changes"].append(change_info)
                    
                    # Add to class/method changes if context is available
                    if current_class or current_method:
                        class_method_key = f"{current_class or 'Unknown'}::{current_method or 'global'}"
                        file_stats[current_file]["class_method_changes"].append({
                            "class": current_class,
                            "method": current_method,
                            "key": class_method_key,
                            "line": new_line_num,
                            "type": "addition",
                            "content": line[1:]
                        })
                
                if new_line_num is not None:
                    new_line_num += 1
                    
            elif line.startswith("-") and not line.startswith("---"):
                file_stats[current_file]["deletions"] += 1
                file_stats[current_file]["changes"] += 1
                
                if old_line_num is not None:
                    change_info = {
                        "type": "deletion",
                        "line_number": old_line_num,
                        "content": line[1:],
                        "class": current_class,
                        "method": current_method
                    }
                    file_stats[current_file]["line_changes"].append(change_info)
                    
                    # Add to class/method changes if context is available
                    if current_class or current_method:
                        class_method_key = f"{current_class or 'Unknown'}::{current_method or 'global'}"
                        file_stats[current_file]["class_method_changes"].append({
                            "class": current_class,
                            "method": current_method,
                            "key": class_method_key,
                            "line": old_line_num,
                            "type": "deletion",
                            "content": line[1:]
                        })
                
                if old_line_num is not None:
                    old_line_num += 1
            
            # Handle context lines
            elif not line.startswith("+") and not line.startswith("-") and not line.startswith("diff") and not line.startswith("@@"):
                if old_line_num is not None:
                    old_line_num += 1
                if new_line_num is not None:
                    new_line_num += 1
                
                # Update class/method context while parsing context lines
                if "class " in line and ":" in line:
                    class_match = line.split("class ")[1].split("(")[0].split(":")[0].strip()
                    current_class = class_match
                
                if "def " in line and ":" in line:
                    method_match = line.split("def ")[1].split("(")[0].strip()
                    current_method = method_match
            
            i += 1
        
        
        
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

def print_analysis_summary(analysis):
    """
    Print a human-readable summary of the analysis
    
    :param analysis: Analysis results dictionary
    """
    if "error" in analysis:
        print(f"Error analyzing commit: {analysis['error']}")
        return
        
    print("\n===== COMMIT ANALYSIS =====")
    # print(f"Commit: {analysis['commit_id']}")
    # print(f"Author: {analysis['author']['name']} <{analysis['author']['email']}>")
    # print(f"Date: {analysis['date']['readable']}")
    # print(f"Message: {analysis['message']}")
    # print("\n----- STATISTICS -----")
    # print(f"Files changed: {analysis['stats']['files_changed']}")
    # print(f"Lines added: {analysis['stats']['total_additions']}")
    # print(f"Lines deleted: {analysis['stats']['total_deletions']}")
    # print(f"Total changes: {analysis['stats']['total_changes']}")
    
    # print("\n----- FILE TYPES -----")
    # for ext, count in analysis['stats']['file_extensions'].items():
    #     print(f".{ext}: {count} files")
    
    print("\n----- CHANGED FILES -----")
    for file_path, stats in analysis['files'].items():
        print(f"{file_path}: +{stats['additions']} -{stats['deletions']} ({stats['changes']} changes)")
    
    print("\n----- DIFF SUMMARY -----")
    print(analysis['diff_summary'])
    
    # Print a truncated version of the full diff
    print("\n----- DIFF PREVIEW -----")
    diff_preview = analysis['full_diff']
    print(diff_preview)

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


# Example usage
if __name__ == "__main__":
    with open('repos_fixes/filtered_fixes.json', 'r') as f:
        repos_fixes = json.load(f)
    # print(repos_fixes)
    repo_playground = "."
    REPO_URL_INDEX = 2
    COMMIT_ID_INDEX = 1
    for repo in repos_fixes:
        repo_owner, repo_name = repo[REPO_URL_INDEX].split("/")[-2:]
        commit_id = repo[COMMIT_ID_INDEX]
        repo_path = os.path.join(".", repo_name)
        
        
        clone_repo(repo_owner, repo_name, repo_playground)
        # Analyze the commit
        analysis = analyze_commit_changes(repo_path, commit_id)
        
        # Save analysis to file
        save_analysis_to_file(analysis, f"{repo_name}_{commit_id[:7]}_analysis.json")
        
        # Print a summary
        print_analysis_summary(analysis)
        break