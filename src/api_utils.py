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
    }
    return load_json_from_file(mpaths[metadata_type])
    