#!/usr/bin/env python3
from pathlib import Path
import requests
import os
from urllib.error import HTTPError
import urllib.parse

from utils import (
    write_json_to_file,
    load_json_from_file,
)

from config import Config

provider_friendly_names = ["eur", "lei", "vu", "aumc"]
temp_provider_mapping = {
    "erasmus-yoda": "eur",
    "test-yoda": "aumc"
}
temp_provider_friendly_names = list(temp_provider_mapping.keys())
KNOWN_ENDPOINTS = [
    "projects",
    "providers",
    "users",
    "users/me",
    "relationship",
    "data_users",
    "data",
    "metadata",
    "session"
]
repo_path = Path(__file__).resolve().parent.parent
BASE_URL = Config.NEPTUNE_BASE_URL
CERT_PATH = repo_path / Config.NEPTUNE_CERT_PATH
USERNAME = Config.NEPTUNE_USERNAME
PASSWORD = Config.NEPTUNE_PASSWORD
SRAM_USER_ENDPOINT = Config.SRAM_USER_ENDPOINT

def check_env():
    if not USERNAME or not PASSWORD:
        raise ValueError(f"Neptune authorization credentials not set. Please set 'EXPLORER_USER' and 'EXPLORER_PASSWD' before making a request to a Neptune endpoint")


def get_metadata(endpoint, params = {}):
    if endpoint not in KNOWN_ENDPOINTS:
        raise ValueError(f"Argument '{endpoint}' is not one of the allowed endpoint options")
    
    check_env()
    
    if endpoint == "data_users":
        my_user = get_metadata("users/me")
        params["provider_id"] = my_user["provider_id"]

    # Get the desired metadata
    r = requests.get(
        f"{BASE_URL}/{endpoint}/",
        auth=(USERNAME, PASSWORD),
        headers={'accept': 'application/json'},
        params=params,
        verify=str(CERT_PATH),
    )
    # Break if request failed
    if r.status_code != 200:
        raise ValueError(f"Unsuccessful request: response code {r.status_code}")
    # Response to JSON
    return r.json()


def check_user(email):
    user_endpoint = f"{BASE_URL}/{SRAM_USER_ENDPOINT}/{urllib.parse.quote_plus(email)}"
    # Get the desired metadata
    r = requests.get(
        user_endpoint,
        auth=(USERNAME, PASSWORD),
        headers={'accept': 'application/json'},
        params={},
        verify=str(CERT_PATH),
    )
    # Break if request failed
    if r.status_code != 200:
        raise ValueError(f"Unsuccessful request: response code {r.status_code}")
    return r.json()


def invite_user(email):
    user_endpoint = f"{BASE_URL}/{SRAM_USER_ENDPOINT}/{urllib.parse.quote_plus(email)}"
    # Get the desired metadata
    r = requests.post(
        user_endpoint,
        auth=(USERNAME, PASSWORD),
        headers={'accept': 'application/json'},
        params={},
        verify=str(CERT_PATH),
    )
    # Break if request failed
    if r.status_code != 200:
        raise ValueError(f"Unsuccessful request: response code {r.status_code}")
    return r.json()


def delete_user(email):
    user_endpoint = f"{BASE_URL}/{SRAM_USER_ENDPOINT}/{urllib.parse.quote_plus(email)}"
    r = requests.delete(
        user_endpoint,
        auth=(USERNAME, PASSWORD),
        headers={'accept': 'application/json'},
        params={},
        verify=str(CERT_PATH),
    )
    # Break if request failed
    if r.status_code != 200:
        raise ValueError(f"Unsuccessful request: response code {r.status_code}")
    return r.json()

def create_new_session(incoming_data):
    """"""
    # Inputs from frontend
    # - data provider friendly name
    # - list of file paths
    # - authenticated user data
    # - submitted form data
    provider_friendly = incoming_data["provider_friendly"]
    file_paths = incoming_data["file_paths"]
    user_data = incoming_data["user_data"]
    form_data = incoming_data["form_data"]

    # First get providers, data-users, and projects:
    providers = load_json_from_file(repo_path / "data" / "_providers.json")
    data_users = load_json_from_file(repo_path / "data" / "_data_users.json")
    projects = load_json_from_file(repo_path / "data" / "_projects.json")
    # Isolate GUTS-Metadata project
    found_project = next((p for p in projects if p["name"] == "GUTS-Metadata"), None)
    if not found_project:
        raise ValueError("GUTS-Metadata project not found among projects")
    # Isolate SRAM provider
    sram_provider = next((p for p in providers if p["friendly_name"] == "sram"), None)
    if not sram_provider:
        raise ValueError(f"SRAM provider not found in list of providers")
    sram_endpoint = next((e for e in sram_provider["endpoints"]), None)
    if not sram_endpoint:
        raise ValueError(f"SRAM provider does not have any endpoints specified")

    # Now determine participants:
    # - the service account of the data provider (where the requested files are hosted)
    # - the reviewer
    participants = []
    # 1: Data provider service account ID
    #    - friendly name -> provider id -> project["service_accounts"] (swap key/value)
    inverse_mapping_friendly = {v: k for k, v in temp_provider_mapping.items()}
    data_provider = next((p for p in providers if p["friendly_name"] == inverse_mapping_friendly[provider_friendly]), None)
    if not data_provider:
        raise ValueError(f"No provider found with friendly name: {provider_friendly}")
    data_endpoint = next((e for e in data_provider["endpoints"]), None)
    if not data_endpoint:
        raise ValueError(f"Data provider does not have any endpoints specified")
    inverse_service_accounts = {v: k for k, v in found_project["service_accounts"].items()}
    service_account_id = inverse_service_accounts[data_provider["_id"]]
    participants.append(service_account_id)
    # 2: Reviewer ID
    #   - for each member in project["members"],
    #     include if user["_id"] (in data_users) is member["_id"],
    #     and user["role"] is "reviewer"
    for member in found_project["members"]:
        found_reviewers = [user for user in data_users
                           if user["_id"] == member
                           and user["role"] == "reviewer"]
        for r in found_reviewers:
            participants.append(r["_id"])
    # Now determine profiles and profile tags:
    # - profile of SRAM user
    # - profile of data provider
    sram_username = user_data.get("sub", user_data.get("name", "noName").replace(" ", "_"))
    sram_tag = f"{sram_endpoint['hostname']}:{sram_endpoint['port']}::{sram_username}::native"
    data_tag = f"{data_endpoint['hostname']}:{data_endpoint['port']}::noaccess::native"
    profiles = [
        # profile of SRAM user
        dict(
            auth_scheme="native",
            endpoint=sram_endpoint,
            metadata={
                "user": form_data,
            },
            secret_type="password",
            tag=sram_tag,
            username=sram_username
        ),
        # profile of data provider
        dict(
            auth_scheme="native",
            endpoint=data_endpoint,
            metadata={
                "user": {},
            },
            secret_type="password",
            tag=data_tag,
        )
    ]
    profile_tags = dict(
        path=data_tag,
        user=sram_tag,
    ) 

    # To create a data request, we have to create a session, with an event per file path
    new_session = dict(
        access="shared",
        events=[],
        lifetime=604800, # in seconds, current default = 1 week
        participants=participants,
        profiles=profiles,
        provenance=[],
    )

    for f in file_paths:
        new_event = dict(
            metadata=[],
            operation="request",
            path=f,
            profile_tags=profile_tags,
        )
        new_session["events"].append(new_event)

    return new_session

def create_neptune_data_request(incoming_data):
    """Forward incoming data to the neptune API, session endpoint"""
    new_session_dict = create_new_session(incoming_data)
    r = requests.post(
        f"{BASE_URL}/session",
        auth=(USERNAME, PASSWORD),
        headers={'Content-Type': 'application/json'},
        verify=str(CERT_PATH),
        json=new_session_dict,
    )
    # Break if request failed
    if r.status_code != 200:
        raise ValueError(f"Unsuccessful request: response code {r.status_code}")
    return r