import argparse
from .settings import edit_settings, load_settings
from .sync import sync_repos
from .gitApi import get_public_repos
from .sync import delete_all_user_repos


def main():
    # parse the arguments
    parser = argparse.ArgumentParser(description="AskSurf CLI")
    parser.add_argument(
        "--settings",
        "-s",
        action="store_true",
        help="Edit the settings",
    )

    parser.add_argument(
        "--delete",
        "-d",
        action="store_true",
        help="Delete all user repositories on Forgejo",
    )

    args = parser.parse_args()

    if args.settings:
        edit_settings()
        return

    if args.delete:
        # load the settings
        settings = load_settings()
        forgejo_api_url = settings["general"]["forgejo-api-url"]
        forgejo_token = settings["general"]["forgejo-token"]
        if not forgejo_api_url or not forgejo_token:
            print("Please set the Forgejo API URL and token in the settings first.")
            return

        # delete all user repos
        delete_all_user_repos()
        print("All user repositories deleted.")
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
