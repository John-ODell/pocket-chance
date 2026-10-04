import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import check_upload  # noqa: E402


class CheckUpload(unittest.TestCase):
    def test_parses_rows(self):
        text = "| # | a | b |\n|---|---|---|\n| 1 | `lib/lcd.py` | `/lib/lcd.py` |\n| 2 | `pocket.py` | `/pocket.py` |\n"
        self.assertEqual(check_upload.rows(text), [('lib/lcd.py', '/lib/lcd.py'), ('pocket.py', '/pocket.py')])

    def test_good_rows(self):
        self.assertEqual(check_upload.check_row('lib/lcd.py', '/lib/lcd.py'), [])
        self.assertEqual(check_upload.check_row('pocket.py', '/pocket.py'), [])
        self.assertEqual(check_upload.check_row('lib/art.py', '/lib/art.py (not assets.py)'), [])

    def test_bad_rows(self):
        self.assertTrue(check_upload.check_row('lib/nope.py', '/lib/nope.py'))
        self.assertTrue(check_upload.check_row('lib/lcd.py', '/lcd.py'))
        self.assertTrue(check_upload.check_row('lib/lcd.py', '/lib/screen.py'))
        self.assertTrue(check_upload.check_row('games/blackjack.py', '/lib/blackjack.py'))

    def test_current_upload_md_is_clean(self):
        self.assertEqual(check_upload.main(['--no-tests']), 0)


if __name__ == '__main__':
    unittest.main()
