# -*- coding: utf-8 -*-
"""Lazy native Gameface window. Financial collection works without this UI."""
import json
import math
import traceback


class LedgerPanel(object):
    def __init__(self, owner):
        self.owner = owner
        self.window = None
        self.model = None
        self.last_payload = None
        self.revision = 0
        self._placed = False
        self._mode = self._configured_view_mode()
        self._placed_mode = None
        self._positions = {}
        self._placement_anchor = None
        self._geometry = None
        self._geometry_mode = None
        self._placement_id = None
        self._position_save_id = None

    def ensure_visible(self, restore=False):
        if (not self.owner._alive or self.owner.replay.isPlaying() or
                not self.owner._garage_view_visible()):
            return
        if self.window is not None:
            try:
                if self.window.proxy is None:
                    raise RuntimeError("credit ledger window is detached")
                if self.window.isReady:
                    # Reading the documented native size detects an invalid
                    # native object even when Python still holds its wrapper.
                    width, height = self.window.size
                    is_hidden = getattr(self.window, "isHidden", None)
                    hidden = is_hidden() if callable(is_hidden) else None
                    visible = not hidden if isinstance(hidden, bool) else getattr(
                        self.window, "isVisible", None)
                    # Window.isHidden() is the current native contract. Without
                    # that method or an optional boolean visibility property,
                    # only an explicit garage-entry event restores the window.
                    if visible is False or (restore is True and visible is not True):
                        self.window.show(False)
                return
            except Exception:
                self._discard_stale_window()
        self.open(automatic=True)

    def _discard_stale_window(self):
        window = self.window
        # Native finalization is not guaranteed to arrive after its parent
        # disappears. Release only this panel's callbacks and event handlers.
        self._detach_window()
        if window is not None:
            try:
                window.destroy()
            except Exception:
                pass

    def open(self, automatic=False):
        if (not self.owner._alive or self.owner.replay.isPlaying() or
                not self.owner._garage_view_visible()):
            return
        if self.window is not None:
            self.ensure_visible(restore=not automatic)
            return
        try:
            self._mode = self._configured_view_mode()
            if automatic and self._mode == "details":
                self._mode = "widget"
            self.window = self._make_window()
            self.window.onPositionChanged += self._position_changed
            self.window.onSizeChanged += self._size_changed
            self.window.load()
        except Exception:
            self.close_window()
            if not automatic:
                print("[CreditLedger] panel could not be opened")
                traceback.print_exc()
                self.owner._notify(u"Contabilidad: no se pudo abrir el panel. Revisa game.log.")

    def _make_window(self):
        from frameworks.wulf import (ViewModel, ViewSettings, ViewFlags,
                                      WindowFlags, WindowLayer)
        from gui.impl.pub import ViewImpl, WindowImpl
        from gui.impl.gen import R
        from helpers import dependency
        from skeletons.gui.impl import IGuiLoader

        layout_id = R.mods.credit_ledger.views.LedgerView()
        if layout_id <= 0:
            raise RuntimeError("credit ledger Gameface layout is not registered")
        controller = self

        class LedgerModel(ViewModel):
            def __init__(self):
                super(LedgerModel, self).__init__(properties=1, commands=12)

            def _initialize(self):
                super(LedgerModel, self)._initialize()
                self._addStringProperty("payload", "{}")
                self.onSaveGoal = self._addCommand("onSaveGoal")
                self.onClose = self._addCommand("onClose")
                self.onRefresh = self._addCommand("onRefresh")
                self.onLayoutReady = self._addCommand("onLayoutReady")
                self.onSaveHistory = self._addCommand("onSaveHistory")
                self.onResetHistory = self._addCommand("onResetHistory")
                self.onSetViewMode = self._addCommand("onSetViewMode")
                self.onResetGoal = self._addCommand("onResetGoal")
                self.onSetVehicleFilter = self._addCommand("onSetVehicleFilter")
                self.onSelectHistoryDay = self._addCommand("onSelectHistoryDay")
                self.onSetLanguage = self._addCommand("onSetLanguage")
                self.onAcknowledgeGoalCompletion = self._addCommand("onAcknowledgeGoalCompletion")

            def setPayload(self, value):
                self._setString(0, value)

        class LedgerView(ViewImpl):
            def __init__(self):
                super(LedgerView, self).__init__(ViewSettings(
                    layout_id, flags=ViewFlags.VIEW, model=LedgerModel()))

            def _getEvents(self):
                model = self.getViewModel()
                return ((model.onSaveGoal, self._save),
                        (model.onClose, self._close),
                        (model.onRefresh, self._refresh),
                        (model.onLayoutReady, self._layout),
                        (model.onSaveHistory, self._save_history),
                        (model.onResetHistory, self._reset_history),
                        (model.onSetViewMode, self._set_view_mode),
                        (model.onResetGoal, self._reset_goal),
                        (model.onSetVehicleFilter, self._set_vehicle_filter),
                        (model.onSelectHistoryDay, self._select_history_day),
                        (model.onSetLanguage, self._set_language),
                        (model.onAcknowledgeGoalCompletion, self._acknowledge_goal_completion))

            def _onLoading(self, *args, **kwargs):
                super(LedgerView, self)._onLoading(*args, **kwargs)
                controller.model = self.getViewModel()
                controller.last_payload = None
                controller.refresh()

            def _save(self, args=None):
                controller.owner.save_goal(args)

            def _reset_goal(self, args=None):
                controller.owner.reset_goal(args)

            def _set_vehicle_filter(self, args=None):
                if controller.model is self.getViewModel():
                    controller.owner.set_vehicle_filter(args)

            def _select_history_day(self, args=None):
                if controller.model is self.getViewModel():
                    controller.owner.set_archive_selection(args)

            def _set_language(self, args=None):
                if controller.model is self.getViewModel():
                    controller.owner.set_language(args)

            def _acknowledge_goal_completion(self, args=None):
                if controller.model is self.getViewModel():
                    controller.owner.acknowledge_goal_completion(args)

            def _close(self, args=None):
                controller._set_view_mode({"mode": "minimized"})

            def _refresh(self, args=None):
                controller.owner.panel_error = None
                controller.refresh(force=True)

            def _layout(self, args=None):
                controller.layout_ready(args)

            def _save_history(self, args=None):
                controller.owner.save_history_settings(args)

            def _reset_history(self, args=None):
                controller.owner.reset_history(args)

            def _set_view_mode(self, args=None):
                controller._set_view_mode(args)

            def _finalize(self):
                if controller.model is self.getViewModel():
                    controller._detach_window()
                super(LedgerView, self)._finalize()

        class FloatingLedgerWindow(WindowImpl):
            def _onReady(self):
                if (controller.window is not self or not controller.owner._alive or
                        controller.owner.replay.isPlaying() or
                        not controller.owner._garage_view_visible()):
                    return
                # This window has neither modal nor fullscreen flags. Opening it
                # does not capture keyboard focus from the garage.
                self.show(False)
                if controller._geometry is not None:
                    controller._cancel("_placement_id")
                    controller._place()
                # Early JS resize requests can be discarded while Wulf is
                # calculating its initial size. Publish native readiness so the
                # frontend can apply and verify the bounds after that stage.
                controller.refresh(force=True)

        loader = dependency.instance(IGuiLoader)
        parent = loader.windowsManager.getMainWindow()
        if parent is None or parent.proxy is None:
            raise RuntimeError("garage window is not available")
        return FloatingLedgerWindow(WindowFlags.WINDOW,
                          content=LedgerView(), decorator=None,
                          layer=WindowLayer.WINDOW, parent=parent)

    def _cancel(self, attribute):
        callback_id = getattr(self, attribute)
        setattr(self, attribute, None)
        if callback_id is not None:
            try:
                self.owner.world.cancelCallback(callback_id)
            except Exception:
                pass

    def _configured_view_mode(self):
        mode = self.owner.config.get("panel_view_mode", "widget")
        return mode if mode in ("widget", "details", "minimized") else "widget"

    @staticmethod
    def _valid_position(position):
        if not isinstance(position, (tuple, list)) or len(position) != 2:
            return False
        return all(not isinstance(value, bool) and isinstance(value, (int, float)) and
                   not math.isnan(value) and not math.isinf(value) for value in position)

    def _set_view_mode(self, args):
        mode = args.get("mode") if isinstance(args, dict) else None
        if mode not in ("widget", "details", "minimized"):
            self.owner.panel_error = u"Selecciona el resumen o los detalles de contabilidad."
            self.refresh(force=True)
            return
        try:
            if mode != self._mode:
                self._cancel("_position_save_id")
                self._save_position()
                anchor = self.window.position if self.window is not None else None
                self.owner.save_panel_view_mode(mode)
                self._mode = self._configured_view_mode()
                self._cancel("_placement_id")
                self._geometry = None
                self._geometry_mode = None
                self._placed = False
                self._placed_mode = None
                self._placement_anchor = anchor if self._valid_position(anchor) else None
            self.owner.panel_error = None
        except Exception:
            self.owner.panel_error = u"No se pudo guardar la vista de contabilidad."
            print("[CreditLedger] panel view mode could not be saved")
            traceback.print_exc()
        self.refresh(force=True)

    def layout_ready(self, args):
        if not isinstance(args, dict) or self.window is None:
            return
        mode = args.get("viewMode")
        if mode not in ("widget", "details", "minimized") or mode != self._mode:
            return
        values = [args.get(key) for key in ("clientWidth", "clientHeight", "width", "height")]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
               math.isnan(v) or math.isinf(v) or v < 1 or v > 100000 for v in values):
            return
        self._geometry = [int(v) for v in values]
        self._geometry_mode = mode
        print("[CreditLedger] panel requested client=%sx%s content=%sx%s; mode=%s phase=%s native=%sx%s" %
              tuple(self._geometry + [mode, args.get("phase", "requested"),
                    args.get("nativeWidth", 0), args.get("nativeHeight", 0)]))
        self._cancel("_placement_id")
        self._placement_id = self.owner.world.callback(0.0, self._place)

    def _place(self):
        self._placement_id = None
        if (self.window is None or self._geometry is None or not self.window.isReady or
                self._geometry_mode != self._mode):
            return
        client_width, client_height, width, height = self._geometry
        max_x, max_y = max(0, client_width - width), max(0, client_height - height)
        position = self.window.position if self._placed and self._placed_mode == self._mode else None
        if not self._valid_position(position):
            position = self._positions.get(self._mode)
        if not self._valid_position(position):
            positions = self.owner.config.get("panel_positions", {})
            saved = positions.get(self._mode, {}) if isinstance(positions, dict) else {}
            position = (saved.get("x"), saved.get("y")) if isinstance(saved, dict) else None
        if not self._valid_position(position):
            position = self._placement_anchor
        if not self._valid_position(position) and self._mode == "details":
            saved = self.owner.config.get("panel_position", {})
            position = (saved.get("x"), saved.get("y")) if isinstance(saved, dict) else None
        if not self._valid_position(position):
            position = (max_x // 2, min(96, max_y) if self._mode != "details" else max_y // 2)
        x, y = position
        self._placed = True
        self._placed_mode = self._mode
        self._placement_anchor = None
        self.window.move(max(0, min(max_x, int(x))), max(0, min(max_y, int(y))))

    def _position_changed(self, *args):
        if not self._placed or self._placed_mode != self._mode:
            return
        self._cancel("_position_save_id")
        self._position_save_id = self.owner.world.callback(0.4, self._save_position)

    def _size_changed(self, *args):
        # window.size is the actual C++ clipping surface, not the CSS request.
        self.refresh(force=True)

    def _window_state(self):
        result = {"ready": False, "width": 0, "height": 0}
        if self.window is not None and self.window.proxy is not None:
            result["ready"] = bool(self.window.isReady)
            try:
                width, height = self.window.size
                if all(not math.isnan(v) and not math.isinf(v) and 0 <= v <= 100000
                       for v in (width, height)):
                    result.update(width=int(width), height=int(height))
            except Exception:
                pass
        return result

    def completion_surface_ready(self):
        """Use the actual native clipping surface and its visibility state."""
        if (self.window is None or self.window.proxy is None or not self.window.isReady or
                self._mode not in ("widget", "details") or self._geometry is None or
                self._geometry_mode != self._mode or not self._placed or
                self._placed_mode != self._mode):
            return False
        try:
            hidden = getattr(self.window, "isHidden", None)
            visible = hidden() is False if callable(hidden) else getattr(self.window, "isVisible", None)
            width, height = self.window.size
            return (visible is True and width == self._geometry[2] and
                    height == self._geometry[3] and width > 0 and height > 0)
        except Exception:
            return False

    def _save_position(self):
        self._position_save_id = None
        if (self.window is not None and self._placed and self._placed_mode == self._mode and
                self.window.proxy is not None):
            try:
                x, y = self.window.position
                if self._valid_position((x, y)):
                    self._positions[self._mode] = (x, y)
                    self.owner.save_panel_position(x, y, view_mode=self._mode)
            except Exception:
                print("[CreditLedger] window position could not be saved")
                traceback.print_exc()

    def refresh(self, force=False):
        if self.model is None:
            return
        try:
            if force:
                self.revision += 1
            data = dict(self.owner.panel_payload())
            data["revision"] = self.revision
            data["view_mode"] = self._mode
            data["window"] = self._window_state()
            payload = json.dumps(data, ensure_ascii=False,
                                 sort_keys=True, separators=(",", ":"))
            if payload != self.last_payload:
                with self.model.transaction() as model:
                    model.setPayload(payload)
                self.last_payload = payload
        except Exception:
            print("[CreditLedger] panel refresh unavailable")
            traceback.print_exc()

    def close_window(self):
        window = self.window
        self._cancel("_position_save_id")
        self._save_position()
        self._detach_window()
        if window is not None:
            try:
                window.destroy()
            except Exception:
                traceback.print_exc()

    def _detach_window(self):
        self._cancel("_placement_id")
        self._cancel("_position_save_id")
        if self.window is not None:
            try:
                self.window.onPositionChanged -= self._position_changed
            except Exception:
                pass
            try:
                self.window.onSizeChanged -= self._size_changed
            except Exception:
                pass
        self.window = None
        self.model = None
        self.last_payload = None
        self._placed = False
        self._placed_mode = None
        self._placement_anchor = None
        self._geometry = None
        self._geometry_mode = None

    def close(self):
        self.close_window()
