import requests


def get_public_repos(username):
    url = f'https://api.github.com/users/{username}/repos'

    repos = []
    page = 1
    while True:
        response = requests.get(url, params={'page': page})
        if response.status_code != 200:
            break
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return [repo['clone_url'] for repo in repos]
