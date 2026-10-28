# -*- coding: utf-8 -*-
"""Native Wargaming realm identifiers supported by this client build."""
import re

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)


SUPPORTED_REALMS = ("NA", "EU", "ASIA")
SUPPORTED_CLIENTS = ("2.4.1.0", "2.4.1.1")


def client_version(version_document):
    """Read the exact client version without treating adjacent patches as tested."""
    match = re.search(r"<version>\s*v\.([0-9.]+)(?:\s|<)", version_document)
    if match and match.group(1) in SUPPORTED_CLIENTS:
        return match.group(1)
    raise RuntimeError("supported client versions are " + ", ".join(SUPPORTED_CLIENTS))


def supported_realm(realm):
    """Validate one native/build realm without mapping different regions."""
    if isinstance(realm, string_types):
        realm = realm.strip().upper()
    if realm not in SUPPORTED_REALMS:
        raise RuntimeError("supported Wargaming realms are NA, EU and ASIA")
    return realm


def resolve_realm(native_constants):
    """Keep the client's actual realm; authentication is only a fallback.

    An unsupported CURRENT_REALM must not be replaced with a supported
    AUTH_REALM. In particular, RU is a different client, not an Asia alias.
    Validate before the collector creates directories or reads account data.
    """
    realm = getattr(native_constants, "CURRENT_REALM", None)
    if realm is None or realm == "":
        realm = getattr(native_constants, "AUTH_REALM", None)
    return supported_realm(realm)
