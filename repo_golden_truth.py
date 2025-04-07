import os
import subprocess
import json

def postprocessing(repo_name, cve_id, cve_cwe_mapping):
    ####################### POSTPROCESSING ########################
    # valid_files_fix = []
    # for file_path, _ in analysis['files'].items():
    #     if ".rst"  in file_path or ".md"  in file_path or "test" in file_path:
    #         continue
    #     valid_files_fix.append(file_path)

    BASE_REPOS_EDITED_FILES_CONTENT_PATH = "repos_vul_golden_truth"
    SPECIFIC_REPOS_EDITED_FILES_CONTENT_PATH = os.path.join(BASE_REPOS_EDITED_FILES_CONTENT_PATH, repo_name)
    SPECIFIC_COMMIT_EDITED_FILES_CONTENT_PATH = os.path.join(SPECIFIC_REPOS_EDITED_FILES_CONTENT_PATH, commit_id[:7])
    if not os.path.exists(BASE_REPOS_EDITED_FILES_CONTENT_PATH):
        os.makedirs(BASE_REPOS_EDITED_FILES_CONTENT_PATH, exist_ok=True)
    if not os.path.exists(SPECIFIC_REPOS_EDITED_FILES_CONTENT_PATH):
        os.makedirs(SPECIFIC_REPOS_EDITED_FILES_CONTENT_PATH, exist_ok=True)
    # if not os.path.exists(os.path.join(BASE_REPOS_EDITED_FILES_CONTENT_PATH, repo_name, commit_id[:7])):
    os.makedirs(SPECIFIC_COMMIT_EDITED_FILES_CONTENT_PATH, exist_ok=True)
    
    my_dict = {"cve_id": cve_id, "cwe_id": cve_cwe_mapping[cve_id]}

    try:
        with open(os.path.join(SPECIFIC_COMMIT_EDITED_FILES_CONTENT_PATH, "golden_truth"), 'w') as json_file:
            json.dump(my_dict, json_file, indent=4)  # Use indent for pretty formatting
        print(f"Data written to {SPECIFIC_COMMIT_EDITED_FILES_CONTENT_PATH}")
    except Exception as e:
        print(f"An error occurred while writing to the JSON file: {e}")

# Example usage
if __name__ == "__main__":

    with open('cve_cwe_mapping/cve_cwe_mappings_dict.json', 'r') as f:
        cve_cwe_mapping = json.load(f)

    with open('repos_fixes/filtered_fixes.json', 'r') as f:
        repos_fixes = json.load(f)

    
    # constants to access elements in the repos_fixes list
    REPO_URL_INDEX = 2
    COMMIT_ID_INDEX = 1
    CVE_ID_INDEX = 0
    
    number = 0
    
    for repo in repos_fixes:
        repo_owner, repo_name = repo[REPO_URL_INDEX].split("/")[-2:]
        commit_id = repo[COMMIT_ID_INDEX]
        cve_id = repo[CVE_ID_INDEX]
        
        postprocessing(repo_name, cve_id, cve_cwe_mapping)
        
        number += 1
        if (number == 20):
            break