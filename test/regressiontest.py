import os
import unittest

import download
import parse


def relative_path(p: str) -> str:
	dirname = os.path.dirname(__file__)
	return os.path.join(dirname, p)


def url_exists(url: str) -> bool:
	try:
		res = download.download(url)
		return res is not None
	except Exception:
		return False


# contains both tests against specific saved html and general stuff in case the curseforge website changes.
# Hopefully this means I am more safe against changes by refactoring and changes to the curseforge website
class TestParse(unittest.TestCase):
	jei_record = "(238222, '/minecraft/mc-mods/jei', 'https://github.com/mezz/JustEnoughItems', 'https://github.com/mezz/JustEnoughItems/issues?q=is%3Aissue', None, 'MIT License')"

	# a basic regression test to check that parsing still works (and curseforge hasn't changed their website format)
	def test_mod_parse(self):
		modrecord = parse.fetch_and_scrape("/minecraft/mc-mods/jei")
		self.assertEqual(238222, modrecord.get_project_id())    # pretty much the only thing I can guarantee

	def test_mod_parse_specific(self):
		with open(relative_path("resources/jei_page_20190715.html"), "rb") as f:
			modrecord = parse.fetch_and_scrape("/minecraft/mc-mods/jei")
			self.assertEqual(self.jei_record, modrecord.test_form().__repr__())

	# a basic check to make sure the curseforge url is the same
	def test_listing_url_specific(self):
		self.assertTrue(url_exists(download.get_listing_url("2020709689:6756", 1)))

	def test_content_url_specific(self):
		self.assertTrue(url_exists(download.get_content_url("/minecraft/mc-mods/jei")))

	def test_listing_url_general(self):
		self.assertTrue(url_exists(download.get_listing_url()))

	# check the download function works
	def test_download(self):
		download.download("https://www.google.com")

	# check the parsing works for a saved html page
	def test_number_pages_specific(self):
		with open(relative_path("resources/mod_listing_page_1_20190715.html"), "rb") as f:
			maxpage = parse.get_number_pages(f.read())
			self.assertEqual(maxpage, 279)

	def test_number_pages_general(self):
		url = download.get_listing_url()
		maxpage = parse.get_number_pages(download.download(url))
		self.assertTrue(maxpage > 10,
		             "cannot parse number of pages correctly")  # 10 is a reasonable number for any version

	def test_project_links_specific(self):
		links = {'/minecraft/mc-mods/mouse-tweaks', '/minecraft/mc-mods/crafttweaker', '/minecraft/mc-mods/iron-chests', '/minecraft/mc-mods/inventory-tweaks', '/minecraft/mc-mods/resource-loader', '/minecraft/mc-mods/chisel', '/minecraft/mc-mods/codechicken-lib-1-8', '/minecraft/mc-mods/applied-energistics-2', '/minecraft/mc-mods/shadowfacts-forgelin', '/minecraft/mc-mods/baubles', '/minecraft/mc-mods/ctm', '/minecraft/mc-mods/appleskin', '/minecraft/mc-mods/jei', '/minecraft/mc-mods/modtweaker', '/minecraft/mc-mods/thermal-foundation', '/minecraft/mc-mods/tinkers-construct', '/minecraft/mc-mods/mantle', '/minecraft/mc-mods/cofh-core', '/minecraft/mc-mods/journeymap', '/minecraft/mc-mods/custom-main-menu'}
		with open(relative_path("resources/mod_listing_page_1_20190715.html"), "rb") as f:
			self.assertEqual(links, parse.get_project_links(f.read()))

	def test_project_links_general(self):
		url = download.get_listing_url(download.GAME_VERSION, 1)
		res = parse.fetch_and_get_project_links(url)
		print(res)
		self.assertTrue(i is not None for i in res)
		self.assertTrue(len(res) > 0)

	# TODO - test for page erroring and check None handled correctly
