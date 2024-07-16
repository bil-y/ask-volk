#!/usr/bin/python3
#
# visualization of our data
#
# Author: Pascal Schärli
#

import os
from matplotlib import pyplot as plt
from utils.utils import verbwrap
from utils.machine_learning import get_language_results
from scipy import stats
import numpy as np


@verbwrap
def plot_attributes(attributes, plot_dir, verbose=False):
    """Plots attributes agianst all chapter and language pairs

    Parameters
    ----------
    attributes : dict
        The attributes we want to plot

    plot_dir : str
        The directory in which we want to save our plots.

    verbose : bool
        Whether the program should display its progress to the user or not.

    """

    # Create plot directory
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    for title in attributes.keys():
        X = {}
        Y = {}
        # Get all X and Y values for the current title (chapter)
        for language in attributes[title].keys():
            x = {}
            y = {}
            for ballot_nr in attributes[title][language].keys():
                for attribute in attributes[title][language][ballot_nr]["attributes"].keys():
                    if attribute not in x:
                        x[attribute] = []
                    x[attribute].append(attributes[title][language][ballot_nr]["attributes"][attribute])
                for data_type in attributes[title][language][ballot_nr]["results"].keys():
                    if data_type not in y:
                        y[data_type] = []
                    y[data_type].append(attributes[title][language][ballot_nr]["results"][data_type])

            X[language] = x
            Y[language] = y

        # Plot all attributes against the current title
        for attribute in X[language].keys():
            for data_type in attributes[title][language][ballot_nr]["results"].keys():

                # Set axis limits depending on the attribute
                if attribute == "polarity":
                    xlim = np.array([-1, 1])
                elif attribute == "subjectivity":
                    xlim = np.array([0, 1])
                elif attribute == "sentence_length":
                    xlim = np.array([0, 30])

                # get a list of all x an y values combined in order to draw the regression
                total_x = []
                total_y = []
                colors = {"de": "blue", "fr": "orange", "it": "green"}

                legend = []
                languages = {"de": "German", "fr": "French", "it": "Italian"}

                for language in attributes[title].keys():
                    x = X[language][attribute]
                    y = Y[language][data_type]
                    # all languages are being plotted onto the same plot
                    plt.scatter(x, y, color=colors[language])
                    total_x += x
                    total_y += y

                    # Linear regression on the combined points
                    gradient, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    plt.xlim(xlim)
                    y_linreg = gradient * xlim + intercept
                    plt.plot(xlim, y_linreg, '-', color=colors[language])

                    legend.append("{}: B0={:.2f} B1={:.2f}, S={:.2f}e-2".format(
                        languages[language], intercept, gradient, std_err * 100))

                # Generate a nicely readable chapter namename from the combined chapters
                chapters = title.split("+")
                if len(chapters) == 8:
                    chapter = "All chapters combined"
                else:
                    out = []
                    for chapter in chapters:
                        chapter = chapter.replace("_", " ")
                        out.append(chapter.title())
                    chapter = ", ".join(out)

                # Save plot to the given folder
                plt.ylim([0, 1])
                plt.title(chapter)
                plt.ylabel(data_type.title())
                plt.xlabel(attribute.replace("_", " ").title())
                file_path = os.path.join(plot_dir, "{}_{}_{}.png".format(attribute, title, data_type))

                plt.legend(legend, loc='upper right')

                plt.savefig(file_path)
                plt.clf()
                if verbose:
                    print("  saved plot to " + file_path)


@verbwrap
def plot_part_yes_no(metadata, plot_dir, verbose=False):

    # Create plot directory
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    data = {"participation": {"de": [], "it": [], "fr": []},
            "yes": {"de": [], "it": [], "fr": []},
            "no": {"de": [], "it": [], "fr": []}}
    dates = []

    for ballot_nr, ballot in metadata.items():
        if ballot["cantonal"] is not None:
            try:
                for language in ["de", "it", "fr"]:
                    results = get_language_results(ballot, language)
                    for data_type, result in results.items():
                        data[data_type][language].append(result)
                date = ballot["id"]
                year = int(date[0:4])
                month = int(date[4:6])
                day = int(date[6:8])
                date_exact = year + month / 12 + day / 30
                dates.append(date_exact)
            except:
                pass

    for data_type, language_data in data.items():
        for language, y_data in language_data.items():
            plt.scatter(dates, y_data, marker='.')
        plt.title(data_type)
        plt.legend(language_data.keys())
        file_path = os.path.join(plot_dir, "{}.png".format(data_type))
        plt.savefig(file_path)
        plt.clf()
        if verbose:
            print("  saved plot to {}".format(file_path))


@verbwrap
def plot_part_yes_no_bar(metadata, plot_dir, bucket_size=20, verbose=False):

    # Create plot directory
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    data = {"participation": {"de": [], "it": [], "fr": []},
            "yes": {"de": [], "it": [], "fr": []},
            "no": {"de": [], "it": [], "fr": []}}

    buckets = []

    for ballot_nr, ballot in metadata.items():
        if ballot["cantonal"] is not None:
            try:
                date = ballot["id"]
                year = int(date[0:4])
                if year > 1900:
                    new_bucket = False
                    bucket = (year - 2000) // bucket_size
                    if bucket not in buckets:
                        buckets.append(bucket)
                        new_bucket = True

                for language in ["de", "it", "fr"]:
                    results = get_language_results(ballot, language)
                    for data_type, result in results.items():
                        if new_bucket:
                            data[data_type][language].append([])
                        data[data_type][language][-1].append(result * 100)
            except Exception:
                pass

    buckets = ["{}-{}".format(bucket * bucket_size + 2000, bucket * bucket_size + bucket_size + 2000) for bucket in buckets]

    for data_type, language_data in data.items():
        x = np.arange(len(buckets))
        width = 0.25
        fig, ax = plt.subplots(figsize=(10, 5))

        rects = []
        for i, (language, y_data) in enumerate(language_data.items()):
            means = [np.mean(y) for y in y_data]
            rects.append(ax.bar(x + (i - 1) * width, means, width, label=language))

        ax.set_xticks(x)
        ax.set_xticklabels(buckets)

        plt.ylabel(data_type + " [%]")
        plt.legend(language_data.keys())
        file_path = os.path.join(plot_dir, "{}_bar.png".format(data_type))
        plt.savefig(file_path)
        plt.clf()
        if verbose:
            print("  saved plot to {}".format(file_path))
