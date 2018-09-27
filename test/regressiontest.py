import unittest

import parse


class TestParse(unittest.TestCase):
	jei_record = "(238222, '/projects/jei', 'https://github.com/mezz/JustEnoughItems', 'https://github.com/mezz/JustEnoughItems/issues?q=is%3Aissue', None, 'MIT License')"

	def test_mod_parse(self):  # basic test to check mod parsing still works
		modrecord = parse.scrape_result("/projects/jei")
		self.assertEqual(modrecord.test_form().__repr__(), self.jei_record)
