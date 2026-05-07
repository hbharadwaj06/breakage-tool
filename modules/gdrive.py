import gzip
import streamlit as st
from supabase import create_client


def is_configured() -> bool:
    try:
        return bool(st.secrets.get("supabase_url") and st.secrets.get("supabase_key"))
    except FileNotFoundError:
        return False


@st.cache_resource
def _storage():
    client = create_client(st.secrets["supabase_url"], st.secrets["supabase_key"])
    return client.storage.from_(st.secrets["supabase_bucket"])


@st.cache_data(ttl=300)
def list_csv_files() -> list:
    files = _storage().list() or []
    return sorted(f["name"] for f in files if f["name"].lower().endswith(".csv"))


def upload_csv(name: str, content: bytes) -> None:
    _storage().upload(
        path=name,
        file=gzip.compress(content),
        file_options={"content-type": "application/gzip", "upsert": "true"},
    )
    list_csv_files.clear()
    download_csv.clear()


@st.cache_data(ttl=300)
def download_csv(name: str) -> bytes:
    return gzip.decompress(bytes(_storage().download(name)))


def delete_csv(name: str) -> None:
    _storage().remove([name])
    list_csv_files.clear()
    download_csv.clear()
