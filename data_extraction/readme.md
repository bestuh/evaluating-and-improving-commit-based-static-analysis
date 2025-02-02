# Data Extraction

This directory contains some scripts for creating and processing datasets.

- `get_vccs_from_db.py`: can be used to extract data from the database by [R. Ahmad](https://git.rwth-aachen.de/rawel.ahmad/commit-analysis-ml). To do so, make sure to first setup the datase itself (see `database` folder).
- `extract_size.py`: allows to extract number of added and deleted lines of commits in a dataset. Was used to compute the normalized Gain metric.
- `dataset_creator.py`: allows creation of datasets (train-, validation-, test-splits).
- `dataset_combinator.py`: Used to combine multiple datasets created via the dataset-creator into one dataset.
- `augment_with_non_vccs.py`: samples random commits from projects repositories to add secure commits to a dataset.
- `dataset_summary.py`: allows to get a basic overview of a dataset.
- `extract_function.py`: is used to extract data for the proposed model (see `model` directory).