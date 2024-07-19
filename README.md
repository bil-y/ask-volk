# Ask Volk Today

Have you ever wondered what the people would (maybe, probably, ...) say
about your crazy referendum idea? Use Ask Volk Today to find out!

## Installation and Setup

To install this package, simply run `pip install -e .`.

This will install two executable scripts, `ask-volk-downloader` and `ask-volk-trainer`.

- `ask-volk-downloader` is a utility to download and preprocess statistics from the Swiss Federal Statistical Office.
- `ask-volk-trainer` is used to train the XGB regressor.

The two utilities can be configured using the YAML files in `ask_volk/conf`. These files control
the sources, preprocessing, and training. The individual files are heavily commented, in case you wish
to understand how they work. In any case, they are currently configured to reproduce the results documented in the paper.

## Reproducing results

- Leaflets of votes starting from 1977 can be downloaded from `https://www.bk.admin.ch/bk/de/home/dokumentation/abstimmungsbuechlein.html`
- Parsing of leaflets has been done combining manual work and using the script `ask_volk/src/robot_judge_project/code/download_data.py`. The resulting file is `ask_volk/data/raw/leaflets/leaflets_merged.csv`, which can be used to reproduce results.
- To reproduce the dataset, run `ask-volk-downloader`. Note that this will take a long time and consume considerable amounts of memory.
- To reproduce the topics dataset, run `ask_volk/src/topic_modeling/topic_modeling.py`. This will produce the data in `ask_volk/data/topics/summary_topics.csv`
- To reproduce the results for **Section 5.1**, run `topic_analysis`
- To reproduce the results for **Section 5.2**, run `ask-volk-trainer`. You can change the cutoff in `ask_volk/cfg/model/default.yaml`. To change the hyperparameters, edit `ask_volk/trainer.py`.
Training without controls requires manual modification of the script (i.e., just don't combine the topics and votes with the controls) as these results were produced before controls were added.
- To reproduce the results for **Section 5.3**, run `ask_volk/notebooks/unknown_municipalities_varying_test_size.ipynb` and `ask_volk/notebooks/unknown_municipalities_varying_preprocessing.ipynb`
