"""
Module that makes use of the Spotify Web API to retrieve songs below a selected
'threshold' of popularity.
Genres list scrapped from: http://everynoise.com/everynoise1d.cgi?scope=all&vector=popularity
Spotify Ref: https://developer.spotify.com/documentation/web-api/reference-beta/#category-search

"""
from base64 import b64encode
from json import load, loads
from random import choice, randint
from requests import post, get
from sys import argv, exit
from fuzzysearch import find_near_matches

# Spotify API URIs
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Wildcards for random search
RANDOM_WILDCARDS = ['%25a%25', 'a%25', '%25a',
                    '%25e%25', 'e%25', '%25e',
                    '%25i%25', 'i%25', '%25i',
                    '%25o%25', 'o%25', '%25o',
                    '%25u%25', 'u%25', '%25u']


def get_token() -> str:
    try:
        with open('client_secrets.json', 'r') as infile:
            secrets_web = load(infile)['web']
    except FileNotFoundError:
        raise FileNotFoundError("Couldn't find client_secrets.json file!")

    client_token = b64encode("{}:{}".format(secrets_web['client_id'],
                                            secrets_web['client_secret']).encode('UTF-8')).decode('ascii')
    headers = {"Authorization": "Basic {}".format(client_token)}
    payload = {"grant_type": "client_credentials"}
    token_request = post(SPOTIFY_TOKEN_URL, data=payload, headers=headers)
    try:
        access_token = loads(token_request.text)["access_token"]
    except KeyError:
        raise RuntimeError("Error in authentication! Check the client_secrets.json file, "
                           "you need to enter your own information instead of leaving it default!")

    return access_token


def request_valid_song(access_token: str, genre: str):
    wildcard = choice(RANDOM_WILDCARDS)

    # Make a request for the Search API with pattern and random index
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Cap the max number of requests until it decides something's up.
    genre_str = "%20genre:%22{}%22".format(genre.replace(" ", "%20"))
    for i in range(51):
        offset = randint(0, 200)
        try:
            song_request = get(
                '{}/search?q={}{}&type=track&offset={}'.format(
                    SPOTIFY_API_URL,
                    wildcard,
                    genre_str,
                    offset
                ),
                headers=authorization_header
            )
            song: dict = choice(loads(song_request.text)['tracks']['items'])
            return song
        except IndexError:
            # the reason we're looping here is to find one ''without'' an IndexError.
            continue

    raise RuntimeError("Exceeded request limit!")


def validate(track: dict, threshold: int) -> bool:
    if threshold > 100:
        return True
    elif threshold <= 0:
        return False

    if int(track['popularity']) < threshold:
        # Might introduce a more thorough check later...
        return True
    else:
        return False


# Displays a message for each step of the search process.
def print_step(step: int):
    print(step)
    """
    For some reason, this routine just didn't work.
    if step == 30:
        print("Still searching...")
    elif step == 60:
        print("Still searching...")
    elif step == 100:
        print("This search is taking a while...")
    elif (step % 100) == 0:
        print("This search is taking a very long time. \n"
              "It may not be going anywhere. Consider re-running the program.")
    """


def select_genre(args) -> str:
    # Open genres file
    n_args = len(args)
    try:
        with open('genres.json', 'r') as infile:
            valid_genres = load(infile)
    except FileNotFoundError:
        print("Couldn't find genres.json file!")
        exit(1)

    # If genre specified by command line argument, choose it.
    # Otherwise, choose randomly. It's seemingly not possible to make it
    # any genre, or else it starts bugging out and giving random pop songs.
    if n_args == 0 or args[0] == "":
        print("No genre chosen: selecting a genre at random...")
        selected_genre = choice(valid_genres)
        print("New genre: " + selected_genre)
    else:
        selected_genre = (" ".join(args)).lower()

    # Call the API for a song that matches the criteria
    if selected_genre not in valid_genres:
        # If genre not found as it is, try fuzzy search with Levenhstein distance 2
        print("Genre entered was '" + selected_genre + "', which is not in the list of genres supported. Attempting "
                                                       "to find similar genre...")
        valid_genres_to_text = " ".join(valid_genres)
        try:
            selected_genre = find_near_matches(selected_genre, valid_genres_to_text, max_l_dist=2)[0].matched
            print("New genre is '" + selected_genre + "'.")
        except IndexError:
            # If this didn't work either, just select at random.
            print("Unable to resolve. Selecting a genre at random...")
            selected_genre = choice(valid_genres)
            print("New genre: " + selected_genre)

    return selected_genre


def main():
    start_index = 1
    threshold = 1
    # You can optionally include your own custom threshold value.
    while start_index < len(argv):
        try:
            threshold = int(argv[start_index])
            start_index = start_index + 1
        except ValueError:
            break
    # trim our arguments to only include what should be the genre name
    args = argv[start_index:]

    # Get a Spotify API token
    access_token = get_token()
    selected_genre = select_genre(args)

    print("Searching...")

    result = None
    for ctr in range(255):
        temp_result = request_valid_song(access_token, genre=selected_genre)
        print_step(ctr)
        if validate(temp_result, threshold):
            result = temp_result
            break

    if result is not None:
        artist = result['artists']
        print(result['name'] + " – " + artist[0]['name'] + " (Popularity " + str(result['popularity']) + ")")
        try:
            print("URL: " + result['preview_url'])
        except TypeError:
            print("(No preview url to print.)")
    else:
        print("No song found.")


if __name__ == '__main__':
    main()
