import unittest

import tests.context  # noqa: F401
from pixfmt import rgb565, swap, rgb, KEY, KEY_BE, KEY_RGB


class PixFmt(unittest.TestCase):
    def test_primaries(self):
        self.assertEqual(rgb565(255, 0, 0), 0xF800)
        self.assertEqual(rgb565(0, 255, 0), 0x07E0)
        self.assertEqual(rgb565(0, 0, 255), 0x001F)
        self.assertEqual(rgb565(255, 255, 255), 0xFFFF)
        self.assertEqual(rgb565(0, 0, 0), 0)

    def test_swapped_matches_hr003(self):
        # HR-003: red 0x00F8, green 0xE007, blue 0x1F00 for framebuf
        self.assertEqual(rgb(255, 0, 0), 0x00F8)
        self.assertEqual(rgb(0, 255, 0), 0xE007)
        self.assertEqual(rgb(0, 0, 255), 0x1F00)
        self.assertEqual(rgb(255, 255, 255), 0xFFFF)

    def test_key(self):
        self.assertEqual(rgb565(*KEY_RGB), KEY_BE)
        self.assertEqual(swap(KEY_BE), KEY)
        self.assertEqual(KEY, 0x1FF8)

    def test_swap_round_trip(self):
        for v in (0, 1, 0x1234, 0xABCD, 0xFFFF):
            self.assertEqual(swap(swap(v)), v)

    def test_old_driver_agreement(self):
        # colour() from main_monolith.py, for a few values
        def colour(R, G, B):
            rp = int(R * 31 / 255); r = rp * 8
            gp = int(G * 63 / 255); g = 0
            if gp & 1: g += 8192
            if gp & 2: g += 16384
            if gp & 4: g += 32768
            if gp & 8: g += 1
            if gp & 16: g += 2
            if gp & 32: g += 4
            bp = int(B * 31 / 255); b = bp * 256
            return r + g + b
        for t in ((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255), (0, 0, 0), (255, 0, 255)):
            self.assertEqual(rgb(*t), colour(*t), t)


if __name__ == '__main__':
    unittest.main()
