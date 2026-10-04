import os
import shutil
import struct
import tempfile
import unittest

import tests.context  # noqa: F401
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
from convert_assets import (to_565, expected_size, convert_file, zone_warnings, TABLE_ZONES,  # noqa: E402
                            MENU_ZONES)
from pixfmt import KEY_BE  # noqa: E402

try:
    from PIL import Image
except ImportError:   # Pillow is a Mac-side tool dependency (DR-004)
    Image = None


class To565(unittest.TestCase):
    def test_header_and_order(self):
        data, nudged = to_565([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 255)], 2, 2)
        self.assertEqual(len(data), 4 + 8)
        self.assertEqual(struct.unpack_from('<HH', data, 0), (2, 2))
        # big-endian: red F8 00, green 07 E0, blue 00 1F, key F8 1F
        self.assertEqual(data[4:], bytes([0xF8, 0x00, 0x07, 0xE0, 0x00, 0x1F, 0xF8, 0x1F]))
        self.assertEqual(nudged, 0)

    def test_near_magenta_is_nudged(self):
        # (255, 3, 255) is not the key colour but converts to the same 565 value
        data, nudged = to_565([(255, 3, 255)], 1, 1)
        self.assertEqual(nudged, 1)
        self.assertNotEqual((data[4] << 8) | data[5], KEY_BE)

    def test_sizes(self):
        self.assertEqual(expected_size('c_AS'), (40, 56))
        self.assertEqual(expected_size('c_back'), (40, 56))
        self.assertEqual(expected_size('chip_500'), (24, 24))
        self.assertEqual(expected_size('table'), (240, 240))
        self.assertEqual(expected_size('logo'), (200, 40))
        self.assertEqual(expected_size('banner_win'), (160, 32))
        self.assertEqual(expected_size('icon_stud'), (48, 48))
        self.assertIsNone(expected_size('sym_cherry'))              # slots dropped (D-009)
        self.assertIsNone(expected_size('cabinet'))
        self.assertIsNone(expected_size('whatever'))


class ZoneWarnings(unittest.TestCase):
    def img(self, colour, w=240, h=240):
        return [colour] * (w * h)

    def test_dark_felt_is_fine(self):
        self.assertEqual(zone_warnings(self.img((0, 90, 40)), 240, 240), [])

    def test_light_table_warns_for_every_zone(self):
        w = zone_warnings(self.img((200, 200, 200)), 240, 240)
        self.assertEqual(len(w), len(TABLE_ZONES))
        self.assertIn('too light', w[0])

    def test_only_the_light_zone_warns(self):
        px = self.img((0, 90, 40))
        for y in range(0, 24):
            for x in range(240):
                px[y * 240 + x] = (230, 220, 200)
        w = zone_warnings(px, 240, 240)
        self.assertEqual(len(w), 1)
        self.assertIn('top line', w[0])

    def test_busy_zone_warns(self):
        px = self.img((0, 90, 40))
        for y in range(168, 240):
            for x in range(16, 224):
                if (x + y) % 3 == 0:
                    px[y * 240 + x] = (160, 160, 160)   # a third of the pixels bright, mean still under 100
        w = zone_warnings(px, 240, 240)
        self.assertEqual(len(w), 1)
        self.assertIn('calm', w[0])

    def test_zones_inside_screen(self):
        for zones in (TABLE_ZONES, MENU_ZONES):
            for name, (x, y, w, h) in zones:
                self.assertTrue(0 <= x and x + w <= 240 and 0 <= y and y + h <= 240, name)


@unittest.skipIf(Image is None, 'Pillow not installed')
class PackSheets(unittest.TestCase):
    def setUp(self):
        self.src = tempfile.mkdtemp()
        self.out = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.src)
        shutil.rmtree(self.out)

    def make(self, folder, name, size, colour):
        d = os.path.join(self.src, folder)
        os.makedirs(d, exist_ok=True)
        Image.new('RGB', size, colour).save(os.path.join(d, name), 'BMP')

    def test_pack_with_placeholders(self):
        from convert_assets import pack_sheet
        import sheets
        self.make('cards', 'c_as.bmp', (40, 56), (200, 10, 10))
        self.make('cards', 'c_back.bmp', (40, 56), (10, 10, 200))
        dst, missing = pack_sheet('cards', self.src, self.out)
        self.assertEqual(os.path.getsize(dst), sheets.file_size('cards'))
        self.assertEqual(len(missing), 51)
        self.assertNotIn('c_AS', missing)
        with open(dst, 'rb') as f:
            data = f.read()
        self.assertEqual(struct.unpack_from('<HH', data, 0), (40, 56 * 53))
        self.assertEqual(data[4], 0xC8)                                   # first pixel of c_AS: red high byte
        off = sheets.offset('cards', 1)
        self.assertEqual(data[off:off + 2], bytes([0xF8, 0x1F]))          # missing member: magenta key

    def test_wrong_size_member_is_an_error(self):
        from convert_assets import pack_sheet
        self.make('chips', 'chip_5.bmp', (25, 24), (1, 2, 3))
        with self.assertRaises(ValueError):
            pack_sheet('chips', self.src, self.out)

    def test_no_members_no_file(self):
        from convert_assets import pack_sheet
        dst, missing = pack_sheet('icons', self.src, self.out)
        self.assertIsNone(dst)
        self.assertEqual(len(missing), 3)


@unittest.skipIf(Image is None, 'Pillow not installed')
class ConvertFile(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def make(self, name, size, colour=(200, 30, 30), fmt='BMP'):
        p = os.path.join(self.dir, name)
        Image.new('RGB', size, colour).save(p, fmt)
        return p

    def test_card_bmp(self):
        src = self.make('c_as.bmp', (40, 56))
        dst = convert_file(src, self.dir)
        self.assertTrue(dst.endswith('c_AS.565'))
        self.assertEqual(os.path.getsize(dst), 4 + 40 * 56 * 2)

    def test_png_and_lowercase(self):
        src = self.make('Chip_5.png', (24, 24), fmt='PNG')
        dst = convert_file(src, self.dir)
        self.assertTrue(dst.endswith('chip_5.565'))

    def test_wrong_size_rejected(self):
        src = self.make('chip_5.bmp', (25, 24))
        with self.assertRaises(ValueError):
            convert_file(src, self.dir)

    def test_wrong_size_resized_on_request(self):
        src = self.make('table.bmp', (120, 120))
        dst = convert_file(src, self.dir, resize=True)
        self.assertEqual(os.path.getsize(dst), 4 + 240 * 240 * 2)

    def test_unknown_name_rejected(self):
        src = self.make('mystery.bmp', (10, 10))
        with self.assertRaises(ValueError):
            convert_file(src, self.dir)
        convert_file(src, self.dir, any_size=True)


if __name__ == '__main__':
    unittest.main()
