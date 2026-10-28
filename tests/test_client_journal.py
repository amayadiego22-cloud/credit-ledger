import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import core.ledger as ledger_module
from capture import storage


class ClientJournalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="credit-ledger-journal-")
        self.destination = os.path.join(self.directory, "record.json")
        self.source = os.path.join(self.directory, "record.tmp")

    def tearDown(self):
        shutil.rmtree(self.directory)

    def _write(self, path, content):
        with open(path, "wb") as handle:
            handle.write(content)

    def _read(self, path):
        with open(path, "rb") as handle:
            return handle.read()

    def test_both_fallbacks_replace_without_ctypes_and_keep_previous(self):
        for replacement in (storage._journal_replace, ledger_module._windows_replace):
            self._write(self.destination, b"old")
            self._write(self.source, b"new")
            replacement(self.source, self.destination)
            self.assertEqual(self._read(self.destination), b"new")
            self.assertEqual(self._read(self.destination + ".previous"), b"old")

    def test_failed_new_rename_restores_previous_file(self):
        real_rename = os.rename
        def fail_new(source, destination):
            if source == self.source:
                raise OSError("synthetic new-file rename failure")
            return real_rename(source, destination)
        for replacement in (storage._journal_replace, ledger_module._windows_replace):
            self._write(self.destination, b"old")
            self._write(self.source, b"new")
            with patch.object(os, "rename", side_effect=fail_new):
                with self.assertRaises(OSError):
                    replacement(self.source, self.destination)
            self.assertEqual(self._read(self.destination), b"old")

    def test_capture_recovers_interrupted_commit_before_existence_check(self):
        self._write(self.destination + ".previous", b'{"old": true}')
        self.assertTrue(storage.json_exists(self.destination))
        self.assertEqual(storage.read_json(self.destination), {"old": True})
        self.assertTrue(os.path.isfile(self.destination))

    def test_ledger_recovers_interrupted_commit_on_load(self):
        ledger = ledger_module.EconomyLedger()
        ledger.save(self.destination)
        os.rename(self.destination, self.destination + ".previous")
        loaded = ledger_module.EconomyLedger.load(self.destination)
        self.assertEqual(loaded.to_dict(), ledger.to_dict())
        self.assertTrue(os.path.isfile(self.destination))


if __name__ == "__main__":
    unittest.main()
