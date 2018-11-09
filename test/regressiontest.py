import unittest

import parse


class TestParse(unittest.TestCase):
	jei_record = "(238222, '/projects/jei', 'https://github.com/mezz/JustEnoughItems', 'https://github.com/mezz/JustEnoughItems/issues?q=is%3Aissue', None, 'MIT License')"

	# a basic regression test to check that parsing still works (and curseforge hasn't changed their website format)
	def test_mod_parse(self):
		modrecord = parse.scrape_result("/projects/jei")
		self.assertEqual(modrecord.test_form().__repr__(), self.jei_record)
