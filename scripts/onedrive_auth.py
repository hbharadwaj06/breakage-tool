"""
One-time script to authenticate with OneDrive and get a refresh token.
Run once locally, then add the printed values to your Streamlit secrets.

  python3 scripts/onedrive_auth.py
"""

import sys
import time
import requests

CLIENT_ID = input("Paste your Azure app client_id: ").strip()
TENANT_ID = input("Paste your Azure Directory (tenant) ID: ").strip()

if not CLIENT_ID or not TENANT_ID:
    sys.exit("client_id and tenant_id are both required.")

BASE = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0"
SCOPE = "Files.ReadWrite offline_access"

# Step 1: request device code
resp = requests.post(
    f"{BASE}/devicecode",
    data={"client_id": CLIENT_ID, "scope": SCOPE},
    timeout=15,
)
resp.raise_for_status()
flow = resp.json()

print(f"\n{flow['message']}\n")

# Step 2: poll until user completes sign-in
interval = int(flow.get("interval", 5))
while True:
    time.sleep(interval)
    token_resp = requests.post(
        f"{BASE}/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": flow["device_code"],
        },
        timeout=15,
    )
    result = token_resp.json()

    if "access_token" in result:
        print("\nAuthenticated! Add the following to your Streamlit secrets:\n")
        print(f'onedrive_client_id     = "{CLIENT_ID}"')
        print(f'onedrive_tenant_id     = "{TENANT_ID}"')
        print(f'onedrive_refresh_token = "{result["refresh_token"]}"')
        print(f'onedrive_folder        = "breakage-tool"')
        print("\nAlso create a folder called 'breakage-tool' in your OneDrive root.")
        break
    elif result.get("error") == "authorization_pending":
        print("Waiting for sign-in...")
    elif result.get("error") == "slow_down":
        interval += 5
    else:
        print(f"Error: {result.get('error_description', result)}")
        sys.exit(1)
