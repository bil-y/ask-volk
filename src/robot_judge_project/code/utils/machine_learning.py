#!/usr/bin/python3
#
# Machine learing tasks for this project
#
# Author: Pascal Schärli
#

import string
from utils.utils import verbwrap
from collections import Counter
import numpy as np

from nltk import ngrams

from sklearn.metrics import mean_squared_error, accuracy_score

from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.models import Model

from textblob import TextBlob

# List of language splits for every canton
# Source: https://www.bfs.admin.ch/bfs/de/home/statistiken/bevoelkerung/sprachen-religionen/sprachen.assetdetail.7226714.html
language_splits = {
    "Zürich": {"de": 0.822, "fr": 0.032, "it": 0.059},
    "Bern": {"de": 0.843, "fr": 0.106, "it": 0.031},
    "Luzern": {"de": 0.888, "fr": 0.018, "it": 0.031},
    "Uri": {"de": 0.935, "fr": 0.0, "it": 0.026},
    "Schwyz": {"de": 0.895, "fr": 0.019, "it": 0.033},
    "Obwalden": {"de": 0.915, "fr": 0.02, "it": 0.011},
    "Nidwalden": {"de": 0.921, "fr": 0.017, "it": 0.021},
    "Glarus": {"de": 0.866, "fr": 0.009, "it": 0.072},
    "Zug": {"de": 0.815, "fr": 0.035, "it": 0.037},
    "Freiburg": {"de": 0.278, "fr": 0.688, "it": 0.023},
    "Solothurn": {"de": 0.884, "fr": 0.026, "it": 0.049},
    "Basel-Stadt": {"de": 0.781, "fr": 0.05, "it": 0.063},
    "Basel-Landschaft": {"de": 0.874, "fr": 0.033, "it": 0.051},
    "Schaffhausen": {"de": 0.884, "fr": 0.017, "it": 0.036},
    "Appenzell A.-Rh.": {"de": 0.913, "fr": 0.012, "it": 0.021},
    "Appenzell I.-Rh.": {"de": 0.936, "fr": 0.0, "it": 0.024},
    "St. Gallen": {"de": 0.88, "fr": 0.012, "it": 0.037},
    "Graubünden": {"de": 0.741, "fr": 0.015, "it": 0.131},
    "Aargau": {"de": 0.87, "fr": 0.018, "it": 0.054},
    "Thurgau": {"de": 0.896, "fr": 0.012, "it": 0.043},
    "Tessin": {"de": 0.105, "fr": 0.048, "it": 0.888},
    "Waadt": {"de": 0.058, "fr": 0.834, "it": 0.054},
    "Wallis": {"de": 0.249, "fr": 0.682, "it": 0.039},
    "Neuenburg": {"de": 0.055, "fr": 0.876, "it": 0.061},
    "Genf": {"de": 0.046, "fr": 0.808, "it": 0.065},
    "Jura": {"de": 0.061, "fr": 0.902, "it": 0.032}
}


def normalize(token):
    """Normalize Token. Get Lemma (base form) and remove any punctuation.

    Parameters
    ----------
    token : spacy.Token
        The input spacy token

    Returns
    -------
    str
        Normalized form of the token
    """
    lemma = token.lemma_
    nopunct = lemma.translate(str.maketrans('', '', string.punctuation))
    return nopunct


def get_language_results(ballot, language):
    """Get results for a specific language of a ballot. Goes through results of every
    canton and weights them according to the language splits found at
    https://www.bfs.admin.ch/bfs/de/home/statistiken/bevoelkerung/sprachen-religionen/sprachen.assetdetail.7226714.html


    Parameters
    ----------
    ballot : dict
        Dictionary of the ballot which contains the results per canton

    language : str
        Either "de" for German, "fr" for French or "it" for Italian. The target language for the results

    Returns
    -------
    dict
        A dictionary containing the results for all data types in the ballot dictionary.
        Example output:
        {
            "participation":0.7,
            "yes":0.4,
            "no":0.3
        }
    """
    out = {}
    # We need to store the total weight in order to normalize the result
    # to a value between 0 and 1 at the end.
    total_weight = 0
    for result in ballot["cantonal"]:
        # We want to return everything except the name of the canton and the total participating voters
        data_titles = [key for key in result.keys() if key not in ["canton", "total voters"]]
        canton = result["canton"]

        # The cantonal data also contains the data for all cantons in switzerland, but we skip this entry
        if canton != "Schweiz":
            # The weight is the number of people that speak that language in the selected canton
            weight = float(language_splits[canton][language]) * float(result["total voters"])
            total_weight += weight

            # we go through all data titles (data titles are "participation", "yes","no")
            for data_title in data_titles:
                if data_title not in out:
                    out[data_title] = []
                rel_data = weight * float(result[data_title]) / float(result["total voters"])
                out[data_title].append(rel_data)

    # Divide all outputs through the total weight in order to get a result between 0 and 1
    for data_title in out.keys():
        out[data_title] = sum(out[data_title]) / total_weight

    return out


@verbwrap
def extract_attributes(data_english, verbose=False):
    """Extracts text attributes from the data. The extracted attributes are polarity,  subjectivity and average sentence length.
    The data texts have to be translated into english in order to apply sentiment analysis on them.


    Parameters
    ----------
    data_english : dict
        Dictionary containing the combined data where every text is translated to english.


    verbose : bool
        Whether the program should display its progress to the user or not.

    Returns
    -------
    dict
        Dictionary holding all attributes. The dictionary is structured as follows,
        words enclosed in <tags> are meant to be placeholders:
        {
            <chapter title>:{
                "de":{
                    <ballot_nr>:{
                        "attributes":{
                            "polarity":<polarity (float)>,
                            "subjectivity":<subjectivity (float)>,
                            "sentence_length":<sentence length (float)>,
                        },
                        "results":{
                            "participation":<participation (float)>,
                            "yes":<yes (float)>,
                            "no":<no (float)>
                        }
                    },
                    <ballot_nr>:{...},
                    ...
                },
                "fr":{ ... },
                "it":{ ... },
            },
            <title>:{ ... },
            ...
        }
    """

    out = {}

    for ballot_nr, ballot_data in data_english.items():
        for language, leaflet in ballot_data["leaflets"].items():
            results = get_language_results(ballot_data, language)
            for title, text in leaflet.items():
                if title not in out:
                    out[title] = {}
                if language not in out[title]:
                    out[title][language] = {}
                # Get the TextBlob of our text for sentiment analysis
                blob = TextBlob(text)
                polarity = blob.polarity
                subjectivity = blob.subjectivity
                # Calculate the average sentence length
                sentence_length = np.mean([len(sentence.words) for sentence in blob.sentences])

                # Add the attributes to the output dict
                out[title][language][ballot_nr] = {
                    "attributes": {
                        "polarity": polarity,
                        "subjectivity": subjectivity,
                        "sentence_length": sentence_length
                    },
                    "results": results
                }
        if verbose:
            print("  gotten attributes for {}".format(ballot_nr))
    return out


@verbwrap
def get_training_data(data, num_features=200, n_gram_size=3, verbose=False):
    """Returns vectorized training data that can be used to feed our neural networks


    Parameters
    ----------
    data : dict
        Dictionary containing the combined data

    num_features : int
        How many features our output array should have

    n_gram_size : int
        The size of the n-grams used to vectorize the text

    verbose : bool
        Whether the program should display its progress to the user or not.

    Returns
    -------
    (dict, dict)
        Two dicts X, y containing first the X (features) and then the y (results)  data for our neural networks,
        words enclosed in <tags> are meant to be placeholders.

        Structure X:
        {
            "de":{
                <chapter title>: <N x 200 numpy array>
                ...
            },
            "fr":{...},
            "it":{...}
        }

        Structure y:
        {
            "de":{
                "participation":<participation (float)>
                "yes":<yes (float)>
                "no":<no (float)>
                "passed":<passed (0 or 1)>
            },
            "fr":{...},
            "it":{...}
        }
    """

    # A list of all n_grams of a language, used to get most common n_grams
    n_grams_concat = {"de": [], "fr": [], "it": []}

    # A list of all n_grams for a specific chapter
    n_grams = {"de": {}, "fr": {}, "it": {}}

    for ballot_nr, ballot_data in data.items():
        for language, leaflet in ballot_data["leaflets"].items():
            for title, spacy_document in leaflet.items():

                if title not in n_grams[language]:
                    n_grams[language][title] = {}

                tokens = []

                # Go through all tokens fo the current document
                for token in spacy_document:
                    # Ignore spaces (newlines etc) and punctuation
                    if not token.is_punct and not token.is_space:
                        tokens.append(token)
                        norm = normalize(token)

                # Get all ngrams ending in either a noun or a verb
                noun_verb_ngrams = []
                for ngram in ngrams(tokens, n_gram_size):  # iterate over all 3-grams
                    if ngram[-1].pos_ in ["NOUN", "VERB"]:  # check if last word is a noun or a verb
                        curr_ngram = (normalize(ngram[0]),
                                      normalize(ngram[1]),
                                      normalize(ngram[2]))
                        noun_verb_ngrams.append(curr_ngram)

                        # Add our ngram to the list containing all ngrams of that language
                        n_grams_concat[language].append(curr_ngram)

                # Add our ngram to the list containing all ngrams of that specific text
                n_grams[language][title][ballot_nr] = noun_verb_ngrams

                if verbose:
                    print("  lemmatized {}_{}".format(ballot_nr, language))

    # Out output dictionaries
    X = {"de": {}, "fr": {}, "it": {}}
    y = {"de": {}, "fr": {}, "it": {}}
    for language, title_ngrams in n_grams.items():

        # Get the most common ngrams for that language
        most_common = Counter(n_grams_concat[language]).most_common(num_features)

        if verbose:
            print("Most common n-grams for {}".format(language))
            print(language, most_common)

        for title, ballot_nr_ngrams in title_ngrams.items():

            # every chapter of every language will get a list of features
            if title not in X[language]:
                X[language][title] = []

            # The y data will be a list of output values, for every data type
            # (data types = participation, yes, no)
            if title not in y[language]:
                y[language][title] = {}

            # Go through all ballots and process their ngrams which were calculated in the previous step.
            for ballot_nr, n_grams in ballot_nr_ngrams.items():
                #
                # X
                #
                most_frequent = Counter(n_grams)

                features = np.zeros(len(most_common))
                for i in range(len(most_common)):
                    ngram = most_common[i][0]
                    if ngram in most_frequent:  # Only add most common 3-gram frequencies
                        features[i] = most_frequent[ngram]

                # Add features to our X dictionary
                X[language][title].append(features)

                #
                # y
                #

                # Firstly, get the results adapted to the current language_result
                language_results = get_language_results(data[ballot_nr], language)

                # Append all y lists with the values for the differnt data titles.
                # (data types = participation, yes, no)
                for data_title in language_results.keys():
                    if data_title not in y[language][title]:
                        y[language][title][data_title] = []
                    y[language][title][data_title].append(language_results[data_title])

                # Add a new list, containing wether the ballot passed for this language or not
                if "passed" not in y[language][title]:
                    y[language][title]["passed"] = []

                if y[language][title]["yes"][-1] > y[language][title]["no"][-1]:
                    y[language][title]["passed"].append(1)
                else:
                    y[language][title]["passed"].append(0)

                if verbose:
                    print("  extracted {}_{}".format(ballot_nr, language))

            # Convert X arrays to numpy arrays and normalize them
            X[language][title] = np.array(X[language][title])
            X[language][title] = X[language][title] / np.std(X[language][title], axis=0)

            # Convert y values to numpy arrays aswell
            for data_title in y[language][title].keys():
                y[language][title][data_title] = np.array(y[language][title][data_title])
    return X, y


@verbwrap
def neural_network(X, y, split=.1, verbose=False):
    """Trains a neural network on our input data dicionaries and returns the result.


    Parameters
    ----------
    X : dict
        Dictionary containing the X training data

    y : dict
        Dictionary containing the y training data

    split : float
        The test/train split.

    verbose : bool
        Whether the program should display its progress to the user or not.

    Returns
    -------
    dict
        A dictionary containing the results of the machine learning,
        words enclosed in <tags> are meant to be placeholders:

        {
           "X shape": <tuple>,
           "X nonzero": <string, "nonzero/arena">,
           "total voters": {"mse": <float> },
           "participation": {"mse": <float> },
           "yes": {"mse": <float> },
           "no": {"mse": <float>},
           "passed": { "accuracy": <float>}
        }

    """
    X[np.isnan(X)] = 0

    # Shuffle Dataset
    permutation = np.random.permutation(X.shape[0])
    X = X[permutation]
    for data_type in y.keys():
        y[data_type] = y[data_type][permutation]

    # Split into test & train dataset
    test_amount = int(X.shape[0] * split)

    # Split the data
    test_X = X[:test_amount]
    train_X = X[test_amount:]

    test_y = {}
    train_y = {}

    # Get shape and sparsity of our input tensor
    dim = X.shape
    area = dim[0] * dim[1]
    x_zero = np.count_nonzero(X == 0)
    results = {"X shape": dim, "X nonzero": "{}/{}".format(area - x_zero, area)}

    for data_type in y.keys():
        # Split the y data
        test_y[data_type] = y[data_type][:test_amount]
        train_y[data_type] = y[data_type][test_amount:]

        # Get input dimension for the Input layers
        input_dim = train_X.shape[1]

        # Check if the data is binary or not
        binary = True
        for data in y[data_type]:
            if data != 1 and data != 0:
                binary = False
                break

        # If the output is binary, compile the model with binary crossentropy as its loss function
        if binary:
            layer_1 = Input((input_dim,), name="input_layer")
            layer_2 = Dense(100)(layer_1)
            layer_3 = Dense(1, activation="softmax", name="output_layer")(layer_2)
            model = Model(layer_1, layer_3)

            model.compile(loss="binary_crossentropy",
                          optimizer="sgd",
                          metrics=['accuracy'])

        # If the output is non-binary, compile the model with mse as its loss function
        else:
            layer_1 = Input((input_dim,), name="input_layer")
            layer_2 = Dense(100)(layer_1)
            layer_3 = Dense(1, activation="relu", name="output_layer")(layer_2)
            model = Model(layer_1, layer_3)

            model.compile(loss='mean_squared_error', optimizer='sgd')

        # Train the model
        model.fit(x=train_X, y=train_y[data_type],
                  batch_size=64, epochs=30,
                  validation_data=(test_X, test_y[data_type]),
                  verbose=0)

        # Make predictions
        y_pred = model.predict(test_X).reshape(-1)

        # Add either accuracy or mse to the results dictionary
        results[data_type] = {}
        if binary:
            results[data_type]["accuracy"] = float(accuracy_score(y_pred, test_y[data_type]))
        else:
            results[data_type]["mse"] = float(mean_squared_error(y_pred, test_y[data_type]))

        if verbose:
            print("  trained on {}".format(data_type))

    return results
