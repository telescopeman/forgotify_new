"""
Module that makes use of the Spotify Web API to retrieve songs below a selected
'threshold' of popularity.
Genres list scrapped from: http://everynoise.com/everynoise1d.cgi?scope=all&vector=popularity
Spotify Ref: https://developer.spotify.com/documentation/web-api/reference-beta/#category-search

"""
from json import load, loads
from random import choice, randint
from sys import argv

from fuzzysearch import find_near_matches

from api_manager import get_token, get_song
from exceptions import NoMatchError

# Wildcards for random search
RANDOM_WILDCARDS = ['%25a%25', 'a%25', '%25a',
                    '%25e%25', 'e%25', '%25e',
                    '%25i%25', 'i%25', '%25i',
                    '%25o%25', 'o%25', '%25o',
                    '%25u%25', 'u%25', '%25u']


def request_valid_song(authorization_header: dict, genre: str) -> dict:
    wildcard = choice(RANDOM_WILDCARDS)

    # Make a request for the Search API with pattern and random index

    genre_str = "%20genre:%22{}%22".format(genre.replace(" ", "%20"))
    for i in range(90):
        offset = randint(0, 200)
        song_request = get_song(wildcard, genre_str, offset, authorization_header)
        try:
            song: dict = choice(loads(song_request.text)['tracks']['items'])
            return song
        except IndexError:
            # the reason we're looping here is to find one ''without'' an IndexError.
            continue

    raise RuntimeError("Exceeded request limit!")


def validate(track: dict, threshold: int) -> bool:
    if int(track['popularity']) < threshold:
        # Might introduce a more thorough check later...
        return True
    else:
        return False


""" 
Displays a message for each step of the search process. 
This is completely aesthetic and doesn't really matter for the program.
"""


def print_step(step: int):
    line_length = 17
    if step % line_length == 0:
        print()
        mega_step = step / line_length
        # Must be an integer ^
        if mega_step == 0:
            header = "Searching"
        elif mega_step < 3:
            header = "Still searching"
        elif mega_step < 6:
            header = "Yet still searching"
        elif mega_step < 10:
            header = "And yet still searching"
        elif mega_step < 20:
            header = "Continuing searching"
        else:
            header = "This is taking a while - you may want to restart the app"

        print(header + "...", end="")
    else:
        print(".", end="")


def select_genre(input_genre) -> str:
    """
    :rtype: str
    """
    # Open genres file
    with open('genres.json', 'r') as infile:
        valid_genres = load(infile)

    """
    If genre was specified by command line argument, choose it.
    Otherwise, choose randomly. It's seemingly not possible to make it
    any genre, or else it starts bugging out and giving random pop songs.
    """
    try:
        if len(input_genre) == 0 or input_genre[0] == "":
            raise NoMatchError("Empty genre field.")
        else:
            selected_genre = (" ".join(input_genre)).lower()

            # Make sure this is a valid genre...
            if selected_genre not in valid_genres:
                # If genre not found as it is, try fuzzy search with Levenhstein distance 2
                print("Genre entered was '" + selected_genre + "', which is not in the list of genres supported. "
                                                               "Attempting to find similar genre via fuzzy search...")
                valid_genres_to_text = " ".join(valid_genres)
                near_matches = find_near_matches(selected_genre, valid_genres_to_text, max_l_dist=2)
                try:
                    first_match = near_matches[0]
                except IndexError:
                    raise NoMatchError("Fuzzy search failed.")

                """
                We make sure to .strip() the whitespace from both 
                sides of the genre name. Without this, the genre
                name may end up malformed.
                """
                selected_genre = first_match.matched.strip()

                if selected_genre in valid_genres:
                    print("New genre is '" + selected_genre + "'.")
                else:
                    # If by some bizarre bug, it's still malformed, default to random again.
                    raise NoMatchError("Fuzzy search failed.")

    except NoMatchError as e:
        # If all else fails, we should just get a random genre from the list.
        print(e, end=" ")
        print("Selecting a new genre at random...")
        selected_genre = choice(valid_genres)
        print("New genre: " + selected_genre)

    return selected_genre


def main():
    """
    This is the lowest allowed threshold, because anything lower than this
    will mean the program will never complete.
    """
    lowest_allowed_threshold: int = 1

    """
    Our default threshold without any command line inputs is the same 
    as the lowest allowed.
    """
    threshold = lowest_allowed_threshold

    start_index: int = 1

    """
    You can optionally include your own custom threshold value.
    The following code handles this in the command line and makes
    sure the input is safe.
    """
    while start_index < len(argv):
        raw_value: str = argv[start_index]
        try:
            # If the current argument is a number, this should be fine.
            # Set the threshold to be the inputted number.
            sanitized_value = int(raw_value)
        except ValueError:
            """
            If it is not convertable to a number, we've reached the 
            genre names in the input - quit this loop.
            """
            break

        if sanitized_value < lowest_allowed_threshold:
            raise ValueError("Threshold value '" + raw_value +
                             "' is too low to find any songs!" +
                             " Must be " +
                             str(lowest_allowed_threshold) +
                             " or higher!")

        threshold = sanitized_value
        start_index = start_index + 1

    # Get a Spotify API token:
    access_token = get_token()
    # Convert it to an authorization header:
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Trim our arguments to only include what should be the genre name
    input_genre = argv[start_index:]
    # Get genre from command line input
    selected_genre = select_genre(input_genre)

    result = None
    for ctr in range(20000):
        # Get a random song in the genre.
        temp_result = request_valid_song(authorization_header, genre=selected_genre)
        # Update the console to show the user something is indeed happening
        print_step(ctr)
        if validate(temp_result, threshold):
            # If it's at the right level of popularity, this is our song.
            result = temp_result
            break

    # Go to new line
    print("")
    if result is not None:
        artist = result['artists']
        print(result['name'] + " – " + artist[0]['name'] + " (Popularity " + str(result['popularity']) + ")")
        try:
            print("Preview URL: " + result['preview_url'])
        except TypeError:
            print("(No preview URL.)")
    else:
        print("No song found.")


if __name__ == '__main__':
    main()
