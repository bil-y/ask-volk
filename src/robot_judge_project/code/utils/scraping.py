#!/usr/bin/python3
#
# Scrapers that fetch the data for this project
#
# Author: Pascal Schärli
#

import os
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

from utils.utils import verbwrap


@verbwrap
def download_leaflets(folder, verbose=False):
    """Downloads all leaflets as pdf files into the given folder

    Parameters
    ----------
    folder : str
        The target folder for the pdf files

    Returns
    -------
    None
    """

    # Create folder if it does not exist yet
    if not os.path.exists(folder):
        os.makedirs(folder)

    base_url = "https://www.bk.admin.ch"
    lang_urls = {"de": "bk/de/home/dokumentation/abstimmungsbuechlein.html",
                 "fr": "bk/fr/home/documentation/compilation-explications-Conseil%20f%C3%A9d%C3%A9ral-depuis-1978.html",
                 "it": "bk/it/home/documentazione/raccolta-delle-spiegazioni-del-consiglio-federale-dal-1978.html"}

    for lang, url in lang_urls.items():
        # Load Webpage
        raw = requests.get("{}/{}".format(base_url, url)).text
        soup = BeautifulSoup(raw, 'html.parser').find("body")  # There are some wrong links in the html header so we only look in the body
        links = soup.find_all("a")

        # Go through all links, we check whether it's a pdf or not later
        for link in links:
            if link.has_attr('href'):
                href = link['href']

                # Check wether the link points to a pdf or not
                if href.lower().endswith(".pdf"):

                    # need to change code, get leaflet ID from title, not href
                    title = link['title']
                    try:
                        date_str = title.split('(')[-1].split(')')[0]
                        date_obj = datetime.strptime(date_str, "%d.%m.%Y")
                        formatted_date = date_obj.strftime("%d%m%Y")
                        leaflet_id = str(formatted_date)
                    except ValueError:
                        print(f"failed to parse {title}")
                        continue

                    # Check if the ID is valid (only digits)
                    if leaflet_id.isdigit():
                        # Convert the leaflet ID to a more readable format (1996-05-22)
                        leaflet_id = re.sub(r'([0-9][0-9])([0-9][0-9])([0-9][0-9][0-9][0-9])', r'\3-\2-\1', leaflet_id)

                        # Create local filename from ID
                        file_name = os.path.join(folder, "{}_{}.pdf".format(leaflet_id, lang))

                        # Only download the file if we haven't downloaded it yet
                        if not os.path.exists(file_name):
                            # Download PDF to specified location
                            pdf_raw = requests.get("{}/{}".format(base_url, href))
                            with open(file_name, "wb+") as f:
                                f.write(pdf_raw.content)

                            if verbose:
                                print("  downloaded {}".format(file_name))
    print("leaflets successfully downloaded")


def get_id_nr_pairs():
    """Gets all paris of ballot ids and ballot nrs. This is needed in order to scrape the overviews and cantonal results.

    Returns
    -------
    dict
        A dict with the ballot nr  as keys and the ballot id as well as its title in all languages as the value.
        An example element of this dict could be the following:

        "305": ("19810405",(
                    "'Mitenand-Initiative für eine neue Ausländerpolitik'",
                    "Iniziativa popolare 'Essere solidali, per una nuova politica degli stranieri'",
                    "Initiative populaire  'Être solidaires en faveur d'une nouvelle politique à l'égard des étrangers'"
                    )
                )
    """

    # URLs with the list of ballots for every languages.
    url_de = "https://www.bk.admin.ch/ch/d/pore/va/vab_2_2_4_1_gesamt.html"
    url_fr = "https://www.bk.admin.ch/ch/f/pore/va/vab_2_2_4_1_gesamt.html"
    url_it = "https://www.bk.admin.ch/ch/i/pore/va/vab_2_2_4_1_gesamt.html"

    # URLs with the list of ballots for every languages.
    req_de = requests.get(url_de)
    req_fr = requests.get(url_fr)
    req_it = requests.get(url_it)

    # Only continue if the webpages could be loaded successfully
    if req_de.status_code != 200 or \
            req_fr.status_code != 200 or \
            req_it.status_code != 200:
        return None

    # Get the corresponding tables for every language
    soup_de = BeautifulSoup(req_de.content.decode("utf-8"), 'html.parser')
    soup_fr = BeautifulSoup(req_fr.content.decode("utf-8"), 'html.parser')
    soup_it = BeautifulSoup(req_it.content.decode("utf-8"), 'html.parser')

    table_de = soup_de.find("table", {"class": "table table-bordered text-left table-striped"})
    table_it = soup_fr.find("table", {"class": "table table-bordered text-left table-striped"})
    table_fr = soup_it.find("table", {"class": "table table-bordered text-left table-striped"})

    out = {}

    # Iterate over rows in all languages at the same time.
    for row_de, row_fr, row_it in zip(table_de.find_all("tr")[1:-4],
                                      table_fr.find_all("tr")[1:-4],
                                      table_it.find_all("tr")[1:-4]):

        # Extract the ballot title for every language
        ballot_title_de = row_de.find_all("td")[1].find("a").text
        ballot_title_fr = row_fr.find_all("td")[1].find("a").text
        ballot_title_it = row_it.find_all("td")[1].find("a").text

        # The ballot id and number are both contained in the link which would open the details about this ballot
        col = row_de.find_all("td")[1]
        link = col.find("a")
        href = link["href"]

        # Extract ballot number and id
        ballot_id = href[:8]
        ballot_nr = href[12:].split(".")[0]

        # Ad the data to the return dictionary
        out[ballot_nr] = (ballot_id, (ballot_title_de, ballot_title_fr, ballot_title_it))
    return out


def get_overview(id, nr):
    """Gets a national overview of the ballot overview section.

    Parameters
    ----------
    id : str
        The ballot id (date)
        A ballot from the 22nd of May, 2019, would have the id 22052019
        This ID is not unique for all ballots.
    nr : str
        The ballot number
        This is unique for every ballot

    Returns
    -------
    dict
        A dictionary containing an overview for this ballot.
        Example output (ballot nr. 2):
        {
           "valid": "315578",
           "yes": "159182",
           "no": "156396",
           "yes council": "9 1/2",
           "no council": "12 1/2"
        }
    """

    # The url where we can get the data
    url = "https://www.bk.admin.ch/ch/d/pore/va/{}/det{}.html".format(id, nr)

    req = requests.get(url)

    # If there was an error, skip this
    if req.status_code != 200:
        return None

    # Get the result table of the webpage
    soup = BeautifulSoup(req.content.decode("utf-8"), 'html.parser')
    table = soup.find("table", {"class": "table table-naked text-right"})
    rows = table.find_all("tr")

    # In order to keep it simple, we simplify the names given in the table to shorter, english names
    translations = {"Total Stimmberechtigte": "total",
                    "davon Auslandschweizer": "foreign",
                    "Eingelangte Stimmzettel": "submitted",
                    "Leere Stimmzettel": "empty",
                    "Stimmbeteiligung": "participation",
                    "Ungültige Stimmzettel": "invalid",
                    "Gültige Stimmzettel": "valid",
                    "Ja-Stimmen": "yes",
                    "Nein-Stimmen": "no",
                    "Annehmende Stände": "yes council",
                    "Verwerfende Stände": "no council"}

    # Go though table and add column contents to our return dictionary.
    out = {}
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            key = translations[cols[0].text]
            value = cols[1].text.replace("'", "")
            out[key] = value
    return out


def get_cantonal(id, nr):
    """Gets the cantonal results of a ballot.

    Parameters
    ----------
    id : str
        The ballot id (date)
        A ballot from the 22nd of May, 2019, would have the id 22052019
        This ID is not unique for all ballots.
    nr : str
        The ballot number
        This is unique for every ballot

    Returns
    -------
    list
        A list containing dictionaries with cantonal result.
        One list item might look like this (ballot nr. 311):
        {
            "canton": "Zürich",
            "total voters": "711637",
            "participation": "272112",
            "yes": "156703",
            "no": "104769"
        }
    """

    # The url where we can get the data
    url = "https://www.bk.admin.ch/ch/d/pore/va/{}/can{}.html".format(id, nr)

    req = requests.get(url)

    # If there was an error, skip this
    if req.status_code != 200:
        return None

    # Get the result table of the webpage
    soup = BeautifulSoup(req.content.decode("utf-8"), 'html.parser')
    table = soup.find("table", {"class": "table table-bordered text-center table-striped"})

    # The content names with their according colum index
    contents = {"canton": 0,
                "total voters": 1,
                "participation": 2,
                "yes": 4,
                "no": 5}

    out = []
    # Go through every row, there is one canton per row
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")

        out.append({})
        # create the dictionary for one canton
        for name, index in contents.items():
            out[-1][name] = cols[index].text.replace("'", "")

    return out


@verbwrap
def get_metadata(json_path, verbose=False):
    """Gets all of the metadata (voting results) and saves them in JSON
    format into the given file path.

    Parameters
    ----------
    json_path : str
        The path to the output JSON file.
    verbose : bool
        Whether the program should display its progress to the user or not.

    Returns
    -------
    None
    """

    # Check if the output file already exists. If it does, we might not have to scrape everything
    if os.path.exists(json_path):
        with open(json_path) as f:
            out = json.loads(f.read())
    else:
        out = {}

    # Fetch all id/nr pairs and titles
    id_nr_pairs = get_id_nr_pairs()

    # Iterate over all ballot numbers, ids and its title in all languages
    for ballot_nr, (ballot_id, (ballot_title_de, ballot_title_fr, ballot_title_it)) in id_nr_pairs.items():
        try:
            # Check if we already have this entry.
            if ballot_nr not in out:
                # Get all information about that ballot and store it into our output dictionary.
                out[ballot_nr] = {"id": ballot_id,
                                  "title_de": ballot_title_de,
                                  "title_fr": ballot_title_fr,
                                  "title_it": ballot_title_it,
                                  "overview": get_overview(ballot_id, ballot_nr),
                                  "cantonal": get_cantonal(ballot_id, ballot_nr)
                                  }
                if verbose:
                    print("  gotten metadata for {} {}".format(ballot_id, ballot_nr))

        except UnicodeDecodeError:
            pass

    # Write the dictionary to our output file as JSON. ensure_ascii has to be false
    # In order to allow for umlaut and other special characters.
    with open(json_path, "w+") as f:
        f.write(json.dumps(out, indent=" ", ensure_ascii=False))
