import os
import shutil
import tempfile
import unittest

import tests.context  # noqa: F401
from save import Store, encode, decode, checksum, MSG_RESTORED, MSG_FRESH


class Codec(unittest.TestCase):
    def test_round_trip(self):
        for bank in (0, 5, 1000, 123456789):
            self.assertEqual(decode(encode(bank)), bank)

    def test_rejects_garbage(self):
        for bad in ('', 'x', '{}', '[]', '{"v":1,"bank":10,"chk":0}', '{"v":2,"bank":10,"chk":%d}' % checksum(10),
                    '{"v":1,"bank":-1,"chk":%d}' % checksum(-1), '{"v":1,"bank":"10","chk":1}',
                    '{"v":1,"bank":true,"chk":%d}' % checksum(1), encode(1000)[:-3]):
            self.assertIsNone(decode(bad), bad)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store = Store(os.path.join(self.dir, 'save.json'))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def files(self):
        return sorted(os.listdir(self.dir))

    def write_main(self, text):
        with open(self.store.path, 'w') as f:
            f.write(text)

    def test_first_run_is_silent(self):
        self.assertEqual(self.store.load(), (None, None))
        self.assertEqual(self.files(), [])

    def test_save_then_load(self):
        self.store.save(950)
        self.assertEqual(self.store.load(), (950, None))
        self.assertEqual(self.files(), ['save.json'])

    def test_second_save_keeps_backup(self):
        self.store.save(950)
        self.store.save(960)
        self.assertEqual(self.files(), ['save.bak', 'save.json'])
        self.assertEqual(self.store.load(), (960, None))
        with open(self.store.bak) as f:
            self.assertEqual(decode(f.read()), 950)

    def test_corrupt_main_restores_backup(self):
        self.store.save(950)
        self.store.save(960)
        self.write_main('{"v":1,"bank":9999')
        self.assertEqual(self.store.load(), (950, MSG_RESTORED))
        self.assertEqual(self.files(), ['save.bad', 'save.bak'])

    def test_corrupt_main_and_backup_starts_fresh(self):
        self.store.save(950)
        self.store.save(960)
        self.write_main('junk')
        with open(self.store.bak, 'w') as f:
            f.write('more junk')
        self.assertEqual(self.store.load(), (None, MSG_FRESH))
        self.assertIn('save.bad', self.files())

    def test_corrupt_main_no_backup_starts_fresh(self):
        self.write_main('junk')
        self.assertEqual(self.store.load(), (None, MSG_FRESH))
        self.assertEqual(self.files(), ['save.bad'])

    def test_bad_file_is_overwritten_on_second_damage(self):
        self.write_main('junk1')
        self.store.load()
        self.write_main('junk2')
        self.assertEqual(self.store.load(), (None, MSG_FRESH))
        with open(self.store.bad) as f:
            self.assertEqual(f.read(), 'junk2')

    def test_save_after_recovery_works(self):
        self.write_main('junk')
        self.store.load()
        self.store.save(1000)
        self.assertEqual(self.store.load(), (1000, None))

    def test_leftover_tmp_is_harmless(self):
        with open(self.store.tmp, 'w') as f:
            f.write('half written')
        self.store.save(500)
        self.assertEqual(self.store.load(), (500, None))
        self.assertNotIn('save.tmp', self.files())


if __name__ == '__main__':
    unittest.main()
