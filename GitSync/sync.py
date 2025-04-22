import os
import requests
from .settings import load_settings


def forgejo_create_repo(repo_name):

    settings = load_settings()
    forgejo_api_url = settings["general"]["forgejo-api-url"]
    forgejo_token = settings["general"]["forgejo-token"]

    url = f"{forgejo_api_url}/api/v1/user/repos"

    headers = {
        "Authorization": f"Bearer {forgejo_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    data = {
        "name": repo_name,
        "description": "",
        "private": False,
        "auto_init": True,
        "default_branch": "main",
        "trust_model": "default"
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        print(f"Repo '{repo_name}' created successfully on Forgejo.")
    elif response.status_code == 409:
        print(f"Repo '{repo_name}' already exists on Forgejo.")
    else:
        print(f"Failed to create repo '{repo_name}'.")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")


def sync_repos(repos):
    path = load_settings()["general"]["local-repo-path"]

    if not os.path.exists(path):
        os.makedirs(path)
    os.chdir(path)

    for repo in repos:
        repo_name = repo.split("/")[-1].replace(".git", "")
        repo_path = f"{path}/{repo_name}"
        if not os.path.exists(repo_path):
            os.system(f"git clone {repo} {repo_path}")

            if load_settings()["general"]["forgejo-api-url"]:
                forgejo_create_repo(repo_name)

        else:
            os.system(f"cd {repo_path} && git pull")

        # push to the target git server
        target_git_server = f'{load_settings()["general"]["target-git-server"]}/{repo_name}.git'
        if target_git_server:
            os.system(f"cd {repo_path} && git remote | grep -q target || git remote add target {target_git_server}")
            os.system(f"cd {repo_path} && git remote set-url target {target_git_server}")
            os.system(f"cd {repo_path} && git push target --all --force")
