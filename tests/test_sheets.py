import unittest

import tests.context  # noqa: F401
import sheets
from cards import card_name
from slots_rules import SYMBOLS


class Sheets(unittest.TestCase):
    def test_card_order_matches_the_engine(self):
        w, h, names = sheets.SHEETS['cards']
        self.assertEqual((w, h), (40, 56))
        self.assertEqual(len(names), 53)
        for c in range(52):
            self.assertEqual(names[c], 'c_' + card_name(c))
        self.assertEqual(names[52], 'c_back')
        self.assertEqual(sheets.member('c_AS'), ('cards', 0))
        self.assertEqual(sheets.member('c_back'), ('cards', 52))

    def test_symbol_order_matches_slots(self):
        w, h, names = sheets.SHEETS['symbols']
        self.assertEqual(tuple(names), tuple('sym_' + s for s in SYMBOLS))
        self.assertEqual((w, h), (56, 56))

    def test_other_families(self):
        self.assertEqual(sheets.member('chip_5'), ('chips', 1))
        self.assertEqual(sheets.member('banner_bust'), ('banners', 3))
        self.assertEqual(sheets.member('icon_slots'), ('icons', 1))
        self.assertIsNone(sheets.member('table'))
        self.assertIsNone(sheets.member('banner_jackpot'))      # 200x40, stays a single file
        self.assertIsNone(sheets.member('logo'))

    def test_offsets_and_sizes(self):
        self.assertEqual(sheets.offset('cards', 0), 4)
        self.assertEqual(sheets.offset('cards', 1), 4 + 4480)
        self.assertEqual(sheets.file_size('cards'), 4 + 53 * 4480)
        self.assertEqual(sheets.sprite_bytes('symbols'), 6272)

    def test_names_unique_across_sheets(self):
        seen = set()
        for w, h, names in sheets.SHEETS.values():
            for n in names:
                self.assertNotIn(n, seen)
                seen.add(n)


if __name__ == '__main__':
    unittest.main()
