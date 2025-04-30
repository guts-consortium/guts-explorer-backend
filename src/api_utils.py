import requests
import os
from pathlib import Path
from utils import load_json_from_file

repo_path = Path(__file__).resolve().parent.parent

def load_metadata(metadata_type):
    mpaths = {
        'files': repo_path / "data" / "guts-file-level-metadata.json",
        'measures': repo_path / "data" / "guts-measure-overview.json",
        'subjects': repo_path / "data" / "guts-subject-level-metadata.json",
        'cohorts': repo_path / "data" / "guts-cohorts.json",
        'data_categories': repo_path / "data" / "guts-data-categories.json",
        'data_types': repo_path / "data" / "guts-data-types.json",
        'demographics': repo_path / "data" / "guts-demographics.json",
    }
    return load_json_from_file(mpaths[metadata_type])
    