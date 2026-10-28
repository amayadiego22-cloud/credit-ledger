"""Client root detection and historical data across the 2.4.1.1 update."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from capture import runtime
from capture.native import derive_credits
from capture.normalizer import normalize_snapshot
from capture.snapshot import CLIENT_VERSION, make_snapshot
from test_native_finance import Reusable
from test_snapshot import fixture


class ClientPatchTests(unittest.TestCase):
    def game(self, root, version):
        root.mkdir(parents=True, exist_ok=True)
        (root / "mods").mkdir(exist_ok=True)
        (root / "win64").mkdir(exist_ok=True)
        (root / "version.xml").write_text(
            "<version.xml><version> v.%s #984 </version></version.xml>" % version,
            encoding="utf-8")
        return root

    def test_runtime_accepts_updated_game_from_root_and_win64(self):
        with tempfile.TemporaryDirectory() as directory:
            game = self.game(Path(directory) / "game with spaces", "2.4.1.1")
            for current in (game, game / "win64"):
                with self.subTest(current=str(current)):
                    with patch.object(runtime.os, "getcwd", return_value=str(current)):
                        with patch.object(runtime.sys, "executable", str(game / "win64/WorldOfTanks.exe")):
                            self.assertEqual(runtime._game_directory(), str(game.resolve()))

    def test_runtime_uses_actual_executable_root_when_working_directory_differs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = self.game(root / "new game", "2.4.1.1")
            old = self.game(root / "old game", "2.4.1.0")
            with patch.object(runtime.os, "getcwd", return_value=str(old)):
                with patch.object(runtime.sys, "executable", str(game / "win64/WorldOfTanks.exe")):
                    self.assertEqual(runtime._game_directory(), str(game.resolve()))

    def test_runtime_rejects_other_patch_versions_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            for version in ("2.4.0.2", "2.4.1.10", "2.4.2.0", "2.5.0.0"):
                game = self.game(Path(directory) / version, version)
                original = (game / "version.xml").read_bytes()
                with self.subTest(version=version):
                    with patch.object(runtime.os, "getcwd", return_value=str(game)):
                        with patch.object(runtime.sys, "executable", str(game / "win64/WorldOfTanks.exe")):
                            with self.assertRaisesRegex(RuntimeError, "2.4.1.1"):
                                runtime._game_directory()
                    self.assertEqual((game / "version.xml").read_bytes(), original)
                    self.assertEqual(list((game / "mods").iterdir()), [])

    def test_snapshot_marks_new_client_but_old_economy_remains_readable(self):
        self.assertEqual(CLIENT_VERSION, "2.4.1.1")
        raw = fixture()
        snapshot = make_snapshot(raw, "EU")
        snapshot["native_credits"] = derive_credits(raw, lambda _: Reusable())
        self.assertEqual(snapshot["client_version"], "2.4.1.1")
        old = copy.deepcopy(snapshot)
        old["client_version"] = "2.4.1.0"
        self.assertEqual(normalize_snapshot(old), normalize_snapshot(snapshot))
        self.assertEqual(old["client_version"], "2.4.1.0")

    def test_actual_previous_patch_is_captured_without_relabelling(self):
        with tempfile.TemporaryDirectory() as directory:
            game = self.game(Path(directory) / "game", "2.4.1.0")
            with patch.object(runtime.os, "getcwd", return_value=str(game)):
                with patch.object(runtime.sys, "executable", str(game / "win64/WorldOfTanks.exe")):
                    self.assertEqual(runtime._game_directory(), str(game.resolve()))
                    actual = runtime._game_client_version(game)
            self.assertEqual(make_snapshot(fixture(), "NA", client=actual)["client_version"], "2.4.1.0")


if __name__ == "__main__":
    unittest.main()
