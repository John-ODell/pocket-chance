import unittest

import tests.context  # noqa: F401
import sheets
from cards import card_name


class Sheets(unittest.TestCase):
    def test_card_order_matches_the_engine(self):
        w, h, count = sheets.SHEETS['cards']
        names = sheets.names('cards')
        self.assertEqual((w, h, count), (40, 56, 53))
        self.assertEqual(len(names), 53)
        for c in range(52):
            self.assertEqual(names[c], 'c_' + card_name(c))
        self.assertEqual(names[52], 'c_back')
        self.assertEqual(sheets.member('c_AS'), ('cards', 0))
        self.assertEqual(sheets.member('c_back'), ('cards', 52))

    def test_other_families(self):
        self.assertEqual(sheets.member('chip_5'), ('chips', 1))
        self.assertEqual(sheets.member('banner_bust'), ('banners', 3))
        self.assertEqual(sheets.member('banner_noqualify'), ('banners', 5))
        self.assertEqual(sheets.SHEETS['banners'][2], 6)
        self.assertEqual(sheets.member('icon_stud'), ('icons', 1))
        self.assertIsNone(sheets.member('sym_cherry'))                # slots dropped (D-009)
        self.assertIsNone(sheets.member('table'))
        self.assertIsNone(sheets.member('banner_jackpot'))      # 200x40, stays a single file
        self.assertIsNone(sheets.member('logo'))
        self.assertIsNone(sheets.member('c_1S'))
        self.assertIsNone(sheets.member('chip_7'))
        self.assertIsNone(sheets.member('c_ASX'))
        for sheet in sheets.SHEETS:
            for i, n in enumerate(sheets.names(sheet)):
                self.assertEqual(sheets.member(n), (sheet, i), n)

    def test_offsets_and_sizes(self):
        self.assertEqual(sheets.offset('cards', 0), 4)
        self.assertEqual(sheets.offset('cards', 1), 4 + 4480)
        self.assertEqual(sheets.file_size('cards'), 4 + 53 * 4480)
        self.assertEqual(sheets.file_size('icons'), 4 + 4 * 48 * 48 * 2)

    def test_names_unique_across_sheets(self):
        seen = set()
        for sheet in sheets.SHEETS:
            for n in sheets.names(sheet):
                self.assertNotIn(n, seen)
                seen.add(n)


if __name__ == '__main__':
    unittest.main()
