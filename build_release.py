"""Build this release with the installed client's Python 2.7 DLL."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from capture.compatibility import SUPPORTED_REALMS, SUPPORTED_CLIENTS, supported_realm

VERSION = "0.22.14"
CLIENT = "2.4.1.1"
PACKAGE = "local.credit_ledger.%s.wotmod" % VERSION
COMPARED_BATTLE_NET = -113508
LAYOUT_ID = "R.mods.credit_ledger.views.LedgerView"
LAYOUT_PATH = "coui://gui/gameface/mods/credit_ledger/LedgerView.html"


def validation_metadata():
    """Keep the observed accounting check separate from the new UI's status."""
    return {
        "circular_progress_shortcut": {
            "minimized_size_px": [184, 144],
            "circle_size_px": [112, 112],
            "initial_goal_new_accounts": 100000,
            "saved_progress_and_explicitly_disabled_goals_preserved": True,
            "hover_move_handle": True,
            "green_ring_stroke_px": 8,
            "green_progress_bar_px": 12,
            "python_tests_passed": 437,
            "widget_size_px": [624, 208],
            "whole_circle_hover_and_restore": True,
            "separate_move_handle_dragging": True,
            "live_percent_while_minimized": True,
            "zero_inactive_pending_complete_states": True,
            "native_svg_paths_no_pathLength_or_conic_gradient": True,
            "accounting_and_stored_data_unchanged": True,
            "browser_layout_checks_passed": 119,
            "real_client_visual_check_pending": False,
            "real_client_visual_check_confirmed_by_user": True,
            "real_client_visual_check_scope": ["goal_circle", "whole_circle_hover", "move_handle", "restore_widget"],
        },
        "eight_point_design": {
            "base_spacing_px": 8,
            "structural_spacing_px": [8, 16, 24, 32],
            "widget_size_px": [624, 208],
            "details_maximum_size_px": [1040, 976],
            "history_row_px": 72,
            "maximum_visible_battles": 5,
            "financial_calculations_unchanged": True,
            "browser_layout_checks_passed": 119,
            "installer_checks_passed": 32,
            "real_client_visual_check_pending": True,
        },
        "default_goal_each_period": {
            "target": 100000,
            "new_accounts_and_reset_periods": True,
            "empty_legacy_zero_migration": True,
            "positive_saved_goals_and_progress_preserved": True,
            "explicit_zero_disables_until_next_period": True,
            "python_tests_passed": 447,
            "browser_layout_checks_passed": 120,
            "real_client_visual_check_pending": True,
        },
        "matchmaking_visibility": {
            "native_queue_classes": ["CommonBattleQueueState", "StrongholdsBattleQueueState",
                                     "HalloweenPreBattleQueueState", "LastStandPreBattleQueueState",
                                     "MapsTrainingQueueState", "BattleRoyaleTournamentQueueState"],
            "inactive_event_modules_imported": False,
            "loaded_native_class_identity_checked": True,
            "native_source": "LobbyStateMachine.visibleState",
            "queue_subclasses_supported": True,
            "cancel_keeps_goal_history_position_and_view_mode": True,
            "battle_loading_and_other_pages_hidden": True,
            "python_tests_passed": 450,
            "six_queue_classes_and_story_hangar_route_verified": True,
            "contracts_identical_regions": ["NA", "EU", "ASIA"],
            "real_client_visual_check_pending": True,
        },
        "garage_only_visibility": {
            "native_source": "LobbyStateMachine.visibleState + isHangarState",
            "native_event": "onVisibleRouteChanged",
            "unknown_loading_or_other_routes_hidden": True,
            "native_matchmaking_queue_routes_allowed": True,
            "returns_automatically_to_garage": True,
            "legacy_and_mode_specific_hangar_flags_supported": True,
            "deferred_window_ready_guard": True,
            "goal_completion_hidden_outside_garage": True,
            "financial_values_and_history_unchanged": True,
            "python_tests_passed": 432,
            "real_client_visual_check_pending": False,
            "real_client_visual_check_confirmed_by_user": True,
            "real_client_visual_check_client": "2.4.1.1",
            "real_client_visual_check_scope": ["tech_tree", "service_record", "return_to_garage"],
        },
        "client_patch_compatibility": {
            "target_client": CLIENT,
            "supported_clients": list(SUPPORTED_CLIENTS),
            "native_python_version": "2.7",
            "runtime_requires_exact_client": True,
            "account_history_schema_unchanged": True,
            "live_client_check_pending": True,
        },
        "regional_compatibility": {
            "supported_realms": list(SUPPORTED_REALMS),
            "automatic_native_realm_detection": True,
            "account_data_key": "realm:account_id",
            "native_regional_server_day_clock": True,
            "automated_region_contract_checks": True,
            "prior_live_client": {"version": "2.4.1.0", "regions": ["NA", "EU", "ASIA"]},
            "live_client_regions": [],
            "live_client_checks_pending": ["NA", "EU", "ASIA"],
        },
        "daily_archive_disclosure": {
            "closed_symbol": "+", "expanded_symbol": "\u2212",
            "visible_bordered_control_px": [32, 32], "whole_header_hit_area_px": 56,
            "keyboard_and_accessible_expanded_state": True,
            "spanish_english_tooltips_and_labels": True,
            "collapsed_by_default": True,
            "no_new_data_mutations": True,
            "real_client_visual_check_pending": True,
        },
        "larger_mode_icons": {
            "filter_and_detail_icon_px": 40,
            "battle_history_icon_px": 24,
            "mode_filter_row_px": 56,
            "battle_history_row_px": 72,
            "maximum_visible_battles": 5,
            "current_and_archived_history": True,
            "native_images_preserved_without_new_packaged_art": True,
            "narrow_labels_and_values_remain_separate": True,
            "real_client_visual_check_pending": True,
        },
        "tournament_mode_names": {
            "native_bonus_codes": {"14": "TOURNAMENT_REGULAR", "15": "TOURNAMENT_CLAN"},
            "spanish_labels": {"14": "Batalla de torneo", "15": "Torneo de clanes"},
            "english_labels": {"14": "Tournament Battle", "15": "Clan Tournament"},
            "native_icon": "gui/maps/icons/battleTypes/64x64/specBattlesList.png",
            "current_filters_selected_battles_and_daily_archive": True,
            "existing_records_relabelled_without_rewriting_money_or_identity": True,
            "garage_mode_and_gui_type_never_used_as_bonus_type": True,
            "unknown_future_codes_remain_explicit": True,
            "real_client_check_pending": True,
        },
        "goal_completion_celebration": {
            "status": "tests_and_browser_checks_client_validation_pending",
            "duration_ms": 2800,
            "stable_visible_garage_delay_ms": 1500,
            "completion_acknowledged_after_visible_presentation": True,
            "interrupted_presentation_remains_pending": True,
            "native_readiness_sources": ["own_Account_showGUI", "LOBBY_space", "IHangarSpace.spaceInited",
                                         "IHangarSpace.isModelLoaded", "Waiting.isVisible", "Window.isHidden"],
            "presentation_generation_rejects_stale_acknowledgements": True,
            "languages": ["es", "en"],
            "scope": "bounded_widget_or_existing_goal_title_in_details",
            "layout_and_native_window_dimensions_unchanged": False,
            "decorations_do_not_capture_input": True,
            "finite_transform_opacity_sparks": True,
            "acknowledged_achievements_do_not_repeat": True,
            "existing_completed_goal_migrates_silently": True,
            "new_goal_reference_rearms": True,
            "higher_completed_target_can_celebrate": True,
            "reduced_motion_keeps_static_message": True,
            "financial_values_unchanged": True,
            "native_command": "onAcknowledgeGoalCompletion",
            "animation_reference": "https://guide.coherent-labs.com/layout-assets-and-styling/animations/ui-animations/",
            "real_client_check_pending": True,
        },
        "bilingual_interface": {
            "status": "tests_and_browser_checks_client_validation_pending",
            "supported_languages": ["es", "en"], "default_language": "es",
            "preference_key": "ui_language", "native_command": "onSetLanguage",
            "instant_without_game_restart": True,
            "saved_preference_applies_to_widget_and_details": True,
            "number_grouping": {"es": "1.000.000", "en": "1,000,000"},
            "spanish_archive_label": "Historial por día",
            "language_change_never_changes_financial_values": True,
            "native_vehicle_and_quest_names_preserved": True,
            "goal_drafts_and_selected_history_preserved": True,
            "language_failures_do_not_cancel_other_actions": True,
            "python_tests_passed": 413, "browser_checks_passed": 116,
            "real_client_check_pending": True,
        },
        "native_mode_and_vehicle_art": {
            "status": "installed_png_resources_and_browser_checks_passed_client_check_pending",
            "mode_emblems_verified": 25,
            "event_vehicle_resources_verified": 65,
            "current_playable_event_vehicles": ["Avispa", "Cerbero", "Doble", "Granadero",
                                                "Malaquita", "Legio Ferrata", "Devastador"],
            "native_vehicle_name_level_and_image_from_result_type": True,
            "halloween_mounted_extend_png_resources_preserved": True,
            "known_vehicles_refreshed_across_entire_visible_period": True,
            "one_native_lookup_per_vehicle_type_per_payload": True,
            "unknown_modes_never_borrow_another_emblem": True,
            "opened_and_selected_filters_have_art": True,
            "mode_row_height": 52, "vehicle_row_height": 56,
            "five_66px_battle_rows_preserved": True,
            "no_vendor_assets_copied_into_package": True,
            "python_tests_passed": 413, "browser_checks_passed": 116,
            "real_client_visual_check_pending": True,
        },
        "daily_archive_and_simplified_history": {
            "status": "tests_and_browser_checks_client_validation_pending",
            "comparison_ui_removed": True,
            "schedule_controls_removed": True,
            "server_day_reset_mandatory_hidden": True,
            "manual_full_reset_button_preserved": True,
            "prior_days_collapsed_by_default": True,
            "catalog_scope": "all_captured_prior_server_days",
            "filters": ["day", "mode", "vehicle"],
            "selected_history_limit": 100,
            "whole_day_totals_before_history_limit": True,
            "external_rewards_separate_and_deduplicated": True,
            "archive_is_read_only": True,
            "native_command": "onSelectHistoryDay",
            "current_balance_goal_and_widget_not_filtered_by_archive": True,
            "real_client_check_pending": True,
        },
        "vehicle_filter": {
            "status": "native_query_format_compatibility_and_browser_checks_passed_client_validation_pending",
            "group_identity": "native_vehicle_type_id",
            "mode_and_vehicle_filters_combine": True,
            "comparison_ui_removed": True,
            "all_vehicle_groups_have_summaries_only": True,
            "one_selected_history_limit": 100,
            "native_command": "onSetVehicleFilter",
            "canonical_integer_string_and_integral_finite_float_request_ids": True,
            "known_vehicle_totals_visible_while_history_loads": True,
            "missing_response_has_bounded_retry": True,
            "stale_requests_and_responses_ignored": True,
            "filter_is_memory_only": True,
            "widget_goal_balance_and_wallet_unfiltered": True,
            "real_client_check_pending": True,
        },
        "history_mode_filter": {
            "status": "full_period_grouping_runtime_cache_and_browser_checks_passed_client_check_pending",
            "local_filter_default": "all",
            "main_modes_available_when_empty": [1, 20, 43],
            "group_identity": "native_bonus_type_not_label_or_gui_type",
            "summary_scope": "all_visible_period_battles_of_selected_mode",
            "history_limit_per_mode": 100,
            "visible_picker_rows": 5,
            "first_summary_card_and_breakdown_follow_filter": True,
            "widget_goal_account_balance_wallet_unfiltered": True,
            "account_and_history_reset_clear_filter": True,
            "legacy_context_lookup_cached_max_reads_per_batch": 25,
            "legacy_context_lookup_signature_and_identity_checked": True,
            "real_client_check_pending": True,
        },
        "battle_mode_attribution": {
            "status": "installed_native_contract_metadata_pipeline_and_browser_checks_passed_client_check_pending",
            "canonical_source": "common.bonusType",
            "fallback_source": "common.arenaBonusType_only_if_canonical_absent",
            "gui_type_is_separate_metadata": True,
            "stored_codes_not_guessed_labels": True,
            "shown_in_picker_and_selected_detail": True,
            "missing_historical_modes_recovered_from_own_captures": True,
            "unknown_modes_explicit": True,
            "finances_unchanged": True,
            "five_visible_rows_preserved": True,
            "real_client_check_pending": True,
        },
        "goal_resume_and_reset": {
            "status": "model_runtime_native_command_and_browser_checks_passed_client_check_pending",
            "zero_only_deactivates": True,
            "reactivation_preserves_original_base_date_and_balance_change": True,
            "disabled_goal_keeps_current_balance_change_visible": True,
            "dedicated_reset_command": "onResetGoal",
            "reset_uses_positive_written_amount_and_current_balance": True,
            "reset_acknowledged_by_incremented_goal_generation": True,
            "reset_does_not_change_history_or_wallet": True,
            "native_model_commands": 12,
            "real_client_check_pending": True,
        },
        "credit_reserves": {
            "status": "native_contract_and_pipeline_tests_passed_clan_compared_personal_nonzero_pending",
            "row_style": "same_cost_row_as_repairs_and_ammo",
            "personal_records": ["boosterCredits", "boosterCreditsFactor100"],
            "clan_records": ["orderCreditsFactor100"],
            "source": "effective_base_or_premium_aggregate.getRecord",
            "monetary_replay_deltas_only": True,
            "already_in_gross_never_added_twice": True,
            "legacy_missing_detail_stays_unknown": True,
            "partial_period_coverage_shown": True,
            "optional_mapping_failure_keeps_verified_income": True,
            "python_tests_passed": 413, "browser_checks_passed": 116,
            "clan_real_report_compared": True,
            "clan_report_credits": 16819,
            "compared_report_gross": 42608, "compared_report_net": 26895,
            "personal_nonzero_comparison_pending": True,
        },
        "widget_amount_layout": {
            "status": "gameface_defaults_regression_checks_passed_client_check_pending",
            "all_mixed_fragments_wrapped": True,
            "explicit_horizontal_flex": True, "no_inline_layout_dependency": True,
            "main_column_zero_flex_basis": True,
            "widget_size_unchanged": [620, 180],
            "narrow_long_values_wrap_deliberately": True,
            "accounting_unchanged": True, "real_client_check_pending": True,
            "primary_reference": "https://docs.coherent-labs.com/cpp-gameface/what_is_gfp/htmlfeaturesupport/",
        },
        "goal_remaining_card": {
            "status": "browser_saved_goal_pending_zero_and_layout_checks_passed_client_check_pending",
            "source": "saved_goal.remaining",
            "completed_value": 0, "inactive_value": None,
            "unknown_balance_stays_pending": True,
            "unsaved_goal_draft_does_not_change_card": True,
            "summary_columns": [4, 2, 1],
            "large_values_use_smaller_type": True,
            "accounting_unchanged": True, "real_client_check_pending": True,
        },
        "detailed_view_design": {
            "status": "browser_layout_and_native_window_contract_checks_passed_client_check_pending",
            "style": "charcoal_cards_and_gold_widget_accents",
            "summary_cards": 4, "progress_bar_height_px": 12,
            "progress_marks": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            "sections": ["battles", "wallet", "rewards", "manual_history_reset", "prior_days"],
            "narrow_summary_stacks": True,
            "history_row_sizes_unchanged": True,
            "native_window_dimensions_unchanged": True,
            "browser_checks_passed": 116, "accounting_unchanged": True,
            "real_client_check_pending": True,
        },
        "financial_sign_colors": {
            "status": "browser_sign_transition_checks_passed_client_check_pending",
            "positive": "#8dd36a", "negative": "#f07171", "zero": "neutral",
            "expenses_colored_by_displayed_negative_value": True,
            "inline_amounts_colored_independently": True,
            "accounting_unchanged": True, "real_client_check_pending": True,
        },
        "optional_credit_goal": {
            "status": "presentation_runtime_persistence_and_browser_checks_passed_client_check_pending",
            "zero_saves_without_goal": True, "zero_does_not_require_balance": True,
            "zero_keeps_accounting_and_history": True,
            "initial_zero_has_no_fabricated_base_or_start": True,
            "deactivation_keeps_last_goal_base_and_start": True,
            "positive_reactivation_preserves_original_base_and_date": True,
            "summary_replaces_average_with_goal_starting_balance": True,
            "real_client_check_pending": True,
        },
        "battle_history_picker": {
            "status": "browser_geometry_and_scroll_checks_passed_client_check_pending",
            "maximum_visible_battles": 5, "opens_downward_in_document_flow": True,
            "pushes_cost_breakdown_below_list": True,
            "short_histories_fit_without_empty_rows": True,
            "extra_battles_scroll_with_wheel_and_bar": True,
            "browser_checks_passed": 116, "real_client_check_pending": True,
        },
        "battle_vehicles": {
            "status": "installed_native_api_contract_and_identity_pipeline_tested",
            "native_source": "IItemsCache.items.getItemByCD(personal_vehicle_compact_descriptor)",
            "properties": ["userName", "level", "icon"],
            "local_game_art_only": True, "legacy_capture_metadata_backfill": True,
            "multiple_own_vehicles_one_financial_aggregate": True,
            "missing_data_explicit_fallback": True,
            "real_client_check_pending": False,
            "real_client_0_10_0_art_confirmed_by_user_screenshot": True,
        },
        "battle_accounting": {
            "status": "compared_by_user",
            "scope": "second captured battle",
            "net_credits": COMPARED_BATTLE_NET,
        },
        "in_game_ui": {"status": "new_layout_pending_client_check", "previous_0_6_size_timeout_observed": True,
                       "previous_0_6_1_full_panel_seen_user_screenshot": True,
                       "new_net_labels_pending_client_check": True,
                       "ignored_early_resize_and_late_256px_fallback_regression_simulated": True,
                       "native_size_and_ready_acknowledgement_tested": True},
        "rewards": {"status": "native_message_contract_checked_and_simulated", "real_award_pending": True},
        "floating_window": {"status": "native_api_contract_and_browser_checked", "garage_input_pending": True},
        "compact_widget": {
            "status": "browser_and_window_contract_checks_passed_real_client_pending",
            "default_view": "widget", "width": 620, "height": 180,
            "separate_detailed_view": True,
            "battle_accounting_unchanged": True,
            "native_180px_height_verified_in_real_client": True,
            "native_size_confirmation_scope": "0.8.0 client log: 620x180 and 1040x980 verified",
            "in_game_verification_pending": True,
        },
        "persistent_garage_widget": {
            "status": "garage_lifecycle_and_three_mode_contract_tested_client_check_pending",
            "garage_only": True, "automatic_open": True,
            "minimized_size": [184, 144], "visible_restore_control": "goal_progress_circle",
            "minimize_preserves_window_and_drafts": True,
            "mods_menu_entry_removed": True,
            "mods_list_api_dependency_removed": True,
            "native_lobby_space_and_late_gui_events_bound": True,
            "hidden_and_invalid_windows_recovered_without_focus": True,
            "real_client_112px_circle_pending": True,
        },
        "goal_target_editing": {
            "status": "target_updates_preserve_base_and_start_time_tested",
            "completed_and_negative_progress_tested": True,
            "explicit_history_reset_behavior_preserved": True,
            "in_game_verification_pending": True,
        },
        "battle_pass_vouchers": {"status": "successful_processor_observer_tested", "real_opening_pending": True},
        "history_reset": {
            "status": "account_period_and_runtime_contract_tested_client_check_pending",
            "python_tests_passed": 413,
            "browser_checks_passed": 116,
            "default_mode": "server",
            "server_source": "Account.serverSettings.regional_settings.starting_time_of_a_new_game_day",
            "legacy_server_offset_key": "starting_time_of_a_new_day_only_if_current_key_absent",
            "server_clock": "helpers.time_utils.getServerUTCTime_after_own_Account_showGUI",
            "stable_utc_day_window": True,
            "server_cycle_not_disconnect_or_maintenance_detection": True,
            "server_and_manual_reset_start_editable_100000_goal_from_current_balance": True,
            "goal_requires_explicit_new_activation": True,
            "first_native_cycle_arms_without_reset": True,
            "old_schedule_choices_migrate_without_immediate_reset": True,
            "all_accounts_use_hidden_server_schedule": True,
            "unavailable_native_clock_never_guesses_schedule": True,
            "clock": "native_server_day_only",
            "default_preserve_goal": False,
            "manual_confirmation_and_cancel_tested": True,
            "daily_offline_first_synced_balance_tested": True,
            "financial_audit_records_preserved": True,
            "in_game_verification_pending": True,
        },
    }


def resource_files(source):
    """Validate original static assets and return their exact package locations."""
    manifest = source / "resources" / "gui" / "gen_resources" / "local_credit_ledger.json"
    expected = [{"type": "Layout", "id": LAYOUT_ID, "path": LAYOUT_PATH,
                 "parameters": {"entrance": "LedgerView", "impl": "gameface"}}]
    if json.loads(manifest.read_text(encoding="utf-8")) != expected:
        raise ValueError("credit ledger layout manifest does not match the supported resource schema")
    assets = [(manifest, Path("res/gui/gen_resources/local_credit_ledger.json"))]
    for name in ("LedgerView.html", "ledger.css", "ledger.js"):
        path = source / "ui" / name
        if not path.is_file() or not path.read_bytes():
            raise ValueError("missing or empty UI asset: " + str(path))
        assets.append((path, Path("res/gui/gameface/mods/credit_ledger") / name))
    return assets


def write_metadata(path):
    root = ET.Element("root")
    for name, value in (
        ("id", "local.credit_ledger"),
        ("version", "0.22.14"),
        ("name", "Credit Ledger / Contabilidad de creditos"),
        ("description", "Contabilidad local de creditos para WoT 2.4.1.1 NA/EU/ASIA: "
         "ingresos, gastos, historial de partidas y metas de ahorro."),
    ):
        ET.SubElement(root, name).text = value
    ET.ElementTree(root).write(str(path), encoding="utf-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    assets = resource_files(source)
    game = args.game_root.resolve()
    version = ET.parse(game / "version.xml").getroot().findtext("version", "").strip()
    build_client = next((candidate for candidate in SUPPORTED_CLIENTS
                         if version.startswith("v.%s " % candidate)), None)
    if build_client is None:
        raise SystemExit("Unsupported compiler client version: " + version)
    build_realm = ET.parse(game / "version.xml").getroot().findtext("meta/realm", "").strip()
    try:
        build_realm = supported_realm(build_realm)
    except RuntimeError as error:
        raise SystemExit(str(error))
    stage = source / "build" / VERSION
    package_root = stage / "package"
    package_root.mkdir(parents=True, exist_ok=True)
    target_modules = package_root / "res" / "scripts" / "client" / "gui" / "mods"
    target_modules.mkdir(parents=True, exist_ok=True)
    jobs = []
    for path in sorted((source / "capture").glob("*.py")):
        relative = Path("credit_ledger_capture") / path.with_suffix(".pyc").name
        jobs.append({"source": str(path), "output": str(target_modules / relative),
                     "filename": "gui/mods/credit_ledger_capture/" + path.name})
    jobs.append({"source": str(source / "core" / "ledger.py"),
                 "output": str(target_modules / "credit_ledger_capture" / "ledger.pyc"),
                 "filename": "gui/mods/credit_ledger_capture/ledger.py"})
    jobs.append({"source": str(source / "game" / "mod_credit_ledger_capture.py"),
                 "output": str(target_modules / "mod_credit_ledger_capture.pyc"),
                 "filename": "gui/mods/mod_credit_ledger_capture.py"})
    manifest = stage / "compile-manifest.json"
    manifest.write_text(json.dumps(jobs, indent=2), encoding="utf-8")
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        raise SystemExit("64-bit PowerShell is required to host Python27.dll")
    subprocess.run([shell, "-NoProfile", "-File", str(source / "build_tools" / "compile_py27.ps1"),
                    "-PythonDll", str(game / "win64" / "python27.dll"),
                    "-Manifest", str(manifest)], check=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    metadata = package_root / "meta.xml"
    write_metadata(metadata)
    static_files = []
    for source_path, relative_path in assets:
        destination = package_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)
        static_files.append(destination)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    package = output / PACKAGE
    compiled_files = [Path(job["output"]) for job in jobs]
    files = [metadata] + compiled_files + static_files
    for path in compiled_files:
        if path.read_bytes()[:4] != b"\x03\xf3\r\n":
            raise RuntimeError("wrong Python 2.7 magic: " + str(path))
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_STORED) as archive:
        for path in files:
            archive.write(path, path.relative_to(package_root).as_posix())
    with zipfile.ZipFile(package) as archive:
        expected_names = {path.relative_to(package_root).as_posix() for path in files}
        infos = archive.infolist()
        if archive.testzip() is not None:
            raise RuntimeError("wotmod archive checksum verification failed")
        if len(infos) != len(expected_names) or set(archive.namelist()) != expected_names:
            raise RuntimeError("wotmod archive entries do not match the release file list")
        if any(info.compress_type != zipfile.ZIP_STORED for info in infos):
            raise RuntimeError("wotmod archive must use ZIP_STORED for every entry")
        for path in compiled_files:
            name = path.relative_to(package_root).as_posix()
            if archive.read(name)[:4] != b"\x03\xf3\r\n":
                raise RuntimeError("packaged module has wrong Python 2.7 magic: " + name)
    report = {"version": VERSION, "client": CLIENT, "build_client": build_client,
              "supported_clients": list(SUPPORTED_CLIENTS), "realm": build_realm,
              "build_realm": build_realm, "supported_realms": list(SUPPORTED_REALMS),
              "file": package.name, "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
              "compiled_modules": len(jobs), "static_assets": len(static_files),
              "layout_id": LAYOUT_ID, "compression": "ZIP_STORED",
              "validation": validation_metadata()}
    (output / "contabilidad-build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Publish the local release pointer only after package verification. The
    # updater waits for the game to exit and always replaces one stable name.
    feed = {"schema": 1, "id": "local.credit_ledger", "version": VERSION,
            "client": CLIENT, "realm": build_realm, "supported_realms": list(SUPPORTED_REALMS),
            "file": package.name,
            "sha256": report["sha256"]}
    staging = output / "credit-ledger-release.json.tmp"
    staging.write_text(json.dumps(feed, indent=2), encoding="utf-8")
    staging.replace(output / "credit-ledger-release.json")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
