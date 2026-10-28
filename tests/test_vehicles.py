# -*- coding: utf-8 -*-
import copy
import types
import sys
import unittest
from unittest.mock import patch

from capture.vehicles import local_icon, normalize_vehicles, resolve_vehicles
from capture.normalizer import normalize_snapshot
from capture.snapshot import make_snapshot
from capture.native import derive_credits
from capture.presentation import build_payload
from core.ledger import EconomyLedger, LedgerValidationError
from test_native_finance import Reusable
from test_snapshot import fixture
import test_capture_runtime as runtime_tests

ICON = 'coui://gui/maps/icons/vehicle/usa-A01_T1_Cunningham.png'
TANK = {'vehicle_type_id':'321', 'name':'XM57', 'tier':8, 'icon':ICON}
EVENT_ICONS = (
    ('Avispa', 'france-F17_AMX_13_90_Halloween_event'),
    ('Cerbero', 'uk-GB24_Centurion_Mk3_Halloween_event'),
    ('Doble', 'ussr-R171_IS_3_II_hw21'),
    ('Granadero', 'usa-A100_T49_Halloween_event'),
    ('Malaquita', 'ussr-R40_T-54_Halloween_event'),
    ('Legio Ferrata', 'italy-It19_Progetto_C50_mod_66_hw21'),
    ('Devastador', 'uk-GB123_GSOR_1006_v7_Halloween_event'),
)


def record():
    snapshot = make_snapshot(fixture(), 'NA')
    snapshot['native_credits'] = derive_credits(fixture(), lambda _: Reusable())
    return normalize_snapshot(snapshot)


class VehicleTests(unittest.TestCase):
    def test_native_identity_resolves_once_per_own_type_without_mutating_input(self):
        rows = [{'vehicle_type_id':'321'}, {'vehicle_type_id':321}, {'vehicle_type_id':'654'}]
        before = copy.deepcopy(rows)
        seen=[]
        def getter(cd):
            seen.append(cd)
            return types.SimpleNamespace(userName='Tanque '+str(cd), level=11, icon='img://'+ICON[7:])
        resolved=resolve_vehicles(rows,getter)
        self.assertEqual(seen,[321,654])
        self.assertEqual(rows,before)
        self.assertEqual(resolved[0]['tier'],11)
        self.assertEqual(resolved[0]['icon'],ICON)

    def test_missing_item_and_broken_resources_do_not_block_identity(self):
        def fail(cd):raise RuntimeError('not ready')
        self.assertEqual(resolve_vehicles([{'vehicle_type_id':'321'}],fail),
                         [{'vehicle_type_id':'321','name':'Vehículo 321','tier':None,'icon':None}])

    def test_only_native_tank_art_is_accepted(self):
        self.assertEqual(local_icon('img://'+ICON[7:]),ICON)
        for unsafe in ['https://example.com/tank.png','coui://gui/maps/icons/vehicle/../private.png',
                       'coui://gui/maps/icons/vehicle/a.png?x=1','file:///tank.png','gui/maps/icons/vehicle//a.png',
                       'halloween/../gui/maps/icons/vehicle/a.png',
                       'halloween/gui/maps/icons/vehicle/../a.extend.png',
                       'halloween/gui/maps/icons/vehicle/%2e%2e/a.extend.png',
                       'halloween/gui/maps/icons/vehicle//a.extend.png',
                       'halloween/gui/maps/icons/vehicleTypes/heavyTank.png',
                       'unknown/gui/maps/icons/vehicle/tank.extend.png']:
            self.assertIsNone(local_icon(unsafe))

    def test_current_event_native_images_and_level_are_preserved_by_result_identity(self):
        # Paths and level verified in the installed client's generated R image
        # map and native vehicle list; translated names are test data only.
        items = {}
        rows = []
        for number, (name, stem) in enumerate(EVENT_ICONS, 1):
            icon = 'img://halloween/gui/maps/icons/vehicle/' + stem + '.extend.png'
            items[number] = types.SimpleNamespace(userName=name, level=9, icon=icon)
            rows.append({'vehicle_type_id':str(number)})
        calls = []
        def getter(cd):
            calls.append(cd)
            return items[cd]
        resolved = resolve_vehicles(rows, getter)
        self.assertEqual(calls, list(range(1, 8)))
        self.assertEqual([row['name'] for row in resolved], [row[0] for row in EVENT_ICONS])
        for number, row in enumerate(resolved, 1):
            self.assertEqual(row['vehicle_type_id'], str(number))
            self.assertEqual(row['tier'], 9)
            self.assertEqual(row['icon'], 'coui://' + items[number].icon[6:])

    def test_native_levels_eight_to_eleven_are_not_replaced_by_event_assumptions(self):
        for tier in (8, 9, 10, 11):
            item = types.SimpleNamespace(userName='Tanque', level=tier, icon=ICON)
            self.assertEqual(resolve_vehicles([{'vehicle_type_id':'321'}], lambda _:item)[0]['tier'], tier)

    def test_unavailable_image_does_not_discard_available_native_name_and_tier(self):
        class Item(object):
            userName = 'Legio Ferrata'
            level = 9
            @property
            def icon(self):
                raise RuntimeError('event image resource is not yet registered')
        resolved = resolve_vehicles([{'vehicle_type_id':'321'}], lambda _:Item())[0]
        self.assertEqual(resolved, {'vehicle_type_id':'321', 'name':'Legio Ferrata', 'tier':9, 'icon':None})

    def test_unavailable_name_preserves_existing_name_with_updated_native_art(self):
        class Item(object):
            level = 9
            icon = 'img://halloween/gui/maps/icons/vehicle/ussr-R171_IS_3_II_hw21.extend.png'
            @property
            def userName(self):
                raise RuntimeError('localization is not yet registered')
        original = {'vehicle_type_id':'321', 'name':'Doble', 'tier':None, 'icon':None}
        resolved = resolve_vehicles([original], lambda _:Item())[0]
        self.assertEqual(resolved['name'], 'Doble')
        self.assertEqual(resolved['tier'], 9)
        self.assertEqual(resolved['icon'], 'coui://' + Item.icon[6:])
        self.assertIsNone(original['tier'])
        self.assertIsNone(original['icon'])

    def test_legacy_records_load_without_metadata_and_keep_totals(self):
        row=record();row.pop('vehicles')
        ledger=EconomyLedger();ledger.upsert_result(row)
        self.assertEqual(ledger.list_results()[0]['vehicles'],[])
        self.assertEqual(EconomyLedger.from_dict(ledger.to_dict()).summary('NA','101')['net_credits'],51500)

    def test_metadata_survives_older_callbacks_and_is_copied_to_history(self):
        row=record(); row['vehicles']=[TANK]
        ledger=EconomyLedger();ledger.upsert_result(row)
        older=record();ledger.upsert_result(older)
        payload=build_payload(ledger,'NA','101',{},None)
        self.assertEqual(payload['history'][0]['vehicles'],[TANK])
        self.assertEqual(payload['summary']['net_credits'],51500)
        payload['history'][0]['vehicles'][0]['name']='changed'
        self.assertEqual(ledger.list_results()[0]['vehicles'][0]['name'],'XM57')

    def test_multivehicle_battle_keeps_one_financial_aggregate(self):
        snapshot=make_snapshot(fixture(),'NA')
        snapshot['personal']['vehicles'].append({'vehicle_type_id':'654','name':'Pz. Neu','tier':11,'icon':None})
        snapshot['native_credits']=derive_credits(fixture(),lambda _:Reusable())
        ledger=EconomyLedger();ledger.upsert_result(normalize_snapshot(snapshot))
        self.assertEqual(len(ledger.list_results()[0]['vehicles']),2)
        self.assertEqual(ledger.summary('NA','101')['battle_count'],1)
        self.assertEqual(ledger.summary('NA','101')['net_credits'],51500)

    def test_invalid_persisted_tier_or_remote_art_is_rejected(self):
        for field,value in [('tier',True),('tier',0),('tier',21),('icon','https://example.com/tank.png')]:
            row=record();row['vehicles']=[dict(TANK,**{field:value})]
            with self.assertRaises(LedgerValidationError):EconomyLedger().upsert_result(row)


class VehicleRuntimeTests(unittest.TestCase):
    setUp = runtime_tests.RuntimeTests.setUp
    tearDown = runtime_tests.RuntimeTests.tearDown
    def test_native_item_cache_uses_battle_descriptor_and_reuses_it(self):
        calls=[]
        item=types.SimpleNamespace(userName='XM57',level=8,icon=ICON)
        cache=types.SimpleNamespace(items=types.SimpleNamespace(getItemByCD=lambda cd:calls.append(cd) or item))
        helpers=types.ModuleType('helpers');helpers.dependency=types.SimpleNamespace(instance=lambda interface:cache)
        shared=types.ModuleType('skeletons.gui.shared');shared.IItemsCache=object()
        with patch.dict(sys.modules,{'helpers':helpers,'skeletons.gui.shared':shared}):
            self.assertIs(self.collector._vehicle_item(321),item)
            self.assertIs(self.collector._vehicle_item(321),item)
        self.assertEqual(calls,[321])
    def test_event_persists_and_presents_historical_tank_metadata(self):
        item=types.SimpleNamespace(userName='XM57',level=8,icon=ICON)
        with patch.object(self.collector,'_vehicle_item',return_value=item) as getter:
            self.events.onBattleResultsReceived.emit(True,fixture())
        getter.assert_called_once_with(321)
        self.assertEqual(self.collector.panel_payload()['history'][0]['vehicles'],[TANK])
        self.assertEqual(self.collector.ledger.summary('NA','101')['net_credits'],51500)

    def test_legacy_capture_backfill_changes_only_vehicle_metadata(self):
        old=record();old.pop('vehicles')
        self.collector.ledger.upsert_result(old)
        self.collector.store.save(make_snapshot(fixture(),'NA'))
        before=self.collector.ledger.list_results()[0]
        with patch.object(self.collector,'_vehicle_item',return_value=types.SimpleNamespace(userName='XM57',level=8,icon=ICON)):
            payload=self.collector.panel_payload()
        after=self.collector.ledger.list_results()[0]
        for field in before:
            if field!='vehicles':self.assertEqual(before[field],after[field])
        self.assertEqual(payload['history'][0]['vehicles'],[TANK])

    def test_foreign_snapshot_cannot_supply_vehicle_for_this_account(self):
        self.collector.ledger.upsert_result(record())
        other=make_snapshot(fixture(),'NA');other['account_id']='999'
        with patch.object(self.collector,'_vehicle_item',return_value=None):
            self.collector._enrich_vehicle_history('101',[other])
        self.assertEqual(self.collector.ledger.list_results()[0]['vehicles'][0]['name'],'Vehículo 321')

    def test_failed_metadata_commit_keeps_credit_record_and_can_retry(self):
        self.collector.ledger.upsert_result(record())
        before=self.collector.ledger.to_dict()
        with patch.object(self.collector,'_vehicle_item',return_value=types.SimpleNamespace(userName='XM57',level=8,icon=ICON)):
            with patch.object(EconomyLedger,'save',side_effect=OSError('synthetic')):
                self.collector._enrich_vehicle_history('101',[])
            self.assertEqual(self.collector.ledger.to_dict(),before)
            self.collector._enrich_vehicle_history('101',[])
        self.assertEqual(self.collector.ledger.list_results()[0]['vehicles'],[TANK])



