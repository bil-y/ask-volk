#!/usr/bin/python3
#
# Downloads all necessary data
#
# Author: Pascal Schärli
#

from utils.scraping import download_leaflets, get_metadata
from utils.pre_processing import convert_to_text, extract_content, data_merger, add_title_groups


def main():
    leaflet_pdf_folder = "data/leaflets_pdf"
    leaflet_txt_folder = "data/leaflets_txt"
    leaflet_json_file = "data/json/leaflet_contents.json"
    metadata_json_file = "data/json/metadata.json"
    merged_json_file = "data/data.json"

    # Download all leaflets
    download_leaflets(leaflet_pdf_folder, verbose=True)

    # Convert all leaflets
    convert_to_text(leaflet_pdf_folder, leaflet_txt_folder, verbose=True)

    # Extract ballot specific contents from leaflet files
    extract_content(leaflet_txt_folder, leaflet_json_file, verbose=True)

    # Download metadata for ballots
    get_metadata(metadata_json_file, verbose=True)

    # Merge metadata and leaflet contents to one file
    data_merger(leaflet_json_file, metadata_json_file, merged_json_file, verbose=True)

    # Get some longer groups in order to reduce sparsity of data
    title_groups = [
        ["subject", "short_summary", "detail", "council", "initiative", "referendum", "parlament", "legal"],
        ["subject", "short_summary", "detail"],
        ["council", "parlament"],
        ["initiative", "referendum"],
    ]
    add_title_groups(merged_json_file, title_groups, verbose=True)


if __name__ == "__main__":
    main()
