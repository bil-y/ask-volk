#!/usr/bin/python3
#
# Main file, all methods are started from this file.
#
# Author: Pascal Schärli
#

import os
import json
import pickle
from utils.utils import create_title
from utils.post_processing import spacyfy, translate_data
from utils.machine_learning import get_training_data, extract_attributes, neural_network
from utils.visualization import plot_attributes, plot_part_yes_no, plot_part_yes_no_bar

# All file paths used in this project
data_json = "data/data.json"
data_english_json = "data/data_english.json"
data_pickle = "data/data.pickle"
X_pickle = "data/X.pickle"
y_pickle = "data/y.pickle"
attributes_json = "data/attributes.json"
ml_results_json = "data/neural_net_results.json"
metadata_json = "data/json/metadata.json"

plot_sentiments_dir = "plots/sentiments"
plot_metadata_dir = "plots/metadata"


def get_data():
    """Gets the data file containing the combined text and voting data. Asks to download the file if it does not exist yet.

    Returns
    -------
    dict
        dictionary containing the combined text and voting data.
    """
    # Check if file already exists
    if not os.path.exists(data_json):
        answer = input("The data file {} does not exist yet. Would you like to download the necessary files? (y/n) ".format(data_json))
        if answer.lower().strip() == "y":
            import download_data
            # download data
            download_data.main()
        else:
            print("Exiting")
            exit()

    # Open data
    with open(data_json) as f:
        data = json.load(f)

    return data


def get_data_english():
    data = get_data()
    return translate_data(data, data_english_json)


def get_spacyfied_data():
    """Gets the spacyfied data file containing the combined text and voting data. If a chached pickle file exists,
    it asks wether to load this file.

    Returns
    -------
    dict
        dictionary containing spacified data dict.
    """

    if os.path.exists(data_pickle):
        answer = input("Do you want to load the pickled, spacyfied data file? (y/n) ")
        if answer.lower().strip() == "y":
            with open(data_pickle, "rb") as f:
                data = pickle.load(f)
            return data

    data = get_data()
    spacyfy(data)

    with open(data_pickle, "wb+") as f:
        pickle.dump(data, f)

    return data


def get_X_y():
    """Gets X and y dictionaries contiainting the training data which is used to do the machine learing tasks. If a chached pickle file exists,
    it asks wether to load this file.

    Returns
    -------
    dict
        X, y dictionaries
    """

    if os.path.exists(X_pickle) and os.path.exists(y_pickle):
        answer = input("Do you want to load the pickled X and y tensors? (y/n) ")
        if answer.lower().strip() == "y":
            with open(X_pickle, "rb") as f:
                X = pickle.load(f)
            with open(y_pickle, "rb") as f:
                y = pickle.load(f)
            return X, y

    data = get_spacyfied_data()
    X, y = get_training_data(data, verbose=True)

    with open(X_pickle, "wb+") as f:
        pickle.dump(X, f)
    with open(y_pickle, "wb+") as f:
        pickle.dump(y, f)

    return X, y


def get_attributes():
    """Gets sentiment and complexity attributes for the data.
    Also asks wether to load the already existing attributes file.

    Returns
    -------
    dict
        attributes containing sentiment and complexity of our data
    """
    if os.path.exists(attributes_json):
        answer = input("Do you want to load the existing attributes file? (y/n) ")
        if answer.lower().strip() == "y":
            with open(attributes_json) as f:
                attributes = json.load(f)
            return attributes

    data_english = get_data_english()
    attributes = extract_attributes(data_english, verbose=True)
    with open(attributes_json, "w+") as f:
        f.write(json.dumps(attributes, indent=" ", ensure_ascii=False))
    return attributes


def get_metadata():
    """Gets the metadata data file containing. Asks to download the file if it does not exist yet.

    Returns
    -------
    dict
        dictionary containing the metadata.
    """
    # Check if file already exists
    if not os.path.exists(metadata_json):
        answer = input("The metadata file {} does not exist yet. Would you like to download the necessary files? (y/n) ".format(metadata_json))
        if answer.lower().strip() == "y":
            import download_data
            # download data
            download_data.main()
        else:
            print("Exiting")
            exit()

    # Open data
    with open(metadata_json) as f:
        metadata = json.load(f)

    return metadata


def neural_net_n_grams():
    """Trains a neural network on ngrams of our data. The results are written to the disk.
    """
    X, y = get_X_y()

    errors = {}
    for language in y.keys():
        errors[language] = {}
        for title in y[language].keys():
            if len(X[language][title]) > 50:
                result = neural_network(X[language][title], y[language][title], verbose=True)
                errors[language][title] = result

    print(errors)

    with open(ml_results_json, "w+") as f:
        f.write(json.dumps(errors, indent=" "))


def sentiment_plots():
    """Plots attributes agianst all chapter and language pairs
    """
    attributes = get_attributes()
    plot_attributes(attributes, plot_sentiments_dir, verbose=True)


def metadata_plots():
    """Plots metadata
    """
    metadata = get_metadata()
    plot_part_yes_no(metadata, plot_metadata_dir, verbose=True)
    plot_part_yes_no_bar(metadata, plot_metadata_dir, bucket_size=20, verbose=True)


if __name__ == "__main__":
    # List of functions that we can do
    possible_functions = [neural_net_n_grams, sentiment_plots, metadata_plots]

    # If there is only one option, run it directly
    if len(possible_functions) == 1:
        possible_functions[0]()

    else:
        # Otherwise display all functions and let the user choose which one to run
        print("Availabe functions:")
        for i, function in enumerate(possible_functions):
            name = create_title(function.__name__)
            print("{}: {}".format(i, name))

        choice = None
        while choice is None:
            try:
                choice = int(input("Which function would you like to run? "))
                if choice < 0 or choice >= len(possible_functions):
                    choice = None
            except Exception:
                pass
            if choice is None:
                print("invalid choice")

        # run the funcition
        possible_functions[choice]()
