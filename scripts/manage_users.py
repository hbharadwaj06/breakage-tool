#!/usr/bin/env python3
"""
Manage breakage app users.

Usage:
  python scripts/manage_users.py list
  python scripts/manage_users.py add <username> <name> <role: admin|viewer>
  python scripts/manage_users.py set-password <username>
  python scripts/manage_users.py remove <username>
"""
import hashlib
import json
import os
import sys
import getpass

USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "users.json")


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _load() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE) as f:
        return json.load(f)


def _save(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)
    print(f"Saved {USERS_FILE}")


def cmd_list():
    users = _load()
    if not users:
        print("No users configured.")
        return
    print(f"{'Username':<20} {'Name':<30} {'Role'}")
    print("-" * 55)
    for username, u in users.items():
        print(f"{username:<20} {u.get('name', ''):<30} {u['role']}")


def cmd_add(username, name, role):
    if role not in ("admin", "viewer"):
        print("Role must be 'admin' or 'viewer'.")
        sys.exit(1)
    users = _load()
    if username in users:
        print(f"User '{username}' already exists. Use set-password to change password.")
        sys.exit(1)
    password = getpass.getpass(f"Set password for {username}: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)
    users[username] = {"name": name, "role": role, "password_hash": _hash(password)}
    _save(users)
    print(f"User '{username}' added with role '{role}'.")


def cmd_set_password(username):
    users = _load()
    if username not in users:
        print(f"User '{username}' not found.")
        sys.exit(1)
    password = getpass.getpass(f"New password for {username}: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)
    users[username]["password_hash"] = _hash(password)
    _save(users)
    print(f"Password updated for '{username}'.")


def cmd_remove(username):
    users = _load()
    if username not in users:
        print(f"User '{username}' not found.")
        sys.exit(1)
    confirm = input(f"Remove user '{username}'? (yes/no): ")
    if confirm.lower() != "yes":
        print("Aborted.")
        return
    del users[username]
    _save(users)
    print(f"User '{username}' removed.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "list":
        cmd_list()
    elif args[0] == "add" and len(args) == 4:
        cmd_add(args[1], args[2], args[3])
    elif args[0] == "set-password" and len(args) == 2:
        cmd_set_password(args[1])
    elif args[0] == "remove" and len(args) == 2:
        cmd_remove(args[1])
    else:
        print(__doc__)
        sys.exit(1)
