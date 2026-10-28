"""Check the panel's native API contract without running or importing the game."""
import contextlib
import json
import types
import unittest
from unittest.mock import patch

from capture.panel import LedgerPanel


class Command:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.handlers.remove(handler)
        return self

    def notify(self, args=None):
        for handler in list(self.handlers):
            if args is None:
                handler()
            else:
                handler(args)


class Model:
    def __init__(self, properties, commands):
        self.expected_properties = properties
        self.expected_commands = commands
        self.values = []
        self.commands = []
        self.writes = 0
        self.payload_history = []
        # The real ViewModel constructor invokes the subclass override once.
        self._initialize()

    def _initialize(self):
        pass

    def _addStringProperty(self, name, default):
        self.values.append(default)

    def _addCommand(self, name):
        command = Command()
        self.commands.append(command)
        return command

    def _setString(self, index, value):
        self.values[index] = value
        self.writes += 1
        self.payload_history.append(json.loads(value))

    @contextlib.contextmanager
    def transaction(self):
        yield self


class View:
    def __init__(self, settings):
        self.model = settings.model
        self.finalized = False

    def getViewModel(self):
        return self.model

    def _onLoading(self):
        for event, handler in self._getEvents():
            event += handler

    def _finalize(self):
        for event, handler in self._getEvents():
            event -= handler
        self.finalized = True


class PanelHarness:
    def __init__(self):
        self.windows = []
        self.layout_id = 123
        self.main_window = types.SimpleNamespace(proxy=object())
        harness = self

        class Settings:
            def __init__(self, layout_id, flags, model):
                self.layout_id, self.flags, self.model = layout_id, flags, model

        class Window:
            def __init__(self, flags, content, decorator, layer, parent):
                self.flags, self.content = flags, content
                self.decorator, self.layer, self.parent = decorator, layer, parent
                self.proxy = object()
                self.isReady = False
                self.isVisible = False
                self.loaded = 0
                self.focus_requests = []
                self.destroyed = 0
                self.onPositionChanged = Command()
                self.onSizeChanged = Command()
                self.position = (0, 0)
                self.size = (256, 256)
                self.moves = []
                harness.windows.append(self)

            def load(self):
                self.loaded += 1
                self.content._onLoading()
                # Native _cReady marks the window ready before calling _onReady.
                self.isReady = True
                self._onReady()

            def show(self, focus=True):
                if self.proxy is None:
                    raise RuntimeError("window was destroyed")
                self.focus_requests.append(focus)
                if "isVisible" in self.__dict__:
                    self.isVisible = True

            def isHidden(self):
                return not self.isVisible

            def move(self, x, y):
                self.position = (x, y)
                self.moves.append((x, y))
                self.onPositionChanged.notify((1, x, y))

            def native_resize(self, width, height):
                self.size = (width, height)
                self.onSizeChanged.notify((1, width, height))

            def destroy(self):
                if self.proxy is not None:
                    self.destroyed += 1
                    self.content._finalize()
                    self.proxy = None

        class GuiLoaderInterface:
            pass

        loader = types.SimpleNamespace(windowsManager=types.SimpleNamespace(
            getMainWindow=lambda: self.main_window))

        def dependency_instance(interface):
            if interface is not GuiLoaderInterface:
                raise AssertionError("unexpected native dependency")
            return loader

        resource_root = types.SimpleNamespace(mods=types.SimpleNamespace(
            credit_ledger=types.SimpleNamespace(views=types.SimpleNamespace(
                LedgerView=lambda: self.layout_id))))

        def module(name, **attributes):
            value = types.ModuleType(name)
            value.__dict__.update(attributes)
            return value

        self.modules = {
            "frameworks": module("frameworks"),
            "frameworks.wulf": module("frameworks.wulf", ViewModel=Model,
                ViewSettings=Settings, ViewFlags=types.SimpleNamespace(VIEW=1),
                WindowFlags=types.SimpleNamespace(WINDOW=1, WINDOW_FULLSCREEN=1024),
                WindowLayer=types.SimpleNamespace(WINDOW=7)),
            "gui": module("gui"),
            "gui.impl": module("gui.impl"),
            "gui.impl.pub": module("gui.impl.pub", ViewImpl=View, WindowImpl=Window),
            "gui.impl.gen": module("gui.impl.gen", R=resource_root),
            "helpers": module("helpers", dependency=types.SimpleNamespace(
                instance=dependency_instance)),
            "skeletons": module("skeletons"),
            "skeletons.gui": module("skeletons.gui"),
            "skeletons.gui.impl": module("skeletons.gui.impl", IGuiLoader=GuiLoaderInterface),
        }


class Owner:
    def __init__(self):
        self._alive = True
        self.playing_replay = False
        self.garage_visible = True
        self.replay = types.SimpleNamespace(isPlaying=lambda: self.playing_replay)
        self.panel_error = "previous error"
        self.saved = []
        self.saved_history = []
        self.resets = []
        self.goal_resets = []
        self.vehicle_filters = []
        self.languages = []
        self.view_modes = []
        self.notices = []
        self.payload = {"status": "ready", "net_credits": -113508}
        self.config = {}
        self.callbacks = {}
        self.sequence = 0
        self.positions = []
        self.world = types.SimpleNamespace(callback=self.callback,
                       cancelCallback=lambda token:self.callbacks.pop(token, None))

    def callback(self, delay, function):
        self.sequence += 1
        self.callbacks[self.sequence] = function
        return self.sequence

    def _garage_view_visible(self):
        return self.garage_visible

    def save_panel_position(self, x, y, view_mode=None):
        if view_mode is None:
            self.config["panel_position"] = {"x": x, "y": y}
        else:
            self.config.setdefault("panel_positions", {})[view_mode] = {"x": x, "y": y}
        self.positions.append((x, y))

    def save_panel_view_mode(self, mode):
        self.config["panel_view_mode"] = mode
        self.view_modes.append(mode)

    def flush_callbacks(self):
        for key, callback in list(self.callbacks.items()):
            self.callbacks.pop(key, None)
            callback()

    def panel_payload(self):
        return dict(self.payload)

    def save_goal(self, args):
        self.saved.append(args)

    def save_history_settings(self, args):
        self.saved_history.append(args)

    def reset_history(self, args):
        self.resets.append(args)

    def reset_goal(self, args):
        self.goal_resets.append(args)

    def set_vehicle_filter(self, args):
        self.vehicle_filters.append(args)

    def set_archive_selection(self, args):
        self.archive_filters.append(args)

    def set_language(self, args):
        self.languages.append(args)

    def acknowledge_goal_completion(self, args):
        self.completion_acks.append(args)

    def _notify(self, text):
        self.notices.append(text)


class PanelTests(unittest.TestCase):
    def setUp(self):
        self.harness = PanelHarness()
        self.patcher = patch.dict("sys.modules", self.harness.modules)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.owner = Owner()
        self.owner.archive_filters = []
        self.owner.completion_acks = []
        self.panel = LedgerPanel(self.owner)

    def test_opens_only_one_window_without_raising_an_already_visible_window(self):
        self.panel.open()
        first = self.panel.window
        self.panel.open()
        self.assertEqual(len(self.harness.windows), 1)
        self.assertEqual(first.loaded, 1)
        self.assertEqual(first.focus_requests, [False])
        self.assertEqual(first.flags, 1)
        self.assertIs(first.parent, self.harness.main_window)

    def test_commands_route_payload_and_minimize_without_destroying_the_launcher(self):
        self.panel.open()
        model = self.panel.model
        self.assertEqual(len(model.values), model.expected_properties)
        self.assertEqual(len(model.commands), model.expected_commands)
        self.assertEqual(len(model.commands), 12)
        opening_payload = json.loads(model.values[0])
        self.assertEqual(opening_payload["status"], self.owner.payload["status"])
        self.assertEqual(opening_payload["net_credits"], self.owner.payload["net_credits"])
        self.assertEqual(opening_payload["view_mode"], "widget")
        self.assertEqual(opening_payload["window"], {
            "ready": True, "width": 256, "height": 256})
        opening_revision = opening_payload["revision"]
        command = {"value": "3000000", "mode": "balance"}
        model.onSaveGoal.notify(command)
        self.assertEqual(self.owner.saved, [command])
        self.owner.payload = {"status": "refreshed"}
        model.onRefresh.notify()
        self.assertIsNone(self.owner.panel_error)
        refreshed_payload = json.loads(model.values[0])
        self.assertEqual(refreshed_payload["status"], "refreshed")
        self.assertGreater(refreshed_payload["revision"], opening_revision)
        self.assertEqual(refreshed_payload["window"], opening_payload["window"])
        window = self.panel.window
        model.onClose.notify()
        self.assertIs(self.panel.window, window)
        self.assertIs(self.panel.model, model)
        self.assertEqual(json.loads(model.values[0])["view_mode"], "minimized")
        self.assertEqual(window.destroyed, 0)
        self.panel.close_window()
        self.assertIsNone(self.panel.window)
        self.assertIsNone(self.panel.model)
        self.assertEqual(window.destroyed, 1)
        self.assertTrue(window.content.finalized)
        self.assertTrue(all(not command.handlers for command in model.commands))
        self.assertEqual(window.onPositionChanged.handlers, [])
        self.assertEqual(window.onSizeChanged.handlers, [])

    def test_history_commands_route_settings_and_confirmation_without_coercion(self):
        self.panel.open()
        model = self.panel.model
        settings = {"mode": "daily", "hour": 6, "preserve_goal": False}
        model.onSaveHistory.notify(settings)
        confirmation = {"confirm": True}
        model.onResetHistory.notify(confirmation)
        self.assertEqual(self.owner.saved_history, [settings])
        self.assertEqual(self.owner.resets, [confirmation])
        self.assertIs(self.owner.saved_history[0], settings)
        self.assertIs(self.owner.resets[0], confirmation)
        model.onSaveHistory.notify()
        model.onResetHistory.notify()
        self.assertEqual(self.owner.saved_history, [settings, None])
        self.assertEqual(self.owner.resets, [confirmation, None])
        self.panel.close_window()
        self.assertTrue(all(not command.handlers for command in model.commands))

    def test_explicit_goal_reset_has_its_own_native_command_and_leaves_history_alone(self):
        self.panel.open()
        model = self.panel.model
        self.assertEqual(model.expected_commands, 12)
        self.assertEqual(len(model.commands), 12)
        request = {"value": "1000000", "mode": "balance_growth"}
        model.onResetGoal.notify(request)
        model.onResetGoal.notify()
        self.assertEqual(self.owner.goal_resets, [request, None])
        self.assertIs(self.owner.goal_resets[0], request)
        self.assertEqual(self.owner.saved, [])
        self.assertEqual(self.owner.resets, [])
        self.panel.close_window()
        self.assertTrue(all(not command.handlers for command in model.commands))

    def test_vehicle_filter_native_command_routes_only_the_current_model(self):
        self.panel.open()
        old_model = self.panel.model
        request = {"mode_key": "mode:20", "vehicle_key": "vehicle:321",
                   "request_id": 1, "account_context": "NA:101"}
        old_model.onSetVehicleFilter.notify(request)
        self.assertEqual(self.owner.vehicle_filters, [request])
        self.assertIs(self.owner.vehicle_filters[0], request)
        self.assertEqual(self.owner.saved, [])
        self.assertEqual(self.owner.resets, [])
        self.panel.close_window()
        self.panel.open()
        old_model.onSetVehicleFilter.notify(request)
        self.assertEqual(self.owner.vehicle_filters, [request])
        self.panel.model.onSetVehicleFilter.notify(request)
        self.assertEqual(self.owner.vehicle_filters, [request, request])

    def test_native_readiness_is_published_after_loading_default_sized_window(self):
        self.panel.open()
        payloads = self.panel.model.payload_history
        self.assertGreaterEqual(len(payloads), 2)
        self.assertEqual(payloads[0]["window"], {
            "ready": False, "width": 256, "height": 256})
        self.assertEqual(payloads[-1]["window"], {
            "ready": True, "width": 256, "height": 256})
        self.assertGreater(payloads[-1]["revision"], payloads[0]["revision"])

    def test_archive_day_command_is_appended_and_releases_stale_model_handlers(self):
        self.panel.open()
        old_model = self.panel.model
        self.assertIs(old_model.commands[8], old_model.onSetVehicleFilter)
        self.assertIs(old_model.commands[9], old_model.onSelectHistoryDay)
        query = {"day_key": "2026-10-18T10:00:00Z", "mode_key": "mode:20",
                 "vehicle_key": "vehicle:321", "request_id": "1", "account_context": "NA:101"}
        old_model.onSelectHistoryDay.notify(query)
        self.assertEqual(self.owner.archive_filters, [query])
        self.assertIs(self.owner.archive_filters[0], query)
        self.panel.close_window()
        self.panel.open()
        old_model.onSelectHistoryDay.notify(query)
        self.assertEqual(self.owner.archive_filters, [query])
        self.panel.model.onSelectHistoryDay.notify(query)
        self.assertEqual(self.owner.archive_filters, [query, query])
        self.assertEqual(self.owner.saved, [])
        self.assertEqual(self.owner.resets, [])

    def test_language_is_command_eleven_and_cannot_change_from_a_stale_native_view(self):
        self.panel.open()
        old_model = self.panel.model
        self.assertIs(old_model.commands[10], old_model.onSetLanguage)
        request = {"language": "en", "request_id": "1"}
        old_model.onSetLanguage.notify(request)
        self.assertEqual(self.owner.languages, [request])
        self.assertIs(self.owner.languages[0], request)
        self.assertEqual(self.owner.saved, [])
        self.assertEqual(self.owner.resets, [])
        self.panel.close_window()
        self.panel.open()
        old_model.onSetLanguage.notify(request)
        self.assertEqual(self.owner.languages, [request])
        self.panel.model.onSetLanguage.notify(request)
        self.assertEqual(self.owner.languages, [request, request])

    def test_completion_ack_is_command_twelve_and_stale_model_cannot_consume(self):
        self.panel.open()
        old_model = self.panel.model
        self.assertIs(old_model.commands[10], old_model.onSetLanguage)
        self.assertIs(old_model.commands[11], old_model.onAcknowledgeGoalCompletion)
        args = {"id": "a" * 32, "account_context": "NA:101"}
        old_model.onAcknowledgeGoalCompletion.notify(args)
        self.assertEqual(self.owner.completion_acks, [args])
        self.assertIs(self.owner.completion_acks[0], args)
        self.panel.close_window()
        self.panel.open()
        old_model.onAcknowledgeGoalCompletion.notify(args)
        self.assertEqual(self.owner.completion_acks, [args])
        self.panel.model.onAcknowledgeGoalCompletion.notify(args)
        self.assertEqual(self.owner.completion_acks, [args, args])
        self.assertEqual(self.owner.saved, [])
        self.assertEqual(self.owner.resets, [])

    def test_completion_presence_requires_placed_matching_visible_native_surface(self):
        self.panel.open()
        self.assertFalse(self.panel.completion_surface_ready())
        self.panel.layout_ready({"clientWidth": 2560, "clientHeight": 1440,
            "width": 620, "height": 180, "viewMode": "widget"})
        self.panel.window.native_resize(620, 180)
        self.owner.flush_callbacks()
        self.assertTrue(self.panel.completion_surface_ready())
        self.panel.window.isVisible = False
        self.assertFalse(self.panel.completion_surface_ready())
        self.panel.window.isVisible = True
        self.panel.window.native_resize(256, 256)
        self.assertFalse(self.panel.completion_surface_ready())
        self.panel.window.native_resize(620, 180)
        self.assertTrue(self.panel.completion_surface_ready())
        self.panel._mode = "minimized"
        self.assertFalse(self.panel.completion_surface_ready())
        self.panel.close_window()
        self.assertFalse(self.panel.completion_surface_ready())

    def test_completion_presence_rejects_unknown_or_failed_native_visibility_query(self):
        self.panel.open()
        self.panel.layout_ready({"clientWidth": 2560, "clientHeight": 1440,
            "width": 620, "height": 180, "viewMode": "widget"})
        self.panel.window.native_resize(620, 180)
        self.owner.flush_callbacks()
        self.panel.window.isHidden = lambda: None
        self.assertFalse(self.panel.completion_surface_ready())
        def broken():
            raise RuntimeError("native visibility unavailable")
        self.panel.window.isHidden = broken
        self.assertFalse(self.panel.completion_surface_ready())

    def test_requested_geometry_does_not_replace_actual_native_window_size(self):
        self.panel.open()
        model = self.panel.model
        model.onLayoutReady.notify({"clientWidth": 2560, "clientHeight": 1440,
            "width": 1040, "height": 980, "nativeWidth": 1040, "nativeHeight": 980,
            "viewMode": "widget"})
        self.owner.flush_callbacks()
        self.panel.refresh()
        self.assertEqual(json.loads(model.values[0])["window"], {
            "ready": True, "width": 256, "height": 256})
        self.assertEqual(self.panel._geometry, [2560, 1440, 1040, 980])

    def test_native_resize_event_updates_actual_size_and_revision(self):
        self.panel.open()
        model = self.panel.model
        revision = json.loads(model.values[0])["revision"]
        self.panel.window.native_resize(1040, 980)
        payload = json.loads(model.values[0])
        self.assertEqual(payload["window"], {
            "ready": True, "width": 1040, "height": 980})
        self.assertGreater(payload["revision"], revision)
        self.assertNotIn("window", self.owner.payload)

    def test_detached_native_proxy_publishes_unavailable_geometry(self):
        self.panel.open()
        self.panel.window.proxy = None
        self.panel.refresh(force=True)
        self.assertEqual(json.loads(self.panel.model.values[0])["window"], {
            "ready": False, "width": 0, "height": 0})

    def test_native_finalization_clears_references_and_allows_reopening(self):
        self.panel.open()
        first = self.panel.window
        model = self.panel.model
        first.destroy()
        self.assertIsNone(self.panel.window)
        self.assertIsNone(self.panel.model)
        self.assertTrue(all(not command.handlers for command in model.commands))
        self.assertEqual(first.onPositionChanged.handlers, [])
        self.assertEqual(first.onSizeChanged.handlers, [])
        self.panel.open()
        self.assertEqual(len(self.harness.windows), 2)
        self.assertIsNot(self.panel.window, first)

    def test_reopening_a_loading_window_waits_for_native_readiness(self):
        self.panel.open()
        first = self.panel.window
        first.isReady = False
        self.panel.open()
        self.assertIs(self.panel.window, first)
        self.assertEqual(first.focus_requests, [False])

    def test_invalid_layout_is_contained_and_capture_owner_remains_alive(self):
        self.harness.layout_id = -1
        with patch("capture.panel.traceback.print_exc"), patch("builtins.print"):
            self.panel.open()
        self.assertTrue(self.owner._alive)
        self.assertEqual(self.harness.windows, [])
        self.assertIsNone(self.panel.window)
        self.assertTrue(self.owner.notices)
        self.assertIs(self.panel.owner, self.owner)

    def test_close_destroys_only_the_owned_window_once(self):
        self.panel.open()
        window = self.panel.window
        self.panel.close()
        self.panel.close()
        self.assertEqual(window.destroyed, 1)
        self.assertEqual(window.onPositionChanged.handlers, [])
        self.assertEqual(window.onSizeChanged.handlers, [])

    def test_panel_can_be_created_and_opened_without_a_mods_menu_api(self):
        with patch.dict("sys.modules", {"gui.modsListApi": None}):
            independent = LedgerPanel(self.owner)
            independent.ensure_visible()
            self.assertIsNotNone(independent.window)
            self.assertEqual(independent.window.flags, 1)
            independent.close()
        self.assertFalse(hasattr(independent, "api"))
        self.assertFalse(hasattr(independent, "registered"))

    def test_stopped_owner_and_replay_cannot_open_panel(self):
        self.owner._alive = False
        self.panel.open()
        self.owner._alive = True
        self.owner.playing_replay = True
        self.panel.open()
        self.assertEqual(self.harness.windows, [])

    def test_normal_window_is_positioned_restored_and_clamped_to_new_resolution(self):
        self.owner.config["panel_position"] = {"x": 1200, "y": 500}
        self.owner.config["panel_view_mode"] = "details"
        self.panel.open()
        model = self.panel.model
        model.onLayoutReady.notify({"clientWidth": 1920, "clientHeight":1080,"width":820,"height":740,"viewMode":"details"})
        self.owner.flush_callbacks()
        self.assertEqual(self.panel.window.position, (1100,340))
        self.panel.window.move(200,100)
        self.owner.flush_callbacks()
        self.assertEqual(self.owner.positions[-1], (200,100))
        self.panel.close_window()
        self.assertEqual(self.owner.callbacks, {})
        self.panel.open()
        self.panel.model.onLayoutReady.notify({"clientWidth":1920,"clientHeight":1080,"width":820,"height":740,"viewMode":"details"})
        self.owner.flush_callbacks()
        self.assertEqual(self.panel.window.position, (200,100))
        self.panel.model.onLayoutReady.notify({"clientWidth":1024,"clientHeight":768,"width":820,"height":732,"viewMode":"details"})
        self.owner.flush_callbacks()
        self.assertEqual(self.panel.window.position, (200,36))

    def test_invalid_geometry_is_rejected_and_finalization_cancels_pending_work(self):
        self.panel.open()
        self.panel.model.onLayoutReady.notify({"clientWidth":True,"clientHeight":1080,"width":820,"height":740,"viewMode":"widget"})
        self.assertEqual(self.owner.callbacks, {})
        self.panel.model.onLayoutReady.notify({"clientWidth":1920,"clientHeight":1080,"width":820,"height":740,"viewMode":"widget"})
        self.assertTrue(self.owner.callbacks)
        self.panel.window.destroy()
        self.assertEqual(self.owner.callbacks, {})

    def test_view_mode_persists_and_invalid_commands_keep_the_previous_mode(self):
        self.panel.open()
        model = self.panel.model
        initial = json.loads(model.values[0])
        model.onSetViewMode.notify({"mode": "details"})
        expanded = json.loads(model.values[0])
        self.assertEqual(self.owner.view_modes, ["details"])
        self.assertEqual(self.owner.config["panel_view_mode"], "details")
        self.assertEqual(expanded["view_mode"], "details")
        self.assertGreater(expanded["revision"], initial["revision"])
        for args in (None, {}, {"mode": "fullscreen"}, {"mode": True}, {"mode": 1}):
            model.onSetViewMode.notify(args)
            self.assertEqual(json.loads(model.values[0])["view_mode"], "details")
            self.assertEqual(self.owner.view_modes, ["details"])
            self.assertIsNotNone(self.owner.panel_error)
        self.panel.close_window()
        self.panel.open()
        self.assertEqual(json.loads(self.panel.model.values[0])["view_mode"], "details")
        self.panel.model.onSetViewMode.notify({"mode": "widget"})
        self.assertEqual(self.owner.view_modes, ["details", "widget"])
        self.assertIsNone(self.owner.panel_error)

    def test_failed_view_mode_save_keeps_current_mode_and_native_geometry(self):
        self.panel.open()
        model = self.panel.model
        model.onLayoutReady.notify({"clientWidth": 1920, "clientHeight": 1080,
            "width": 620, "height": 180, "viewMode": "widget"})
        self.owner.flush_callbacks()
        position = self.panel.window.position
        with patch.object(self.owner, "save_panel_view_mode", side_effect=OSError("synthetic failure")), \
                patch("capture.panel.traceback.print_exc"), patch("builtins.print"):
            model.onSetViewMode.notify({"mode": "details"})
        self.assertEqual(json.loads(model.values[0])["view_mode"], "widget")
        self.assertEqual(self.panel._geometry, [1920, 1080, 620, 180])
        self.assertEqual(self.panel.window.position, position)
        self.assertIsNotNone(self.owner.panel_error)

    def test_default_widget_ignores_legacy_detail_position_and_invalid_saved_mode(self):
        self.owner.config["panel_position"] = {"x": 1200, "y": 500}
        self.owner.config["panel_view_mode"] = "corrupt"
        self.panel.open()
        self.assertEqual(json.loads(self.panel.model.values[0])["view_mode"], "widget")
        self.panel.model.onLayoutReady.notify({"clientWidth": 1920, "clientHeight": 1080,
            "width": 620, "height": 180, "viewMode": "widget"})
        self.owner.flush_callbacks()
        self.assertEqual(self.panel.window.position, (650, 96))

    def test_switching_modes_restores_separate_positions_without_recentering(self):
        self.panel.open()
        model = self.panel.model
        model.onLayoutReady.notify({"clientWidth": 1920, "clientHeight": 1080,
            "width": 620, "height": 180, "viewMode": "widget"})
        self.owner.flush_callbacks()
        self.panel.window.move(1200, 800)
        self.owner.flush_callbacks()
        model.onSetViewMode.notify({"mode": "details"})
        model.onLayoutReady.notify({"clientWidth": 1920, "clientHeight": 1080,
            "width": 1040, "height": 980, "viewMode": "details"})
        self.owner.flush_callbacks()
        self.assertEqual(self.panel.window.position, (880, 100))
        self.panel.window.move(300, 50)
        self.owner.flush_callbacks()
        model.onSetViewMode.notify({"mode": "widget"})
        model.onLayoutReady.notify({"clientWidth": 1920, "clientHeight": 1080,
            "width": 620, "height": 180, "viewMode": "widget"})
        self.owner.flush_callbacks()
        self.assertEqual(self.panel.window.position, (1200, 800))
        self.assertEqual(self.owner.config["panel_positions"]["details"], {"x": 300, "y": 50})
        self.assertEqual(self.owner.config["panel_positions"]["widget"], {"x": 1200, "y": 800})
        model.onLayoutReady.notify({"clientWidth": 1024, "clientHeight": 768,
            "width": 620, "height": 180, "viewMode": "widget"})
        self.owner.flush_callbacks()
        self.assertEqual(self.panel.window.position, (404, 588))
        model.onSetViewMode.notify({"mode": "details"})
        model.onLayoutReady.notify({"clientWidth": 1024, "clientHeight": 768,
            "width": 976, "height": 720, "viewMode": "details"})
        self.owner.flush_callbacks()
        self.assertEqual(self.panel.window.position, (48, 48))

    def test_stale_or_missing_mode_geometry_cannot_move_the_new_mode(self):
        self.panel.open()
        model = self.panel.model
        widget_layout = {"clientWidth": 1920, "clientHeight": 1080,
            "width": 620, "height": 180, "viewMode": "widget"}
        model.onLayoutReady.notify(widget_layout)
        model.onSetViewMode.notify({"mode": "details"})
        self.owner.flush_callbacks()
        self.assertIsNone(self.panel._geometry)
        for wrong_mode in ("widget", "corrupt", True, None):
            stale = dict(widget_layout, viewMode=wrong_mode)
            model.onLayoutReady.notify(stale)
            self.assertIsNone(self.panel._geometry)
        details = dict(widget_layout, width=1040, height=980, viewMode="details")
        model.onLayoutReady.notify(details)
        self.owner.flush_callbacks()
        geometry = list(self.panel._geometry)
        position = self.panel.window.position
        model.onLayoutReady.notify(widget_layout)
        self.owner.flush_callbacks()
        self.assertEqual(self.panel._geometry, geometry)
        self.assertEqual(self.panel.window.position, position)
        self.panel.window.native_resize(1040, 980)
        payload = json.loads(model.values[0])
        self.assertEqual(payload["view_mode"], "details")
        self.assertEqual(payload["window"], {"ready": True, "width": 1040, "height": 980})

    def test_mode_switch_reports_native_fallback_size_without_reloading_or_taking_focus(self):
        self.panel.open()
        model, window = self.panel.model, self.panel.window
        model.onSetViewMode.notify({"mode": "details"})
        model.onLayoutReady.notify({"clientWidth": 1920, "clientHeight": 1080,
            "width": 1040, "height": 980, "viewMode": "details",
            "nativeWidth": 1040, "nativeHeight": 980})
        self.owner.flush_callbacks()
        self.panel.refresh(force=True)
        payload = json.loads(model.values[0])
        self.assertEqual(payload["view_mode"], "details")
        self.assertEqual(payload["window"], {"ready": True, "width": 256, "height": 256})
        window.native_resize(1040, 980)
        self.assertEqual(json.loads(model.values[0])["window"]["width"], 1040)
        # A late C++ fallback must remain visible to the frontend retry logic.
        window.native_resize(256, 256)
        payload = json.loads(model.values[0])
        self.assertEqual(payload["view_mode"], "details")
        self.assertEqual(payload["window"], {"ready": True, "width": 256, "height": 256})
        model.onSetViewMode.notify({"mode": "widget"})
        window.native_resize(620, 180)
        self.assertEqual(json.loads(model.values[0])["view_mode"], "widget")
        self.assertEqual(json.loads(model.values[0])["window"], {
            "ready": True, "width": 620, "height": 180})
        self.assertIs(self.panel.window, window)
        self.assertEqual(window.loaded, 1)
        self.assertEqual(window.flags, 1)
        self.assertEqual(window.focus_requests, [False])

    def test_garage_ensure_opens_once_without_raising_existing_window_and_restores_plus(self):
        self.owner.config["panel_view_mode"] = "details"
        self.panel.ensure_visible()
        first = self.panel.window
        self.assertEqual(json.loads(self.panel.model.values[0])["view_mode"], "widget")
        for _ in range(3):
            self.panel.ensure_visible()
        self.assertEqual(first.focus_requests, [False])
        self.assertEqual(len(self.harness.windows), 1)
        self.panel.model.onClose.notify()
        self.assertEqual(self.owner.config["panel_view_mode"], "minimized")
        self.panel.close_window()
        self.panel.ensure_visible()
        self.assertIsNot(self.panel.window, first)
        self.assertEqual(json.loads(self.panel.model.values[0])["view_mode"], "minimized")
        self.assertEqual(self.panel.window.focus_requests, [False])

    def test_stale_detached_proxy_recovers_without_native_finalization(self):
        self.owner.config["panel_view_mode"] = "minimized"
        self.panel.ensure_visible()
        first = self.panel.window
        layout = {"clientWidth": 1920, "clientHeight": 1080,
                  "width": 64, "height": 56, "viewMode": "minimized"}
        self.panel.model.onLayoutReady.notify(layout)
        self.owner.flush_callbacks()
        first.move(1500, 700)
        self.panel.model.onLayoutReady.notify(layout)
        self.assertTrue(self.owner.callbacks)
        # The native parent vanished without calling LedgerView._finalize.
        first.proxy = None
        self.panel.ensure_visible()
        self.assertIsNot(self.panel.window, first)
        self.assertFalse(first.content.finalized)
        self.assertEqual(first.onPositionChanged.handlers, [])
        self.assertEqual(first.onSizeChanged.handlers, [])
        self.assertEqual(self.owner.callbacks, {})
        self.assertEqual(json.loads(self.panel.model.values[0])["view_mode"], "minimized")
        self.assertEqual(self.panel.window.focus_requests, [False])

    def test_invalid_native_object_is_replaced_and_its_handlers_are_released(self):
        self.panel.ensure_visible()
        first = self.panel.window

        def unavailable_hidden_state():
            raise RuntimeError("native object is no longer valid")

        first.isHidden = unavailable_hidden_state
        self.panel.ensure_visible(restore=True)
        self.assertIsNot(self.panel.window, first)
        self.assertEqual(first.destroyed, 1)
        self.assertEqual(first.onPositionChanged.handlers, [])
        self.assertEqual(first.onSizeChanged.handlers, [])
        self.assertEqual(self.panel.window.focus_requests, [False])

    def test_hidden_window_restores_without_focus_and_visible_ticks_do_not_raise_it(self):
        self.panel.ensure_visible()
        first = self.panel.window
        first.isVisible = False
        self.panel.ensure_visible(restore=True)
        self.assertIs(self.panel.window, first)
        self.assertFalse(first.isHidden())
        self.assertEqual(first.focus_requests, [False, False])
        for _ in range(3):
            self.panel.ensure_visible()
            self.panel.ensure_visible(restore=True)
        self.assertEqual(first.focus_requests, [False, False])
        first.isVisible = False
        self.panel.ensure_visible()
        self.assertEqual(first.focus_requests, [False, False, False])

    def test_unknown_visibility_only_forces_restore_on_explicit_garage_entry(self):
        self.panel.ensure_visible()
        first = self.panel.window
        first.isHidden = None
        del first.isVisible
        self.panel.ensure_visible()
        self.panel.ensure_visible()
        self.assertEqual(first.focus_requests, [False])
        self.panel.ensure_visible(restore=True)
        self.assertEqual(first.focus_requests, [False, False])
        self.panel.ensure_visible()
        self.assertEqual(first.focus_requests, [False, False])

    def test_deferred_native_ready_cannot_show_a_replaced_or_closed_window(self):
        native_window = self.harness.modules["gui.impl.pub"].WindowImpl

        def deferred_load(window):
            window.loaded += 1
            window.content._onLoading()

        with patch.object(native_window, "load", deferred_load):
            self.panel.ensure_visible()
            first = self.panel.window
            self.panel.ensure_visible(restore=True)
            self.assertIs(self.panel.window, first)
            self.assertEqual(first.focus_requests, [])
            first.proxy = None
            self.panel.ensure_visible()
            second = self.panel.window
            first.isReady = True
            first._onReady()
            self.assertEqual(first.focus_requests, [])
            self.assertEqual(second.focus_requests, [])
            second.isReady = True
            second._onReady()
            self.assertEqual(second.focus_requests, [False])
            self.panel.close_window()
            second._onReady()
            self.assertEqual(second.focus_requests, [False])

    def test_other_lobby_page_cannot_open_restore_or_finish_a_deferred_window(self):
        self.owner.garage_visible = False
        self.panel.open()
        self.panel.ensure_visible(restore=True)
        self.assertEqual(self.harness.windows, [])
        self.owner.garage_visible = True
        native_window = self.harness.modules["gui.impl.pub"].WindowImpl

        def deferred_load(window):
            window.loaded += 1
            window.content._onLoading()

        with patch.object(native_window, "load", deferred_load):
            self.panel.open()
            window = self.panel.window
            self.owner.garage_visible = False
            window.isReady = True
            window._onReady()
            self.panel.ensure_visible(restore=True)
            self.assertEqual(window.focus_requests, [])
            self.owner.garage_visible = True
            self.panel.ensure_visible(restore=True)
            self.assertEqual(window.focus_requests, [False])

    def test_ensure_does_not_restore_or_recreate_while_stopped_or_in_replay(self):
        self.panel.ensure_visible()
        first = self.panel.window
        first.isVisible = False
        self.owner._alive = False
        self.panel.ensure_visible(restore=True)
        self.owner._alive = True
        self.owner.playing_replay = True
        self.panel.ensure_visible(restore=True)
        self.assertIs(self.panel.window, first)
        self.assertEqual(first.focus_requests, [False])
        self.panel.close_window()
        self.panel.ensure_visible(restore=True)
        self.assertIsNone(self.panel.window)

    def test_automatic_open_retries_a_missing_parent_without_notification_spam(self):
        self.harness.layout_id = -1
        self.panel.ensure_visible()
        self.panel.ensure_visible()
        self.assertIsNone(self.panel.window)
        self.assertEqual(self.owner.notices, [])
        self.harness.layout_id = 1234
        self.panel.ensure_visible()
        self.assertIsNotNone(self.panel.window)

    def test_minimized_launcher_is_bounded_and_does_not_accept_stale_widget_geometry(self):
        self.panel.open()
        model, window = self.panel.model, self.panel.window
        widget = {"clientWidth": 1920, "clientHeight": 1080,
                  "width": 620, "height": 180, "viewMode": "widget"}
        model.onLayoutReady.notify(widget)
        self.owner.flush_callbacks()
        original_position = window.position
        model.onSetViewMode.notify({"mode": "minimized"})
        model.onLayoutReady.notify(widget)
        self.assertIsNone(self.panel._geometry)
        compact = dict(widget, width=64, height=56, viewMode="minimized")
        model.onLayoutReady.notify(compact)
        self.owner.flush_callbacks()
        self.assertEqual(window.position, original_position)
        # Reports remain honest until the real native surface changes.
        self.assertEqual(json.loads(model.values[0])["window"]["width"], 256)
        window.native_resize(64, 56)
        self.assertEqual(json.loads(model.values[0])["window"], {
            "ready": True, "width": 64, "height": 56})
        window.move(1990, 1200)
        model.onLayoutReady.notify(compact)
        self.owner.flush_callbacks()
        self.assertEqual(window.position, (1856, 1024))
        model.onSetViewMode.notify({"mode": "widget"})
        model.onLayoutReady.notify(widget)
        self.owner.flush_callbacks()
        self.assertEqual(window.position, original_position)
        self.assertIs(self.panel.window, window)
        self.assertEqual(window.destroyed, 0)


if __name__ == "__main__":
    unittest.main()
