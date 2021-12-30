from base64 import b64encode
from json import load, loads

from requests import get, Response, post

# Spotify API constants
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


def get_token() -> str:
    # Get API token from a file.
    with open('client_secrets.json', 'r') as infile:
        secrets_web = load(infile)['web']

    client_token = b64encode("{}:{}".format(secrets_web['client_id'],
                                            secrets_web['client_secret']).encode('UTF-8')).decode('ascii')
    headers = {"Authorization": "Basic {}".format(client_token)}
    payload = {"grant_type": "client_credentials"}
    token_request = post(SPOTIFY_TOKEN_URL, data=payload, headers=headers)
    request_text: dict = loads(token_request.text)
    if 'access_token' in request_text:
        access_token = request_text["access_token"]
    else:

        """
        If there is no token returned, the received packet must be an error.
        The only way this should have happened is if the authentication was incorrect.
        """

        raise ValueError("Error in authentication! Check the client_secrets.json file, "
                         "you need to enter your own information instead of leaving it default!")

    return access_token


def get_song(wildcard: str, genre_str: str, offset: int, header: dict) -> Response:
    return get(
        '{}/search?q={}{}&type=track&offset={}'.format(
            SPOTIFY_API_URL,
            wildcard,
            genre_str,
            offset
        ),
        headers=header
    )
