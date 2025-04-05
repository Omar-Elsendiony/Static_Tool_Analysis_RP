import ast
import json
import os
import subprocess

def checkout_commit(repo_path, commit_id, previous=False):
    """
    Checkout the specified commit or its parent in the given local git repository.

    :param repo_path: Path to the local git repository
    :param commit_id: Commit ID to checkout (or to find parent of)
    :param previous: If True, checkout the parent of the specified commit
    :return: None
    """
    try:
        if previous:
            # Get the parent commit ID
            result = subprocess.run(
                ["git", "-C", repo_path, "rev-parse", f"{commit_id}^"],
                check=True,
                capture_output=True,
                text=True
            )
            parent_commit = result.stdout.strip()
            print(f"Found parent commit: {parent_commit}")
            commit_to_checkout = parent_commit
        else:
            commit_to_checkout = commit_id

        # Checkout the appropriate commit
        print(f"Checking out commit {commit_to_checkout} in repository at {repo_path}...")
        subprocess.run(["git", "-C", repo_path, "checkout", commit_to_checkout], check=True)
        print("Commit checked out successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running git command: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def clone_repo(repo_owner, repo_name, repo_playground):
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

def clone_checkout_repo(
    repo_owner, repo_name, commit_id, repo_playground, checkout_previous=False
):
    if (repo_name) in os.listdir(repo_playground):
        subprocess.run(
            ["rm", "-rf", f"{repo_name}"], check=True
        )
    os.makedirs(repo_name)

    clone_repo(repo_owner, repo_name, repo_playground)
    checkout_commit(f"{repo_playground}/{repo_name}", commit_id, previous=checkout_previous)

# pydicom__pydicom
repo_playground = "."
repo_owner = "django"
repo_name = "django"
commit_id = "9305c0e12d43c4df999c3301a1f0c742264a657e"

# ('CVE-2012-4520', '9305c0e12d43c4df999c3301a1f0c742264a657e', 'https://github.com/django/django')
# frictionlessdata__frictionless-py-515
# c59fee5d352e429309ddce7f8350ef70f2003593
# getmoto__moto
# sul-dlss__libsys-airflow

clone_checkout_repo(repo_owner, repo_name, commit_id, repo_playground, checkout_previous=False)

