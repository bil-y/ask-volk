"""
downloads legal text of all votations from swissvotes.ch and parses and cleans them
author: carlo schmid
"""

import pandas as pd
import requests
import os
import subprocess

# paths
swiss_votes_path = "../../data/swissvotes/DATASET_CSV_09-06-2024.csv"
legal_texts_path = "../../data/legal_texts"

def list_votations(path: str)->list:
    """
    returns list of all votation ids in the swissvotes dataset
    """
    df = pd.read_csv(path,delimiter=';')
    df = df[df['anr'] >= 305] # starting only from 1981
    return df['anr'].to_list()

def download_pdf(votations:list)->None:
    """
    downloads pdf legal texts from swissvotes
    """
    for votation in votations:
        download_path = f'https://swissvotes.ch/vote/{votation}/abstimmungstext-de.pdf'
        save_path = f'{legal_texts_path}/raw/{votation}_abstimmungstext-de.pdf'
        if not os.path.exists(save_path):
            # Download PDF to specified location
            response = requests.get(download_path)
            with open(save_path, "wb+") as f:
                f.write(response.content)

def parse_pdfs(votations: list, source_path: str, target_path: str)->None:
    """
    coverts pdf legal texts to txt
    """
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    for votation in votations:
        in_path = f'{source_path}/{votation}_abstimmungstext-de.pdf'
        out_path = f'{target_path}/{votation}_abstimmungstext-de.txt'
        if not os.path.exists(in_path):
            raise ValueError(f'pdf for votation {votation} does not exist yet')
        if not os.path.exists(out_path):
            # Calls the converter and saves the output file in the output folder
            subprocess.call(["pdftotext", "-enc", "UTF-8", in_path, out_path])
    return None

if __name__ == "__main__":
    votations = list_votations(swiss_votes_path)
    download_pdf(votations)
    parse_pdfs(votations, f'{legal_texts_path}/raw', f'{legal_texts_path}/parsed')


