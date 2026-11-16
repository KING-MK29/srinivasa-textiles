import os
import sys
import json
import time
import threading
from pathlib import Path
from flask import Blueprint, request, jsonify

PARENT_DIR = str(Path(__file__).resolve().parent.parent)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from utils.logger import logger

store_sync_bp = Blueprint("store_sync_bp", __name__)

DB_DIR = Path(__file__).resolve().parent.parent / "database"
STATE_FILE = DB_DIR / "store_state.json"
DEFAULT_STATE_FILE = DB_DIR / "default_store_state.json"

_lock = threading.Lock()
_state = {}
_version = int(time.time() * 1000)

def _load_initial_state():
    global _state, _version
    with _lock:
        # 1. First priority: Check Supabase PostgreSQL store_state table if available
        try:
            from database.db import query_db, execute_db, get_db_type
            if get_db_type() == "postgres":
                execute_db("""
                    CREATE TABLE IF NOT EXISTS store_state (
                        key VARCHAR(100) PRIMARY KEY,
                        data JSONB NOT NULL,
                        updated_at TIMESTAMP WITH TIMEZONE DEFAULT timezone('utc'::text, now()) NOT NULL
                    )
                """)
                rows = query_db("SELECT key, data, EXTRACT(EPOCH FROM updated_at)*1000 AS ts FROM store_state")
                if rows and len(rows) > 0:
                    _state = {}
                    max_ts = 0
                    for r in rows:
                        _state[r["key"]] = r["data"]
                        if r.get("ts") and r["ts"] > max_ts:
                            max_ts = int(r["ts"])
                    _version = max_ts or int(time.time() * 1000)
                    logger.info(f"Loaded store state from Supabase PostgreSQL (version: {_version})")
                    return
        except Exception as pg_err:
            logger.info(f"Supabase PostgreSQL state load notice: {pg_err}")

        # 2. Local JSON file fallback
        if STATE_FILE.is_file():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    _state = json.load(f)
                _version = int(STATE_FILE.stat().st_mtime * 1000)
                logger.info(f"Loaded store state from {STATE_FILE} (version: {_version})")
                return
            except Exception as e:
                logger.error(f"Error reading {STATE_FILE}: {e}")

        if DEFAULT_STATE_FILE.is_file():
            try:
                with open(DEFAULT_STATE_FILE, "r", encoding="utf-8") as f:
                    _state = json.load(f)
                _version = int(time.time() * 1000)
                _save_state_to_disk()
                logger.info(f"Initialized store state from {DEFAULT_STATE_FILE}")
                return
            except Exception as e:
                logger.error(f"Error reading {DEFAULT_STATE_FILE}: {e}")

        _state = {}
        _version = int(time.time() * 1000)

def _save_state_to_disk():
    # 1. Persist to Supabase PostgreSQL store_state table if connected
    try:
        from database.db import execute_db, get_db_type
        if get_db_type() == "postgres":
            for k, v in _state.items():
                execute_db(
                    """
                    INSERT INTO store_state (key, data, updated_at)
                    VALUES (%s, %s::jsonb, NOW())
                    ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data, updated_at = NOW()
                    """,
                    (k, json.dumps(v))
                )
    except Exception as pg_save_err:
        logger.warning(f"PostgreSQL store_state save warning: {pg_save_err}")

    # 2. Persist to local disk (safely handles read-only filesystems on serverless)
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        temp_file = DB_DIR / "store_state.json.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(_state, f, ensure_ascii=False, indent=2)
        temp_file.replace(STATE_FILE)
    except Exception:
        pass # Ignore read-only filesystem errors on Vercel lambda

# Load state on startup
_load_initial_state()

@store_sync_bp.route("/state", methods=["GET"])
def get_store_state():
    """
    Returns the complete current live store state.
    Supports ?version=XXXX to avoid transferring data if already up to date.
    """
    client_version = request.args.get("version")
    with _lock:
        if client_version and str(_version) == str(client_version):
            return jsonify({
                "success": True,
                "upToDate": True,
                "version": _version
            })

        return jsonify({
            "success": True,
            "upToDate": False,
            "version": _version,
            "state": _state
        })

@store_sync_bp.route("/version", methods=["GET"])
def get_store_version():
    """
    Ultra-lightweight endpoint for clients to poll every few seconds.
    """
    with _lock:
        return jsonify({
            "success": True,
            "version": _version
        })

@store_sync_bp.route("/sync", methods=["POST"])
def sync_store_update():
    """
    Receives state updates from admin (or customer orders/reviews).
    Accepts:
      { "key": "st_catalog_data_v2", "data": [...] }
      or
      { "updates": { "key1": val1, "key2": val2 } }
    """
    global _version
    body = request.get_json(silent=True) or {}

    with _lock:
        updated = False

        if "key" in body and "data" in body:
            key = body["key"]
            _state[key] = body["data"]
            updated = True
        elif "updates" in body and isinstance(body["updates"], dict):
            for k, v in body["updates"].items():
                _state[k] = v
            updated = True
        elif "state" in body and isinstance(body["state"], dict):
            _state.update(body["state"])
            updated = True

        if updated:
            _version = int(time.time() * 1000)
            try:
                _save_state_to_disk()
                logger.info(f"Store state synced successfully (new version: {_version})")
            except Exception as e:
                logger.error(f"Error saving synced store state: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        return jsonify({
            "success": True,
            "version": _version
        })

@store_sync_bp.route("/reset", methods=["POST"])
def reset_store_state():
    """
    Restores the store state to default seed data.
    """
    global _state, _version
    with _lock:
        if DEFAULT_STATE_FILE.is_file():
            try:
                with open(DEFAULT_STATE_FILE, "r", encoding="utf-8") as f:
                    _state = json.load(f)
                _version = int(time.time() * 1000)
                _save_state_to_disk()
                return jsonify({"success": True, "version": _version, "message": "Store reset to defaults"})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": False, "error": "Default state file not found"}), 404

