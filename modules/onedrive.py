import streamlit as st
import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def is_configured() -> bool:
    try:
        return bool(
            st.secrets.get("onedrive_client_id")
            and st.secrets.get("onedrive_tenant_id")
            and st.secrets.get("onedrive_refresh_token")
            and st.secrets.get("onedrive_folder")
        )
    except FileNotFoundError:
        return False


@st.cache_data(ttl=3000)
def _get_token() -> str:
    tenant_id = st.secrets["onedrive_tenant_id"]
    resp = requests.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        data={
            "client_id": st.secrets["onedrive_client_id"],
            "refresh_token": st.secrets["onedrive_refresh_token"],
            "grant_type": "refresh_token",
            "scope": "Files.ReadWrite offline_access",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _h() -> dict:
    return {"Authorization": f"Bearer {_get_token()}"}


def _folder() -> str:
    return st.secrets["onedrive_folder"].strip("/")


@st.cache_data(ttl=300)
def list_csv_files() -> list:
    url = f"{GRAPH_BASE}/me/drive/root:/{_folder()}:/children"
    resp = requests.get(url, headers=_h(), timeout=15)
    resp.raise_for_status()
    return sorted(
        item["name"]
        for item in resp.json().get("value", [])
        if item["name"].lower().endswith(".csv")
    )


def upload_csv(name: str, content: bytes) -> None:
    url = f"{GRAPH_BASE}/me/drive/root:/{_folder()}/{name}:/content"
    requests.put(
        url,
        headers={**_h(), "Content-Type": "text/csv"},
        data=content,
        timeout=60,
    ).raise_for_status()
    list_csv_files.clear()
    download_csv.clear()


@st.cache_data(ttl=300)
def download_csv(name: str) -> bytes:
    url = f"{GRAPH_BASE}/me/drive/root:/{_folder()}/{name}:/content"
    resp = requests.get(url, headers=_h(), timeout=30)
    resp.raise_for_status()
    return resp.content


def delete_csv(name: str) -> None:
    url = f"{GRAPH_BASE}/me/drive/root:/{_folder()}/{name}:"
    requests.delete(url, headers=_h(), timeout=15).raise_for_status()
    list_csv_files.clear()
    download_csv.clear()
