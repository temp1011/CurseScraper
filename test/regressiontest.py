import unittest
from urllib.request import urlopen

import downloads_all
import parse_all


class TestParse(unittest.TestCase):
	jei_record = "(238222, '/projects/jei', 'https://github.com/mezz/JustEnoughItems', 'https://github.com/mezz/JustEnoughItems/issues?q=is%3Aissue', None, '/projects/jei/license', 'MIT License')"

	def test_mod_parse(self):   # basic test to check mod parsing still works
		with urlopen(downloads_all.CURSEFORGE_HOME+"/projects/jei") as url:
			modrecord = parse_all.scrape_file_in_results(url.read(), "/projects/jei")
			self.assertEqual(modrecord.test_form().__repr__(),self.jei_record)