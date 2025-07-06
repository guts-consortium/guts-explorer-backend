# --------------------------------------------------------------------------------
# Fetch metadata from Neptune and process it for use in the GUTS metadata explorer
# --------------------------------------------------------------------------------
# 
# ASSUMPTIONS
# -----------
# Providers create a new session whenever new metadata is provided,
# i.e. existing sessions are not updated/patched.

# CONFIG
# ------
# - A list of known provider friendly names (a.k.a. cohorts): ["eur", "lei", "vu", "aumc"]
# - A list of known metadata types:
#   ["guts-file-level-metadata", "guts-subject-level-metadata"]
# - A list of session ids for which metadata has already been processed
# - A list of session ids for which metadata has already been processed,
#   assoctaied with a source site

# STEPS
# -----
# 1: Get providers
# ----------------
# - Make an HTTP GET request to the "providers" endpoint, retrieving the list.
# - Isolate providers with known friendly names: providers[i]["friendly_name"]
# - Get their endpoints, for matching with associated metadata profile later:
#   providers[i]["endpoints"][j]["hostname"]
# - Save list if different from previous

# 2: Get and filter sessions
# --------------------------
# - Make an HTTP GET request to the “session” endpoint, retrieving the list.
# - Filter down the list of sessions to those that can be used:
#   - New id: sessions[i]["_id"] not in list of previously processed ids
#   - Active status: sessions[i]["status"] == "active"
#   - Must have events: len(sessions[i]["events"]) > 0
#   - Event operation must be type share: sessions[i]["events"][j]["operation"] == "share"
#   - Must have metadata: len(sessions[i]["events"][j]["metadata"]) > 0
#   - Metadata item must be of known types:
#     sessions[i]["events"][j]["metadata"][k][0] == "json"
#     sessions[i]["events"][j]["metadata"][k][1] in ["guts-file-level-metadata", "guts-subject-level-metadata"]

# 3: Merge and save metadata
# --------------------------
# - Write new session ids and friendly names and time stamps to list:
#   - id and time stamp directly from session
#   - Get associated profile tag: tag = sessions[i]["events"][j]["profile_tags"]["path"]
#   - Find associated profile: k where sessions[i]["events"][j]["profiles"][k]["tag"] == tag
#   - Get associated hostname: hostname = sessions[i]["events"][j]["profiles"][k]["endpoint"]["hostname"]
#   - Get associated friendly name from known list: providers["hostname"] == hostname
# - Merge all subject-level and file-level metadata from different site sessions into common
#   data objects that are written to the explorer’s files “guts-file-level-metadata.json”
#   and “guts-subject-level-metadata.json”:

from pathlib import Path
import sys
from datetime import datetime, timezone

from utils import (
    load_json_from_file,
    write_json_to_file,
)

from neptune_utils import get_metadata



# ---------
# CONSTANTS
# ---------
repo_path = Path(__file__).resolve().parent.parent
_sesspath = repo_path / "data" / "_sessions.json"
_friendly_providerpath = repo_path / "data" / "_providers_friendly.json"
_providerpath = repo_path / "data" / "_providers.json"
_projectpath = repo_path / "data" / "_projects.json"
_datauserpath = repo_path / "data" / "_data_users.json"
file_metadata_path = repo_path / "data" / "guts-file-level-metadata.json"
subject_metadata_path = repo_path / "data" / "guts-subject-level-metadata.json"
overview_metadata_path = repo_path / "data" / "guts-measure-overview.json"
known_meta_types = [
    "file-level-metadata",
    "subject-level-metadata",
    "measure-overview",
]

ignore_ids = []

provider_friendly_names = ["eur", "lei", "vu", "aumc"]
temp_provider_mapping = {
    "erasmus-yoda": "eur",
    "test-yoda": "aumc",
    "leiden-yoda": "lei"
}
temp_provider_friendly_names = list(temp_provider_mapping.keys())



# ---------
# FUNCTIONS
# ---------

def add_latest_to_sessions(previous_sessions, latest_session):
    previous_sessions.append(
        {
            "_id": latest_session["_id"],
            "create_ts": latest_session["create_ts"],
            "updated": datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        }
    )
    write_json_to_file(previous_sessions, _sesspath)



# ------
# SCRIPT
# ------

# Get own user info
print("Getting own user info...")
user_me = get_metadata("users/me")
# print(f"\tMy provider-id: {user_me['provider_id']}")

# Get data users
print("Getting data users...")
data_users = get_metadata("data_users")
# print(f"\tData users: {data_users}")

# Get projects
print("Getting projects...")
projects = get_metadata("projects")
# print(f"\tProjects: {projects}")


# (1) Get providers
# -----------------
# Make an HTTP GET request to the "providers" endpoint, retrieving the list.
print("Getting providers from Neptune endpoint...")
try:
    providers = get_metadata("providers")
except Exception as e:
    print(e)

# Isolate providers with known friendly names: providers[i]["friendly_name"]
# - assuming these all have a single endpoint [!]
# - direct mapping to endpoints
print("Providers:")
print(providers)
friendly_providers = [
    {
        "_id": p["_id"],
        "friendly_name": temp_provider_mapping[p["friendly_name"]],
        "hostname": p["endpoints"][0]["hostname"].strip()
    }
    for p in providers if p["friendly_name"] in temp_provider_friendly_names
]
print("Friendly providers:")
print(f"\t{friendly_providers}")
     

# (2) Get and filter sessions
# ---------------------------
print("Getting sessions from Neptune endpoint...")
# Make an HTTP GET request to the "sessions" endpoint, retrieving the list.
sessions = get_metadata("session")
# Retrieve list of previously used sessions and their ids
try:
    existing_sessions = load_json_from_file(_sesspath)        
except:
    existing_sessions = []

existing_session_ids = [s["_id"] for s in existing_sessions]
# Isolate new and valid sessions
new_sessions = [
    s for s in sessions if
    # New id, i.e. not in list of previously processed ids
    s["_id"] not in existing_session_ids and
    # TEMPORARY: Not in list of ids to ignore
    s["_id"] not in ignore_ids and
    # Active status
    s["status"] == "active" and
    # has at least 1 event, which contains metadata
    len(s["events"]) > 0
]
# Exit process if no new sessions available
if len(new_sessions) == 0:
    sys.exit(f"No new active sessions found, exiting process.")

# print(f"\t{new_sessions}")



# (3) Merge and save metadata
# ---------------------------
available_providers = []
file_metadata = []
subject_metadata = []
overview_metadata = []
file_metadata_added = False
subject_metadata_added = False
overview_metadata_added = False
# Sessions > events > metadata
for s in new_sessions:
    metadata_added = False
    new_ses = {
        "_id": None,
        "create_ts": None,
        "provider": None,
        "metadata_shared": []
    }
    for e in s["events"]:
        # Event operation must be type share
        if e["operation"] != "share":
            continue
        # Metadata must be an array with more than 0 elements
        if e.get("metadata", None) is not None and len(e["metadata"]) == 0:
            continue
        # Process metadata
        for m in e["metadata"]:
            # To write the new session ids and friendly names and time stamps to "previously processed"
            # list, and also to map files to providers, we first need several details

            # - Get id and time stamp directly from session
            new_ses["_id"] = s["_id"]
            new_ses["create_ts"] = s["create_ts"]
            # - Get associated profile tag: tag = sessions[i]["events"][j]["profile_tags"]["path"]
            profile_tag = e["profile_tags"]["path"]
            # - Find associated profile: k where sessions[i]["events"][j]["profiles"][k]["tag"] == tag
            profiles = [p for p in s["profiles"] if p["tag"] == profile_tag]
            profile = profiles[0]
            # - Get associated hostname: hostname = sessions[i]["events"][j]["profiles"][k]["endpoint"]["hostname"]
            hostname = profile["endpoint"]["hostname"].strip()
            print(hostname)
            # - Get associated friendly name from known list: providers["hostname"] == hostname
            pproviders = [fp for fp in friendly_providers if fp["hostname"] == hostname]
            provider = pproviders[0]
            new_ses["provider"] = provider["friendly_name"]
            if new_ses["provider"] not in available_providers:
                available_providers.append(new_ses["provider"])
            
            # Now process metadata
            # Metadata item must be of known types:
            # - m[0] must be "json"
            # - m[1] must be a string containing one element of ["file-level-metadata", "subject-level-metadata", "measure-overview"]
            # - m[2] must be an array with more than 0 elements
            if m[0] != "json" or not any(t in m[1] for t in known_meta_types) or len(m[2]) == 0:
                continue
            if "file-level-metadata" in m[1]:
                new_file_metadata = [f for f in m[2]]
                for nfm in new_file_metadata:
                    nfm["explorer_provider"] = new_ses["provider"]
                file_metadata += new_file_metadata
                file_metadata_added = True
                if "file-level-metadata" not in new_ses["metadata_shared"]:
                    new_ses["metadata_shared"].append("file-level-metadata")
            if "subject-level-metadata" in m[1]:
                subject_metadata += m[2]
                subject_metadata_added = True
                if "subject-level-metadata" not in new_ses["metadata_shared"]:
                    new_ses["metadata_shared"].append("subject-level-metadata")
            # Only add overview metadata if available AND the provider == "eur"
            if "measure-overview" in m[1] and new_ses["provider"] == "eur":
                overview_metadata = m[2]
                overview_metadata_added = True
                if "measure-overview" not in new_ses["metadata_shared"]:
                    new_ses["metadata_shared"].append("measure-overview")
            metadata_added = file_metadata_added or subject_metadata_added or overview_metadata_added
    # Assuming only a single provider per session
    # - if this is not true, the following will take the last provider in a session as the value, incorrectly
    if metadata_added:
        existing_sessions.append(new_ses)

# (4) Write files
# ---------------
write_json_to_file(friendly_providers, _friendly_providerpath)
write_json_to_file(providers, _providerpath)
write_json_to_file(data_users, _datauserpath)
write_json_to_file(projects, _projectpath)

if file_metadata_added:
    write_json_to_file(file_metadata, file_metadata_path)
if subject_metadata_added:
    write_json_to_file(subject_metadata, subject_metadata_path)
if overview_metadata_added:
    write_json_to_file(overview_metadata, overview_metadata_path)
if file_metadata_added or subject_metadata_added or overview_metadata_added:
    write_json_to_file(existing_sessions, _sesspath)


if not file_metadata_added and not subject_metadata_added and not overview_metadata_added:
    print(f"WARNING: No file-level, subject-level, or overview metadata available from any share-sessions.")
else:
    if len(available_providers) < 2:
        print(f"WARNING: Active session(s) only from {len(available_providers)} provider, i.e. request creation to several providers cannot be tested.")

print("Process of updating metadata completed.")

# # -----
# # Notes
# # -----

# # Sessions:
# # - array of objects

# # Session:
# # - "_id" = unique session id
# # - "status" = status of session, guts-explorer is interested in the "active" sessions: session["status"] == "active"
# # - "events" = array of events associated with the session
# #   - an event has a specific type of "operation", the guts-explorer is interested in the "share" operation,
# #     since they have metadata attached: session["events"]["metadata"]
# # - "profiles": the profiles of users/providers involved in the session, identified by the "tag" field