import argparse
from .settings import edit_settings, load_settings
from .sync import sync_repos
from .gitApi import get_public_repos


def main():
    # parse the arguments
    parser = argparse.ArgumentParser(description="AskSurf CLI")
    parser.add_argument(
        "--settings",
        "-s",
        action="store_true",
        help="Edit the settings",
    )

    args = parser.parse_args()

    if args.settings:
        edit_settings()
        return

    # load the settings
    settings = load_settings()
    username = settings["general"]["github-username"]
    local_repo_path = settings["general"]["local-repo-path"]
    target_git_server = settings["general"]["target-git-server"]
    if not username or not local_repo_path or not target_git_server:
        print("Please set the settings first.")
        return

    # get the public repos
    repos = get_public_repos(username)
    if not repos:
        print("No public repos found.")
        return

    # sync the repos
    sync_repos(repos)
    print("Sync completed.")


if __name__ == "__main__":
    main()
