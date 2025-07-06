#!/usr/bin/env python3
from pathlib import Path
from neptune_utils import (
    KNOWN_ENDPOINTS,
    get_metadata,
    check_user,
    invite_user,
)

if __name__ == '__main__':
    try:
        r = get_metadata("data_users")
        # r = check_user("jsheunis@gmail.com")
        print(r)

        print("\n\n\n\n")

        r = get_metadata("projects")
        # r = check_user("jsheunis@gmail.com")
        print(r)

        print("\n\n\n\n")

        r = get_metadata("providers")
        # r = check_user("jsheunis@gmail.com")
        print(r)


    except Exception as e:
        print(e)