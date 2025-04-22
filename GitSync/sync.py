import os
import requests
import time
from .settings import load_settings


def forgejo_create_repo(repo_name, default_branch="main"):
    settings = load_settings()
    forgejo_api_url = settings["general"]["forgejo-api-url"]
    forgejo_token = settings["general"]["forgejo-token"]


    url = f"{forgejo_api_url}/api/v1/user/repos"
    headers = {
        "Authorization": f"Bearer {forgejo_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Create the repository WITHOUT auto_init
    data = {
        "name": repo_name,
        "description": "",
        "private": False,
        "auto_init": False,  # Specifically do NOT create with README
        "trust_model": "default"
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        print(f"Repo '{repo_name}' created successfully on Forgejo.")
        repo_data = response.json()
        # The default branch will be set after the first push
        return True
    elif response.status_code == 409:
        print(f"Repo '{repo_name}' already exists on Forgejo.")
        return True
    else:
        print(f"Failed to create repo '{repo_name}'.")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def set_default_branch(repo_name, default_branch):
    """Set the default branch after pushing content to the repository"""
    settings = load_settings()
    forgejo_api_url = settings["general"]["forgejo-api-url"]
    forgejo_token = settings["general"]["forgejo-token"]

    # First, determine the owner
    headers = {
        "Authorization": f"Bearer {forgejo_token}",
        "Accept": "application/json"
    }

    # Get user info to determine owner
    user_url = f"{forgejo_api_url}/api/v1/user"
    user_response = requests.get(user_url, headers=headers)

    if user_response.status_code != 200:
        print("Failed to get user info")
        print(f"Status code: {user_response.status_code}")
        return False

    owner = user_response.json().get("username")

    # Update the default branch
    update_url = f"{forgejo_api_url}/api/v1/repos/{owner}/{repo_name}"
    update_headers = {
        "Authorization": f"Bearer {forgejo_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    update_data = {
        "default_branch": default_branch
    }

    update_response = requests.patch(update_url, headers=update_headers, json=update_data)

    if update_response.status_code == 200:
        print(f"Default branch for '{repo_name}' set to '{default_branch}'")
        return True
    else:
        print(f"Failed to set default branch for '{repo_name}'")
        print(f"Status code: {update_response.status_code}")
        print(f"Response: {update_response.text}")
        return False


def sync_repos(repos):
    path = load_settings()["general"]["local-repo-path"]
    if not os.path.exists(path):
        os.makedirs(path)
    os.chdir(path)

    for repo_info in repos:
        repo, default_branch = repo_info
        repo_name = repo.split("/")[-1].replace(".git", "")
        repo_path = f"{path}/{repo_name}"

        if not os.path.exists(repo_path):
            # Clone the original repository first
            os.system(f"git clone {repo} {repo_path}")

            # Create empty repository on Forgejo without README
            if load_settings()["general"]["forgejo-api-url"]:
                forgejo_create_repo(repo_name, default_branch)
        else:
            # Update existing repository
            os.system(f"cd {repo_path} && git pull")

        # Push to the target git server
        target_git_server = f'{load_settings()["general"]["target-git-server"]}/{repo_name}.git'
        if target_git_server:
            # Set up the remote if it doesn't exist
            os.system(f"cd {repo_path} && git remote | grep -q target || git remote add target {target_git_server}")
            os.system(f"cd {repo_path} && git remote set-url target {target_git_server}")
            os.system(f"cd {repo_path} && git fetch origin")

            # Push all branches from the origin to the target
            push_result = os.system(f"cd {repo_path} && git push target 'refs/remotes/origin/*:refs/heads/*' --force")

            # If push successful and we have a non-default branch, set it
            if push_result == 0 and default_branch != "main" and load_settings()["general"]["forgejo-api-url"]:
                # Wait a moment for the server to process the push
                time.sleep(2)
                set_default_branch(repo_name, default_branch)


def delete_all_user_repos():
    """Delete all repositories owned by the authenticated user"""
    settings = load_settings()
    forgejo_api_url = settings["general"]["forgejo-api-url"]
    forgejo_token = settings["general"]["forgejo-token"]

    headers = {
        "Authorization": f"Bearer {forgejo_token}",
        "Accept": "application/json"
    }

    user_url = f"{forgejo_api_url}/api/v1/user"
    user_response = requests.get(user_url, headers=headers)

    if user_response.status_code != 200:
        print("Failed to get user info")
        print(f"Status code: {user_response.status_code}")
        return False

    username = user_response.json().get("username")

    repos_url = f"{forgejo_api_url}/api/v1/user/repos"
    repos_response = requests.get(repos_url, headers=headers)

    if repos_response.status_code != 200:
        print("Failed to get user repositories")
        print(f"Status code: {repos_response.status_code}")
        return False

    repos = repos_response.json()
    deleted_count = 0
    failed_count = 0

    print(f"Found {len(repos)} repositories")

    confirmation = input(f"Are you sure you want to delete all {len(repos)} repositories? (y/n): ")
    if confirmation.lower() != 'y':
        print("Deletion cancelled")
        return False

    for repo in repos:
        repo_name = repo.get("name")
        owner = repo.get("owner", {}).get("username")

        if not owner:
            owner = username

        delete_url = f"{forgejo_api_url}/api/v1/repos/{owner}/{repo_name}"
        delete_response = requests.delete(delete_url, headers=headers)

        if delete_response.status_code == 204:
            print(f"Successfully deleted repository: {repo_name}")
            deleted_count += 1
        else:
            print(f"Failed to delete repository: {repo_name}")
            print(f"Status code: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
            failed_count += 1

    print(f"Deletion complete. Successfully deleted: {deleted_count}, Failed: {failed_count}")
    return True
