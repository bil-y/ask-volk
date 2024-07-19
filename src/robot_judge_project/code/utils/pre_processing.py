#!/usr/bin/python3
#
# Processes the downloaded data so that its usable for data analysis
#
# Author: Pascal Schärli
#

import os
import subprocess
import re
import json
from fuzzywuzzy import fuzz


from utils.utils import verbwrap


@verbwrap
def convert_to_text(folder_pdf, folder_txt, verbose=False):
    """Converts all pdf leaflets into text files using pdftotext
    Requirs pdftotext to be installed on your system

    Parameters
    ----------
    folder_pdf : str
        The folder containing pdf files

    folder_txt : str
        The output folder for all text files.

    verbose : bool
        Whether the program should display its progress to the user or not.

    Returns
    -------
    None
    """

    # Check that the given pdf folder exists
    if not os.path.exists(folder_pdf):
        raise ValueError("The given PDF folder does not exist yet! ({})".format(folder_pdf))

    # Create our output folder if it does not exist yet
    if not os.path.exists(folder_txt):
        os.makedirs(folder_txt)

    # Iterate over all files contained in the folder
    for file_name in os.listdir(folder_pdf):
        # If the file ends with .pdf, convert it to text
        if file_name.lower().endswith(".pdf"):
            in_path = os.path.join(folder_pdf, file_name)
            out_path = os.path.join(folder_txt, file_name.replace(".pdf", ".txt"))
            if not os.path.exists(out_path):
                # Calls the converter and saves the output file in the output folder
                subprocess.call(["pdftotext", "-enc", "UTF-8", in_path, out_path])
                if verbose:
                    print("  converted {}".format(file_name))


def clean_up(text):
    """Cleans up a text. This is used before adding the texts to our database,
    to remove all unneccessary newlines, double spaces and other unwanted characters.

    Parameters
    ----------
    text : str
        The text we want to clean

    Returns
    -------
    str
        A string containing the cleaned version of the text.
    """

    # A dictionary with strings as keys and their replacements as values
    replacements = {
        "\xad\n": "",
        "\n\xad ": "",
        "\xad": "",
        "\n": " ",
        "  ": " ",
        "¬": "",
        "’": "'"
    }

    for s, r in replacements.items():
        text = text.replace(s, r)
    return text.strip()


def get_parts(file_path):
    """
    Parameters
    ----------
    file_path : str
        The file path for the text file we want to extract the text from

    Returns
    -------
    dict
        A dictionary containing all chapters of this text file. If it could not get any
        chapters this returns an empty dictionary {}.
        If it could the could look like as follows, where "..." would be replaced with the actual text in the leaflet:
        {
            "de":{
               "Volksinitiative «Ja zur Aufhebung der Wehrpflicht»": {
                "short_summary": "...",
                "detail": "...",
                "legal": "...",
                "initiative": "...",
                "council": "..."
               },
               "Bundesgesetz über die Bekämpfung übertragbarer Krankheiten des Menschen (Epidemiengesetz)": {
                "short_summary": "...",
                "detail": "...",
                "council": "...",
                "legal": "...",
               },
               "Änderung des Arbeitsgesetzes": {
                "short_summary": "...",
                "detail": "...",
                "council": "...",
                "legal": "...",
               }
            }
        }

    """
    delimiters = {
        "de": {
            "subject": "Vorlage",
            "short_summary": "Das Wichtigste in Kürze",
            "detail": "Die Vorlage im Detail",
            "council": "Die Argumente des Bundesrates",
            "initiative": "Die Argumente des Initiativkomitees",
            "referendum": "Die Argumente des Referendumskomitees",
            "parlament": "Die Beratungen im Parlament",
            "legal": "§"
        },
        "fr": {
            "subject": "Objet",
            "short_summary": "L'essentiel en bref",
            "detail": "L'objet en détail",
            "council": "Les arguments du Conseil fédéral",
            "initiative": "Les arguments du comité d'initiative",
            "referendum": "Les arguments du comité référendaire",
            "parlament": "Les délibérations du Parlement",
            "parlament2": "Débats parlementaires",
            "legal": "§"
        },
        "it": {
            "subject": "Oggetto",
            "short_summary": "L'essenziale in breve",
            "detail": "Il progetto in dettaglio",
            "council": "Gli argomenti del Consiglio federale",
            "initiative": "Gli argomenti del comitato d'iniziativa",
            "referendum": "Gli argomenti del Comitato referendario",
            "parlament": "Le deliberazioni in Parlamento",
            "legal": "§"
        }
    }

    # Open the leaflet text file
    with open(file_path, encoding='utf-8') as f:
        raw_text = f.read()

    # Get the language of this leaflet from its filen name
    language = os.path.splitext(file_path)[0].split("_")[-1]

    # Create a regular expression that can match the delimiters between different subjects (ballots)
    subject_delimiters = "\n\f.*{}\n".format(delimiters[language]["subject"])
    subject_delimiters_re = re.compile(subject_delimiters, flags=re.IGNORECASE)

    # Split the leaflets into the individual subjects (ballots)
    ballots = re.split(subject_delimiters_re, raw_text)
    if len(ballots) == 1:  # only one subject
        ballots = [raw_text]
    else:
        ballots = ballots[1:]

    out = {}

    # Create a regular expression that can match delimiters between the leaflet pages
    page_delimiters = ["\n\f", "\nSeite [0-9]+\n"]  # older leaflets contain Seite X as a delimiter, regardless of the language
    page_delimiter_re = "" + "|".join(page_delimiters) + ""
    page_delimiters_re = re.compile(page_delimiter_re, flags=re.IGNORECASE)

    for ballot in ballots:
        try:
            # Split the ballot into its chapters (pages)
            chapters = page_delimiters_re.split(ballot)

            # The title is contained on the first line of the first page in every ballot.
            title = chapters[0].split("\n\n")[0]

            title = clean_up(title)

            out[title] = {}

            # Go through all chapters
            for chapter in chapters[1:]:

                # Clean up the text of that chapter
                chapter = clean_up(chapter)

                # Go through all delimiters for this language
                for delimiter_name, delimiter_text in delimiters[language].items():

                    # There might be multiple delimiter names for the same thing (parlament, parlament2 in french)
                    # The ending digits are being removet from the name
                    delimiter_name = re.sub(r"[0-9]+$", "", delimiter_name)

                    # Check if this chapter title appears in this chapter or not
                    delimiter_re = re.compile(delimiter_text, flags=re.IGNORECASE)
                    if delimiter_name != "subject" and re.search(delimiter_re, chapter):
                        # The chapter title gets removet from the text
                        chapter = re.sub(delimiter_re, "", chapter)
                        # Then the chapter gets cleaned up and added to the output dict
                        out[title][delimiter_name] = clean_up(chapter)

            # If the output dictionary is empty, delete it
            if not out[title]:
                del out[title]
        except Exception as e:
            print("  exception:", file_path, e)

    # Check wether we could get any chapters or not
    if out:
        return {language: out}
    else:
        return {}


@verbwrap
def extract_content(folder_txt, json_path, verbose=False):
    """Extracts all leaflet contents from a folder holding the leaflet textfiles into a JSON file.

    Parameters
    ----------
    folder_txt : str
        The folder containing the leaflet txt files

    json_path : str
        The output path for the JSON file.

    verbose : bool
        Whether the program should display its progress to the user or not.

    Returns
    -------
    None
    """

    # Checkif the output file already exists.
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding='utf-8') as f:
                out = json.loads(f.read())
        except json.JSONDecodeError:
            out = {}
    else:
        # Create the directory to the json file if it does not exist yet
        directory = os.path.dirname(json_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        out = {}

    # Go through all files stored in that folder
    for file_name in sorted(os.listdir(folder_txt)):
        # Check if the file is a text file
        if file_name.lower().endswith(".txt"):
            # Extract the date from the filename
            date = file_name.split("_")[0]
            full_path = os.path.join(folder_txt, file_name)

            # Get all parts for this specific file.
            parts = get_parts(full_path)
            if parts:
                # Update the output dictionary
                if date in out:
                    out[date].update(parts)
                else:
                    out[date] = parts
                if verbose:
                    print("  extracted {}".format(file_name))
            elif verbose:
                print("  couldn't extract from {}".format(file_name))
                print(f"parts: {parts}")

    # Write the dictionary to our output file as JSON. ensure_ascii has to be false
    # In order to allow for umlaut and other special characters.
    with open(json_path, "w+", encoding='utf-8') as f:
        f.write(json.dumps(out, indent=" ", ensure_ascii=False))
    print('extracted content successfully')


def find_ballot_nr(metadata, ballot_id, title, language):
    """Tries to find the ballot nr for a specific ballot id, title and language.
    This uses a fuzzy string search in order to match up the correct titles.

    Parameters
    ----------
    metadata : dict
        The dictionary holding the metadata

    ballot_id : str
        The ballot id (date)

    title : str
        The title of the ballot

    language : str
        The language of the given title

    Returns
    -------
    str
        The nr of the best matching ballot
    """

    best_match_nr = None
    best_match_score = -1
    # Go through all votes in the metadata
    for ballot_nr, data in metadata.items():

        # Check if the id (date) matches
        if data["id"] == ballot_id:

            # Determine how similar the titles are
            score = fuzz.ratio(data["title_" + language], title)
            if score > best_match_score:
                best_match_score = score
                best_match_nr = ballot_nr

    # Return the ballot nr with the most similar title
    return best_match_nr


def data_merger(leaflet_json_file, metadata_json_file, merged_json_file, verbose=False):
    """Merges the leaflet texts and the metadata into one data file that combines both of them.

    Parameters
    ----------
    leaflet_json_file : str
        The path to the JSON file containing the extracted leaflets texts

    metadata_json_file : str
        The path to the JSON file containing the metadata (vote results)

    merged_json_file : str
        The file path for the output JSON file

    verbose : bool
        Whether the program should display its progress to the user or not.

    Returns
    -------
    None
    """

    # Load the leaflet contents
    with open(leaflet_json_file, errors='ignore') as f:
        leaflets_content = json.load(f)

    # Load the metadata
    with open(metadata_json_file) as f:
        metadata = json.load(f)

    # If the output file already exists, open it
    if os.path.exists(merged_json_file):
        with open(merged_json_file, errors='ignore') as f:
            out = json.loads(f.read())
    else:
        # If the output file does not exist make sure its parent directory
        # Exists
        directory = os.path.dirname(merged_json_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        out = {}

    # Go through all leaflets
    for date, leaflet_content in leaflets_content.items():
        ballot_id = date.replace("-", "")
        for language in ["de", "fr", "it"]:
            if language in leaflet_content:
                leaflet = leaflet_content[language]
                for title, content in leaflet.items():

                    # Get the vote id for every ballot text
                    vote_id = find_ballot_nr(metadata, ballot_id, title, language)

                    if vote_id is not None:
                        if vote_id not in out:
                            # Add the leaflets and metadata to the output dictionary
                            out[vote_id] = metadata[vote_id]
                            out[vote_id]["leaflets"] = {}
                        out[vote_id]["leaflets"][language] = content

    # Write the dictionary to our output file as JSON. ensure_ascii has to be false
    # In order to allow for umlaut and other special characters.
    with open(merged_json_file, "w+") as f:
        f.write(json.dumps(out, indent=" ", ensure_ascii=False))


@verbwrap
def add_title_groups(merged_json_file, title_groups, verbose=False):
    """Goes through the merged json file again and groups up some chapter titles in order
    to get some longer chapters. The result is saven to the same file agian.

    Parameters
    ----------
    merged_json_file : str
        The path to the JSON file containing the merged data

    title_groups : list
        A list of chapter titles that should be grouped up

    verbose : bool
        Whether the program should display its progress to the user or not.

    Returns
    -------
    None
    """

    # Open merged data
    with open(merged_json_file) as f:
        data = json.load(f)

    # Go through all title groups
    for title_group in title_groups:
        # Get name for new chapter
        name = "+".join(title_group)
        for ballot_nr, ballot_data in data.items():
            for language, leaflet in ballot_data["leaflets"].items():
                add_text = []
                # Go through all chapters and check it the title is in the current title group
                for title, text in leaflet.items():
                    if title in title_group:
                        add_text.append(text)
                # if at leas one chapter of this group was found, create the new title group
                if len(add_text) > 0:
                    leaflet[name] = "\n\n".join(add_text)

    # Write the result to the merged data file again
    with open(merged_json_file, "w+") as f:
        f.write(json.dumps(data, indent=" ", ensure_ascii=False))
