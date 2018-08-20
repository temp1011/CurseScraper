# get all the html off the internet into memory
import concurrent.futures
from typing import List
from urllib import request, parse
from bs4 import BeautifulSoup
from bs4.element import NavigableString
import threading

from new_src import parse_all

CURSEFORGE_HOME = "https://minecraft.curseforge.com"
CURSEFORGE_URL = CURSEFORGE_HOME + "/mc-mods?%s"
GAME_VERSION_1_12_2 = "2020709689:6756"
GAME_VERSION = GAME_VERSION_1_12_2


def init_input_queue() -> List[str]:    # for me, as many processes as possible gives a very fast result
	ret = []
	number_pages = get_number_pages()
	with concurrent.futures.ProcessPoolExecutor(max_workers=number_pages) as executor:  # uses a lot of memory but fast
		project_ids = {executor.submit(get_project_ids, i): i for i in range(1, number_pages + 1)}
		for future in concurrent.futures.as_completed(project_ids):
			ret.extend(future.result())
	print("no tasks left to do")
	return ret


def scrape_results(exts: List[str]):
	with concurrent.futures.ProcessPoolExecutor(max_workers=100) as executor:  # uses a lot of memory but fast it seems on linux more processes == more memory == faster
		with concurrent.futures.ProcessPoolExecutor(max_workers=100) as executor2:
			pages = {executor.submit(get_content, i): i for i in exts}
			for future in concurrent.futures.as_completed(pages):
				pass


def get_url(game_version: str = GAME_VERSION, page: int = 1) -> str:
	return CURSEFORGE_URL % parse.urlencode({"filter-game-version": game_version, "page": page})


def get_number_pages(game_version: str = GAME_VERSION) -> int:  # curseforge gives us mobile stuff here
	highest = 0
	with request.urlopen(get_url(game_version)) as page:
		page_list = BeautifulSoup(page.read(), "lxml").find(
			class_="b-pagination-list paging-list j-tablesorter-pager j-listing-pagination")
		for li in page_list.children:
			if isinstance(li, NavigableString):
				continue
			try:
				link = li.find("a").get("href")
				page_number = int(link.split("page")[1].replace("=", ""))
				highest = max(page_number, highest)
			except:
				pass
	global NUMBER_PAGES
	NUMBER_PAGES = highest
	return highest


def get_project_ids(page: int, game_version: str = GAME_VERSION):
	print("page", page, threading.get_ident())
	foundIDs = []
	with request.urlopen(get_url(game_version, page), timeout=10) as url:
		raw_content = BeautifulSoup(url.read(), "lxml")
		ul = raw_content.find("ul", class_="listing listing-project project-listing")
		for li in ul.children:
			if isinstance(li, NavigableString):
				continue
			mod_descriptor = li.find("div", class_="details")

			# name and author
			info_name = mod_descriptor.find("div", class_="info name")

			name_tab = info_name.div.a
			foundIDs.append(name_tab.get("href"))
	return foundIDs


def get_content(ext: str):  # TODO - handle exceptions here eg - timeouts
	print("downloading: ", ext)
	with request.urlopen(CURSEFORGE_HOME + ext, timeout=10) as raw:
		parse_all.scrape_file_in_results(raw.read())


class ModRecord:
	__slots__ = ("_project_id",
	             "_name",
	             "_name_link",
	             "_author",
	             "_author_link",
	             "_download_count",
	             "_updated",
	             "_description",
	             "_wiki_link",
	             "_issues_link",
	             "_source_link",
	             "_license_link",
	             "_license")

	def __init__(self, name: str, name_link: str, author: str, author_link: str, download_count: int, updated: int,
	             description: str):
		self._project_id = None
		self._name = name
		self._name_link = name_link
		self._author = author
		self._author_link = author_link
		self._download_count = download_count
		self._updated = updated
		self._description = description
		self._wiki_link = None
		self._issues_link = None
		self._source_link = None
		self._license_link = None
		self._license = None

	def __repr__(self) -> str:
		ret = ""
		ret += str(self._project_id) if self._project_id is not None else ""
		ret += self._name + " "
		ret += self._name_link + " "
		ret += self._author + " "
		ret += self._author_link + " "
		ret += str(self._download_count) + " "
		ret += str(self._updated) + " "
		ret += self._description + " "
		ret += str(self._wiki_link) + " "
		ret += str(self._issues_link) + " "
		ret += str(self._source_link) + " "
		ret += str(self._license_link) + " "
		ret += str(self._license)
		return ret

	def set_wiki_link(self, wiki_link):
		self._wiki_link = wiki_link

	def set_issues_link(self, issues_link):
		self._issues_link = issues_link

	def set_source_link(self, source_link):
		self._source_link = source_link

	def set_license_link(self, license_link):
		self._license_link = license_link

	def set_license(self, lic):
		self._license = lic

	def set_project_id(self, id):
		self._project_id = id

	def project_url(self) -> str:
		return CURSEFORGE_HOME + self._name_link

