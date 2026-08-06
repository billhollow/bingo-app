from django.test import SimpleTestCase

from rooms.colors import Color


class ColorTests(SimpleTestCase):
    def test_blank_has_no_names(self):
        self.assertEqual(Color.BLANK.names, [])

    def test_single_color_name(self):
        self.assertEqual(Color.RED.names, ["red"])

    def test_composite_color_names(self):
        composite = Color.RED | Color.BLUE
        self.assertCountEqual(composite.names, ["red", "blue"])

    def test_membership(self):
        composite = Color.RED | Color.BLUE
        self.assertIn(Color.RED, composite)
        self.assertNotIn(Color.GREEN, composite)

    def test_removal(self):
        composite = Color.RED | Color.BLUE
        remaining = composite & ~Color.RED
        self.assertEqual(remaining, Color.BLUE)

    def test_all_ten_non_blank_colors_fit_in_a_positive_small_int(self):
        # PositiveSmallIntegerField tops out at 32767.
        everything = Color.BLANK
        for color in Color:
            everything |= color
        self.assertLessEqual(int(everything), 32767)
        self.assertEqual(len(everything.names), 10)
