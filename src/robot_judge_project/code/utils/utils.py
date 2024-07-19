#!/usr/bin/python3
#
# General utility functions
#
# Author: Pascal Schärli
#

import requests
import json


def get_stackoverflow_link(exception):
    """Gets a link to a stackoverflow post for a given exception type.
    """
    query = "python {}".format(exception)
    url = "https://api.stackexchange.com/2.2/search?order=desc&sort=relevance&site=stackoverflow&intitle={}".format(query)
    response = requests.get(url)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        if len(response_json["items"]) > 0:
            return response_json["items"][0]["link"]

    return None


def exception_catcher(function):
    """Decorator for exception catching. When an exception occurs it displays my contact information and a
    stackoverflow link to resolve the issue. If the user decides not to continue with the program, the
    exception gets raised, otherwise its supressed.
    """
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            print("Oops, an exception occured: {}".format(e))
            print("You can try messaging me per mail: pascscha@student.ethz.ch")
            stackoverflow_link = get_stackoverflow_link(e)
            if stackoverflow_link is not None:
                print("Or you can look it up on stackoverflow: {}".format(stackoverflow_link))

            choice = input("Would you like to continue with the program? (y/n) ")
            if choice != "y":
                raise e
    return wrapper


def create_title(name):
    """Creates a title from a function name in snake_case.
    Example: snake_case -> Snake Case
    """
    return name.replace("_", " ").title()


def verbwrap(function):
    """Wraps functions that are be verbose. Prints a message when they start and when they end.
    """
    @exception_catcher
    def wrapper(*args, verbose=False, **kwargs):
        if verbose:
            name = create_title(function.__name__)
            print("Start {}".format(name))
        result = function(*args, verbose=verbose, **kwargs)
        if verbose:
            print("Done")
        return result
    return wrapper
