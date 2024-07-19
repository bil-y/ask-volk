import spacy
from utils.utils import verbwrap
from googletrans import Translator
import os
import json


@verbwrap
def spacyfy(data, verbose=False):
    """Processes all text in the data dict using spacy in place.

    Parameters
    ----------
    data : dict
        Dictionary containing the combined data from data/data.json

    verbose : bool
        Whether the program should display its progress to the user or not.

    Returns
    -------
    dict
        Returns the changed dictionary.
    """
    nlps = {
        "de": spacy.load('de'),  # requires: python -m spacy download de
        "fr": spacy.load('fr'),  # requires: python -m spacy download fr
        "it": spacy.load('it'),  # requires: python -m spacy download it
    }

    for ballot_nr, ballot_data in data.items():
        for language, leaflet in ballot_data["leaflets"].items():
            for title, text in leaflet.items():
                # Parse the text using spacy
                data[ballot_nr]["leaflets"][language][title] = nlps[language](text)
        if verbose:
            print("  processed {}".format(ballot_data["id"]))
    return data


def translate_data(data, data_english_json):
    if os.path.exists(data_english_json):
        with open(data_english_json) as f:
            data_english = json.load(f)
        return data_english
    else:
        data_english = {}

    translator = Translator()

    for ballot_nr, ballot_data in data.items():
        if ballot_nr not in data_english:
            data_english[ballot_nr] = data[ballot_nr]
            for language, leaflet in ballot_data["leaflets"].items():
                for title, text in leaflet.items():
                    try:
                        text_en = translator.translate(text, dest="en").text
                    except:
                        text_en = []
                        words = text.split(" ")
                        for i in range(0, len(words), 300):
                            split = " ".join(words[i:min(len(words), i + 300)])
                            text_en.append(translator.translate(split, dest="en").text)
                        text_en = " ".join(text_en)
                    data_english[ballot_nr]["leaflets"][language][title] = text_en
                print("  translated {} {}".format(ballot_nr, language))
            with open(data_english_json, "w+") as f:
                f.write(json.dumps(data_english, indent=" ", ensure_ascii=False))

    return data_english
