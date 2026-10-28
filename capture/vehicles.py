# -*- coding: utf-8 -*-
"""Own-vehicle identity and local art; no financial values or selected tank."""
import re

try:
    string_types = (basestring,)
    integer_types = (int, long)
    text_type = unicode
except NameError:
    string_types = (str,)
    integer_types = (int,)
    text_type = str


def local_icon(value):
    if not isinstance(value, string_types):
        return None
    value = value.replace('\\', '/')
    for prefix in ('coui://', 'img://', 'res://'):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break
    # The event's generated R resource map uses a mounted image path, including
    # its .extend.png suffix. Vehicle.icon already resolves the correct native
    # resource from this result's type CD; stripping the mount loses that art.
    if not re.match(r'^(?:halloween/)?gui/maps/(?:icons/vehicle|shop/vehicles)/[A-Za-z0-9_./-]+\.png\Z', value):
        return None
    if any(part in ('', '.', '..') for part in value.split('/')):
        return None
    return 'coui://' + value


def normalize_vehicles(rows):
    normalized = []
    seen = set()
    if not isinstance(rows, list):
        return normalized
    for row in rows[:64]:
        if not isinstance(row, dict):
            continue
        identity = row.get('vehicle_type_id')
        if isinstance(identity, bool) or not isinstance(identity, string_types + integer_types):
            continue
        identity = text_type(identity)
        if not identity.isdigit() or not 0 < int(identity) < 2147483648:
            continue
        identity = text_type(int(identity))
        if identity in seen:
            continue
        seen.add(identity)
        name = row.get('name')
        if not isinstance(name, string_types) or not name.strip():
            name = u'Veh\u00edculo ' + identity
        name = u' '.join(name.split())[:160]
        tier = row.get('tier')
        if isinstance(tier, bool) or not isinstance(tier, integer_types) or not 1 <= tier <= 20:
            tier = None
        normalized.append({'vehicle_type_id':identity, 'name':name,
                           'tier':tier, 'icon':local_icon(row.get('icon'))})
    return normalized


def merge_vehicles(existing, incoming):
    rows = normalize_vehicles(existing)
    by_id = dict((row['vehicle_type_id'], row) for row in rows)
    for row in normalize_vehicles(incoming):
        identity = row['vehicle_type_id']
        if identity not in by_id:
            rows.append(row)
            by_id[identity] = row
            continue
        previous = by_id[identity]
        for key in ('name', 'tier', 'icon'):
            if row[key] is not None and not (key == 'name' and row[key] == u'Veh\u00edculo ' + identity):
                previous[key] = row[key]
    return rows


def resolve_vehicles(rows, get_item_by_cd):
    result = normalize_vehicles(rows)
    for row in result:
        try:
            item = get_item_by_cd(int(row['vehicle_type_id']))
            if item is None:
                continue
            # Resolve the fields independently: delayed/missing event artwork
            # must not discard an otherwise available native name or level.
            native = {'vehicle_type_id':row['vehicle_type_id']}
            for key, attribute in (('name', 'userName'), ('tier', 'level'), ('icon', 'icon')):
                try:
                    native[key] = getattr(item, attribute)
                except Exception:
                    continue
            row.update(merge_vehicles([row], [native])[0])
        except Exception:
            # A missing resource must never interrupt credit capture.
            continue
    return result
