"""
One-time script to authenticate with OneDrive and get a refresh token.

Before running:
  1. Go to https://portal.azure.com → Azure Active Directory → App registrations → New registration
  2. Name: anything (e.g. "Breakage Tool")
  3. Supported account types: "Personal Microsoft accounts only"
  4. No redirect URI needed — click Register
  5. Go to API permissions → Add a permission → Microsoft Graph → Delegated → Files.ReadWrite → Add
  6. Go to Authentication → Add a platform → Mobile and desktop applications
     Check: https://login.microsoftonline.com/common/oauth2/nativeclient
  7. Copy the Application (client) ID from the Overview page

Run:
  python3 scripts/onedrive_auth.py

Then add the printed values to your Streamlit secrets (.streamlit/secrets.toml).
"""

import sys
import time
import requests

CLIENT_ID = input("Paste your Azure app client_id: ").strip()
if not CLIENT_ID:
    sys.exit("No client_id provided.")

SCOPE = "Files.ReadWrite offline_access"

# Step 1: request device code
resp = requests.post(
    "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode",
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
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": flow["device_code"],
        },
        timeout=15,
    )
    result = token_resp.json()

    if "access_token" in result:
        print("\nAuthenticated! Add the following to .streamlit/secrets.toml:\n")
        print(f'onedrive_client_id   = "{CLIENT_ID}"')
        print(f'onedrive_refresh_token = "{result["refresh_token"]}"')
        print(f'onedrive_folder      = "breakage-tool"  # folder name in your OneDrive root')
        print("\nThen create a folder called 'breakage-tool' in your OneDrive root.")
        break
    elif result.get("error") == "authorization_pending":
        print("Waiting for sign-in...")
    elif result.get("error") == "slow_down":
        interval += 5
    else:
        print(f"Error: {result.get('error_description', result)}")
        sys.exit(1)
