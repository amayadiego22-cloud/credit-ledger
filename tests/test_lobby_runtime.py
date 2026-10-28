"""Garage recovery follows the native GUI space and the account lifecycle."""
import sys
import copy
import types
import unittest
from unittest.mock import patch

import test_capture_runtime as harness


LOGIN = 0
LOBBY = 3
BATTLE = 2


class FakeAppLoader(object):
    def __init__(self, space=LOGIN):
        self.space = space
        self.read_error = False
        self.onGUISpaceEntered = harness.Event()
        self.onGUISpaceLeft = harness.Event()
        self.onGUIInitialized = harness.Event()

    def getSpaceID(self):
        if self.read_error:
            raise RuntimeError("synthetic native space lookup failure")
        return self.space


class LobbyRuntimeTests(unittest.TestCase):
    def setUp(self):
        harness.RuntimeTests.setUp(self)
        self.loader = FakeAppLoader()
        helpers = types.ModuleType("helpers")
        self.loader_contract = object()
        helpers.dependency = types.SimpleNamespace(instance=lambda interface: self.loader)
        app_loader = types.ModuleType("skeletons.gui.app_loader")
        app_loader.IAppLoader = self.loader_contract
        app_loader.GuiGlobalSpaceID = types.SimpleNamespace(LOBBY=LOBBY)
        self.loader_modules = patch.dict(sys.modules, {
            "helpers": helpers,
            "skeletons": types.ModuleType("skeletons"),
            "skeletons.gui": types.ModuleType("skeletons.gui"),
            "skeletons.gui.app_loader": app_loader,
        })
        self.loader_modules.start()

    def tearDown(self):
        self.loader_modules.stop()
        harness.RuntimeTests.tearDown(self)

    def bind(self, space=LOBBY):
        self.loader.space = space
        self.assertTrue(self.collector._bind_lobby())

    def no_native_service(self):
        self.collector._app_loader = None
        self.collector._lobby_space_id = None
        return patch.object(self.collector, "_bind_lobby", return_value=False)

    def test_native_event_registration_is_idempotent_and_close_unsubscribes(self):
        self.bind(LOGIN)
        self.assertTrue(self.collector._bind_lobby())
        events = (self.loader.onGUISpaceEntered, self.loader.onGUISpaceLeft,
                  self.loader.onGUIInitialized)
        self.assertEqual([len(event.handlers) for event in events], [1, 1, 1])
        self.collector.close()
        self.assertEqual([len(event.handlers) for event in events], [0, 0, 0])
        self.assertEqual(self.events.onAccountBecomePlayer.handlers, [])

    def test_late_binding_in_current_lobby_recovers_without_gui_event_or_balance(self):
        self.assertIsNone(self.balance)
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.bind(LOBBY)
            self.collector._ensure_garage_widget()
            ensure.assert_called_with(restore=False)
            self.assertTrue(self.collector._garage_recovery_allowed)

    def test_late_lobby_bind_arms_pending_account_and_opens_after_identity_sync(self):
        self.account.databaseID = None
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.bind(LOBBY)
            self.assertTrue(self.collector._garage_recovery_allowed)
            self.collector._ensure_garage_widget()
            ensure.assert_not_called()
            self.account.databaseID = 101
            self.collector._tick()
            ensure.assert_called_with(restore=False)

    def test_lobby_entry_arms_pending_identity_but_space_loss_and_logout_need_new_entry(self):
        self.bind(LOGIN)
        self.account.databaseID = None
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.loader.space = LOBBY
            self.loader.onGUISpaceEntered.emit(LOBBY)
            self.assertTrue(self.collector._garage_recovery_allowed)
            ensure.assert_not_called()
            self.account.databaseID = 101
            self.collector._wallet_changed()
            ensure.assert_called_with(restore=False)
            ensure.reset_mock()
            self.loader.space = LOGIN
            self.loader.onGUISpaceLeft.emit(LOBBY)
            self.assertFalse(self.collector._garage_recovery_allowed)
            self.loader.space = LOBBY
            self.loader.onGUIInitialized.emit()
            self.collector._wallet_changed()
            ensure.assert_not_called()
            self.loader.onGUISpaceEntered.emit(LOBBY)
            ensure.assert_called_with(restore=True)
            ensure.reset_mock()
            self.events.onAccountBecomeNonPlayer.emit()
            self.loader.onGUIInitialized.emit()
            self.collector._wallet_changed()
            ensure.assert_not_called()
            self.assertFalse(self.collector._garage_recovery_allowed)

    def test_login_space_overrides_synced_balance_and_account_gui_event(self):
        self.bind(LOGIN)
        self.balance = 22000000
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.events.onAccountBecomePlayer.emit()
            self.events.onAccountShowGUI.emit({"databaseID": 101})
            self.collector._ensure_garage_widget(restore=True)
            self.collector._wallet_changed()
            self.collector._tick()
            ensure.assert_not_called()

    def test_entering_lobby_restores_but_polling_does_not_raise_the_window(self):
        self.bind(LOGIN)
        self.events.onAccountBecomePlayer.emit()
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.loader.space = LOBBY
            self.loader.onGUISpaceEntered.emit(LOBBY)
            ensure.assert_called_with(restore=True)
            previous = ensure.call_count
            self.collector._ensure_garage_widget()
            self.assertEqual(ensure.call_count, previous + 1)
            ensure.assert_called_with(restore=False)

    def test_gui_initialized_without_arguments_recovers_only_in_lobby(self):
        self.bind(LOBBY)
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.loader.onGUIInitialized.emit()
            ensure.assert_called_with(restore=True)
            previous = ensure.call_count
            self.loader.space = LOGIN
            self.loader.onGUIInitialized.emit()
            self.assertEqual(ensure.call_count, previous)

    def test_leaving_lobby_closes_immediately_and_battle_never_reopens(self):
        self.bind(LOBBY)
        self.balance = 22000000
        with patch.object(self.collector.panel, "ensure_visible") as ensure, \
                patch.object(self.collector.panel, "close_window") as close:
            self.collector._ensure_garage_widget()
            previous = ensure.call_count
            self.loader.space = BATTLE
            self.loader.onGUISpaceLeft.emit(LOBBY)
            close.assert_called()
            self.loader.onGUISpaceEntered.emit(BATTLE)
            self.collector._wallet_changed()
            self.collector._tick()
            self.assertEqual(ensure.call_count, previous)

    def test_avatar_and_late_gui_event_cannot_reopen_over_a_stale_lobby_space(self):
        self.bind(LOBBY)
        self.balance = 22000000
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.account = types.SimpleNamespace(arenaUniqueID=901, playerVehicleID=1,
                arena=types.SimpleNamespace(vehicles={1: {"accountDBID": 101}}))
            self.events.onAvatarBecomePlayer.emit()
            self.events.onAccountShowGUI.emit({"databaseID": 101})
            self.collector._wallet_changed()
            self.collector._tick()
            ensure.assert_not_called()

    def test_logout_blocks_late_gui_initialization_and_timer_with_cached_account(self):
        self.bind(LOBBY)
        self.balance = 22000000
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.events.onAccountBecomeNonPlayer.emit()
            self.loader.onGUIInitialized.emit()
            self.collector._wallet_changed()
            self.collector._tick()
            ensure.assert_not_called()
            self.assertFalse(self.collector._garage_recovery_allowed)
            self.events.onAccountBecomePlayer.emit()
            self.collector._ensure_garage_widget()
            ensure.assert_called_with(restore=False)

    def test_replay_and_stopped_collector_never_open_even_in_lobby(self):
        self.bind(LOBBY)
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.replay.isPlaying = lambda: True
            self.collector._ensure_garage_widget(restore=True)
            ensure.assert_not_called()
            self.replay.isPlaying = lambda: False
            self.collector._alive = False
            self.collector._ensure_garage_widget(restore=True)
            ensure.assert_not_called()
            self.collector._alive = True

    def test_native_space_lookup_failure_is_not_a_permissive_balance_fallback(self):
        self.bind(LOBBY)
        self.balance = 22000000
        self.loader.read_error = True
        with patch.object(self.collector.panel, "ensure_visible") as ensure, \
                patch.object(self.collector.panel, "close_window") as close, \
                patch.object(self.collector, "_error"):
            self.collector._ensure_garage_widget(restore=True)
            ensure.assert_not_called()
            close.assert_called()
            self.assertIs(self.collector._app_loader, self.loader)

    def test_native_garage_route_still_requires_account_and_accepts_unsynced_or_zero_balance(self):
        with self.no_native_service(), patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.collector._ensure_garage_widget()
            ensure.assert_not_called()
            self.events.onAccountBecomePlayer.emit()
            self.collector._ensure_garage_widget()
            ensure.assert_called_with(restore=False)
            self.balance = 0
            self.collector._ensure_garage_widget()
            ensure.assert_called_with(restore=False)
            previous = ensure.call_count
            self.events.onAccountBecomeNonPlayer.emit()
            self.collector._ensure_garage_widget()
            self.assertEqual(ensure.call_count, previous)

    def test_missing_service_explicit_account_gui_can_show_pending_balance(self):
        with self.no_native_service(), patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.events.onAccountShowGUI.emit({"databaseID": 101})
            ensure.assert_called_with(restore=True)
            self.assertIsNone(self.balance)

    def test_ui_recovery_precedes_financial_io_failures_on_wallet_and_tick(self):
        self.bind(LOBBY)
        with patch.object(self.collector.panel, "ensure_visible") as ensure, \
                patch.object(self.collector, "_sync_finance", side_effect=OSError("synthetic finance write failure")), \
                patch.object(self.collector, "_error"):
            self.collector._wallet_changed()
            ensure.assert_called_with(restore=False)
            previous = ensure.call_count
            self.collector._tick()
            self.assertEqual(ensure.call_count, previous + 1)
            ensure.assert_called_with(restore=False)

    def test_native_lobby_still_requires_an_account_player_before_showing(self):
        self.bind(LOBBY)
        self.balance = 22000000
        self.account = types.SimpleNamespace(databaseID=101)
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.events.onAccountShowGUI.emit({"databaseID": 101})
            self.collector._ensure_garage_widget(restore=True)
            ensure.assert_not_called()

    def test_navigation_hides_immediately_and_return_restores_without_financial_changes(self):
        self.bind(LOBBY)
        self.balance = 22000000
        self.collector._sync_finance()
        before = (copy.deepcopy(self.collector.config), self.collector.ledger.to_dict(),
                  copy.deepcopy(self.collector.wallet.data))
        event = self.lobby_machine.onVisibleRouteChanged
        with patch.object(self.collector.panel, "ensure_visible") as ensure, \
                patch.object(self.collector.panel, "close_window") as close:
            for page in ("techtree", "service_record", "store", "missions", "mode_selector",
                         "battle_results", "vehicle_preview", "loadout"):
                with self.subTest(page=page):
                    self.lobby_machine.visibleState = types.SimpleNamespace(hangar=False, name=page)
                    event.emit(types.SimpleNamespace(state=self.lobby_machine.visibleState))
                    self.assertFalse(self.collector._garage_visible)
                    close.assert_called()
                    self.assertTrue(self.collector._garage_recovery_allowed)
                    self.lobby_machine.visibleState = self.garage_state
                    event.emit(types.SimpleNamespace(state=self.garage_state))
                    ensure.assert_called_with(restore=True)
                    self.assertTrue(self.collector._garage_visible)
        self.assertEqual(before, (self.collector.config, self.collector.ledger.to_dict(),
                                  self.collector.wallet.data))

    def test_tick_wallet_and_account_gui_cannot_restore_over_another_lobby_page(self):
        self.bind(LOBBY)
        self.balance = 22000000
        self.lobby_machine.visibleState = types.SimpleNamespace(hangar=False)
        self.lobby_machine.onVisibleRouteChanged.emit(None)
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            self.events.onAccountShowGUI.emit({"databaseID": 101})
            self.collector._wallet_changed()
            self.collector._tick()
            self.loader.onGUIInitialized.emit()
            ensure.assert_not_called()
            self.assertFalse(self.collector._garage_visible)

    def test_loading_missing_or_failed_route_is_not_evidence_of_a_visible_garage(self):
        self.bind(LOBBY)
        self.balance = 22000000
        machine = self.lobby_machine
        with patch.object(self.collector.panel, "ensure_visible") as ensure:
            machine.visibleState = None
            self.collector._ensure_garage_widget(restore=True)
            self.lobby_machine = None
            self.collector._ensure_garage_widget(restore=True)
            self.assertEqual(machine.onVisibleRouteChanged.handlers, [])
            self.lobby_machine = machine
            machine.visibleState = self.garage_state
            states = sys.modules["gui.lobby_state_machine.states"]
            with patch.object(states, "isHangarState", side_effect=RuntimeError("route unavailable")):
                self.collector._ensure_garage_widget(restore=True)
            ensure.assert_not_called()
            self.collector._ensure_garage_widget(restore=True)
            ensure.assert_called_with(restore=True)

    def test_route_binding_replaces_old_machine_and_unsubscribes_on_logout_and_close(self):
        self.bind(LOBBY)
        old = self.lobby_machine
        self.assertEqual(len(old.onVisibleRouteChanged.handlers), 1)
        self.lobby_machine = types.SimpleNamespace(visibleState=self.garage_state,
                                                  onVisibleRouteChanged=harness.Event())
        self.collector._ensure_garage_widget()
        self.assertEqual(old.onVisibleRouteChanged.handlers, [])
        event = self.lobby_machine.onVisibleRouteChanged
        self.assertEqual(len(event.handlers), 1)
        self.events.onAccountBecomeNonPlayer.emit()
        self.assertEqual(event.handlers, [])
        self.events.onAccountBecomePlayer.emit()
        self.assertEqual(len(event.handlers), 1)
        self.collector.close()
        self.assertEqual(event.handlers, [])


if __name__ == "__main__":
    unittest.main()
