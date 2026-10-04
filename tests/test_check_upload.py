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

    def test_record_catches_a_missing_method_and_import(self):
        # a board file calling a method the recorded library lacks (the step-1g bug), and an
        # import of a module that is not on the board
        import tempfile, subprocess
        root = check_upload.ROOT
        old_blob = subprocess.check_output(['git', 'hash-object', '-w', '--stdin'], cwd=root,
                                           input=b'class Assets:\n    def blit(self, fb, name, x, y):\n        pass\n').decode().strip()
        game_blob = subprocess.check_output(['git', 'hash-object', '-w', '--stdin'], cwd=root,
                                           input=b'from art import Assets\nimport mystery\nx = assets.open_sprite(1)\ny = lcd.fill(0)\n').decode().strip()
        text = ('| Board path | Repo file | Step | Version (git blob) |\n|---|---|---|---|\n'
                '| `/lib/art.py` | `lib/art.py` | 1f | %s |\n'
                '| `/games/slots.py` | `games/slots.py` | 1g | %s |\n' % (old_blob[:12], game_blob[:12]))
        problems, warnings = check_upload.check_record(text)
        joined = '\n'.join(problems)
        self.assertIn('assets.open_sprite()', joined)
        self.assertIn("imports 'mystery'", joined)
        self.assertNotIn('lcd.fill', joined)                   # framebuf method, not ours
        self.assertTrue(any('differs from the version on the board' in w for w in warnings))

    def test_record_helper_updates_rows(self):
        text = ('| Board path | Repo file | Step | Version (git blob) |\n|---|---|---|---|\n'
                '| `/lib/art.py` | `lib/art.py` | 1f | 000000000000 |\n')
        out = check_upload.update_record(text, '1h', ['lib/art.py', 'games/blackjack.py'])
        self.assertIn('| `/lib/art.py` | `lib/art.py` | 1h | %s |' % check_upload.blob_of('lib/art.py')[:12], out)
        self.assertIn('| `/games/blackjack.py` | `games/blackjack.py` | 1h |', out)
        self.assertNotIn('000000000000', out)

    def test_current_upload_md_is_clean(self):
        self.assertEqual(check_upload.main(['--no-tests']), 0)


if __name__ == '__main__':
    unittest.main()
