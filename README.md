# GUTS-Explorer Backend

Backend services for the GUTS-Explorer application


### 0. Load config from environment variables


### 1. Fetch metadata from Neptune and process it for use by `guts-explorer` frontend

This is a Python script that should run every X days/weeks and does
the following:

1. Fetch metadata from `providers`, `data_users`, and `projects` endpoints
2. Fetch and filter `sessions` endpoint
3. Merge all subject-level and file-level metadata from all providers:
   - IMPORTANT: adds provider to file-level metadata, which is needed by browser app during basket checkout
4. Save state data (processed sessions from specific providers)
5. Save provider/user/project data, metadata, and state data to persistent shared storage or POST to Neptune

