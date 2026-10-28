# -*- coding: utf-8 -*-
"""Local JSON storage, with a journal for the client's Windows Python 2."""
import io
import json
import os
import re
import tempfile
import time


def _replace(source, destination):
    if hasattr(os, "replace"):
        os.replace(source, destination)
    elif os.name == "nt":
        _journal_replace(source, destination)
    else:
        os.rename(source, destination)


def _journal_replace(source, destination):
    previous = destination + ".previous"
    if not os.path.exists(destination):
        os.rename(source, destination)
        return
    if os.path.exists(previous):
        os.unlink(previous)
    os.rename(destination, previous)
    try:
        os.rename(source, destination)
    except Exception:
        if not os.path.exists(destination):
            os.rename(previous, destination)
        raise


def _recover_previous(path):
    if not os.path.exists(path) and os.path.isfile(path + ".previous"):
        os.rename(path + ".previous", path)
    return path


def json_exists(path):
    return os.path.isfile(path) or os.path.isfile(path + ".previous")


def atomic_json(path, value):
    destination = _recover_previous(os.path.abspath(path))
    directory = os.path.dirname(destination)
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory)
        except OSError:
            if not os.path.isdir(directory):
                raise
    payload = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8")
    if len(payload) > 2 * 1024 * 1024:
        raise ValueError("capture document exceeds 2 MiB")
    descriptor, temporary = tempfile.mkstemp(prefix=".credit-ledger-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.write(b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        _replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path):
    with io.open(_recover_previous(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _component(value, expression):
    if not isinstance(value, type(u"")):
        value = str(value)
    if len(value) > 64 or not re.match(expression + r"\Z", value):
        raise ValueError("unsafe capture identity")
    return value


class CaptureStore(object):
    def __init__(self, directory):
        self.directory = os.path.abspath(directory)
        self._mode_metadata_cache = {}
        self._mode_metadata_cursor = {}

    def mode_metadata(self, region, account_id, battle_ids, read_limit=25):
        """Read small batches of own legacy context beyond the recent cache.

        Cache only context and a file signature, never whole financial snapshots.
        Missing files are retried when they appear; corrupt files have a short
        backoff. Rotating candidates prevents repeated errors starving history.
        """
        region = _component(region, r"[A-Z0-9_-]+")
        account = _component(account_id, r"[0-9]+")
        directory = os.path.join(self.directory, "captures", region, account)
        identities = []
        for battle_id in battle_ids:
            try:
                identities.append(_component(battle_id, r"[0-9]+"))
            except ValueError:
                continue
        if not identities:
            return []
        owner = (region, account)
        start = self._mode_metadata_cursor.get(owner, 0) % len(identities)
        identities = identities[start:] + identities[:start]
        self._mode_metadata_cursor[owner] = (start + max(1, read_limit)) % len(identities)
        result, reads = [], 0
        now = time.time()
        for battle in identities:
            key = (region, account, battle)
            path = os.path.join(directory, battle + ".json")
            def signature():
                candidate = path if os.path.isfile(path) else path + ".previous"
                try:
                    stat = os.stat(candidate)
                    return (candidate, stat.st_mtime, stat.st_size)
                except (OSError, IOError):
                    return None
            observed = signature()
            cached = self._mode_metadata_cache.get(key)
            if cached is not None and cached[0] == observed and (not cached[2] or now < cached[2]):
                metadata = cached[1]
            elif observed is None:
                metadata = None
                self._mode_metadata_cache[key] = (None, None, 0)
            elif reads >= read_limit:
                continue
            else:
                reads += 1
                metadata = None
                retry_at = 0
                try:
                    snapshot = read_json(path)
                    if (isinstance(snapshot, dict) and snapshot.get("region") == region
                            and snapshot.get("account_id") == account and snapshot.get("battle_id") == battle):
                        common = snapshot.get("common")
                        if isinstance(common, dict):
                            metadata = {"region": region, "account_id": account, "battle_id": battle,
                                "common": dict((name, common[name]) for name in
                                    ("bonusType", "arenaBonusType", "guiType") if name in common)}
                except (ValueError, OSError, IOError):
                    retry_at = now + 30
                self._mode_metadata_cache[key] = (signature(), metadata, retry_at)
            if metadata is not None:
                result.append(dict(metadata, common=dict(metadata["common"])))
        return result

    def save(self, snapshot):
        region = _component(snapshot["region"], r"[A-Z0-9_-]+")
        account = _component(snapshot["account_id"], r"[0-9]+")
        battle = _component(snapshot["battle_id"], r"[0-9]+")
        path = os.path.join(self.directory, "captures", region, account, battle + ".json")
        existed = json_exists(path)
        if existed:
            previous = read_json(path)
            comparable_previous = dict(previous)
            comparable_current = dict(snapshot)
            for key in ("captured_at", "source"):
                comparable_previous.pop(key, None)
                comparable_current.pop(key, None)
            if comparable_previous == comparable_current:
                return "unchanged", path
        atomic_json(path, snapshot)
        return "updated" if existed else "inserted", path

    def write_status(self, value):
        atomic_json(os.path.join(self.directory, "status.json"), value)

    def recovery_candidates(self, region, account_id):
        region = _component(region, r"[A-Z0-9_-]+")
        account = _component(account_id, r"[0-9]+")
        directory = os.path.join(self.directory, "captures", region, account)
        if not os.path.isdir(directory):
            return []
        paths = set()
        for name in os.listdir(directory):
            main_name = name[:-9] if name.endswith(".previous") else name
            if re.match(r"[0-9]+\.json\Z", main_name):
                paths.add(os.path.join(directory, main_name))
        def modified(path):
            return os.path.getmtime(path if os.path.isfile(path) else path + ".previous")
        results = []
        for path in sorted(paths, key=modified, reverse=True)[:100]:
            try:
                snapshot = read_json(path)
                if snapshot.get("region") == region and snapshot.get("account_id") == account:
                    results.append(snapshot)
            except (ValueError, OSError, IOError):
                # Preserve a corrupt file for inspection; never replace it with zero.
                continue
        return results
