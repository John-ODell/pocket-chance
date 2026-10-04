"""Guard against HR-F02: on the board '' (the root) is first on sys.path and MicroPython treats a
bare folder as a package, so a module named like a root folder (/assets, /lib, /games) is shadowed
and never imports. CPython never shows this, so check it here."""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_FOLDERS = {'lib', 'games', 'assets'}
BOARD_FILES = {'pocket', 'main', 'save', 'boot'}      # names that live or may live in the root


def board_modules():
    mods = {}
    for d in ('lib', 'games'):
        for n in os.listdir(os.path.join(ROOT, d)):
            if n.endswith('.py'):
                mods[n[:-3]] = d + '/' + n
    mods['pocket'] = 'pocket.py'
    return mods


class BoardNames(unittest.TestCase):
    def test_no_module_named_like_a_board_folder(self):
        for name, path in board_modules().items():
            self.assertNotIn(name, BOARD_FOLDERS, '%s would be shadowed by the /%s folder on the board' % (path, name))

    def test_no_import_of_a_board_folder_name(self):
        pat = re.compile(r'^\s*(?:from\s+(\w+)\s+import|import\s+(\w+))', re.M)
        for d in ('lib', 'games', 'tools', '.'):
            for n in os.listdir(os.path.join(ROOT, d)):
                if not n.endswith('.py'):
                    continue
                with open(os.path.join(ROOT, d, n)) as f:
                    for m in pat.finditer(f.read()):
                        mod = m.group(1) or m.group(2)
                        self.assertNotIn(mod, BOARD_FOLDERS, '%s/%s imports %r, a board folder name' % (d, n, mod))

    def test_lib_and_games_names_are_unique(self):
        names = [n[:-3] for d in ('lib', 'games') for n in os.listdir(os.path.join(ROOT, d)) if n.endswith('.py')]
        self.assertEqual(len(names), len(set(names)), names)

    def test_upload_list_matches_files(self):
        with open(os.path.join(ROOT, 'UPLOAD.md')) as f:
            text = f.read()
        for name, path in board_modules().items():
            self.assertIn('`%s`' % path, text, '%s is not in UPLOAD.md' % path)
        self.assertNotIn('lib/assets.py', text)
