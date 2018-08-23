# get all the html off the internet into memory
import concurrent.futures
import sqlite3
import time
from typing import List
from urllib import request, parse
from bs4 import BeautifulSoup
from bs4.element import NavigableString

from new_src import parse_all, main

CURSEFORGE_HOME = "https://minecraft.curseforge.com"
CURSEFORGE_URL = CURSEFORGE_HOME + "/mc-mods?%s"
GAME_VERSION_1_12_2 = "2020709689:6756"
GAME_VERSION = GAME_VERSION_1_12_2


def init_input_queue(number_downloader_threads: int = 0) -> List[str]:    # for me, as many processes as possible gives a very fast result
	ret = []
	number_pages = get_number_pages()
	workers = number_downloader_threads if number_downloader_threads != 0 else number_pages
	with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:  # uses a lot of memory but fast
		project_ids = {executor.submit(get_project_links, i): i for i in range(1, number_pages + 1)}
		for future in concurrent.futures.as_completed(project_ids):
			ret.extend(future.result())
	print("no tasks left to do")
	return ret


def scrape_results(exts: List[str], NUMBER_PARSER_PROCESSES: int = 0):
	ret = []
	workers = NUMBER_PARSER_PROCESSES if NUMBER_PARSER_PROCESSES != 0 else 30
	with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:  #  uses a lot of memory but fast it seems on linux more processes == more memory == faster
		pages = {executor.submit(get_content, i): i for i in exts}            #  maybe due to unix using os.fork(). Not sure how this compares to windows
		for future in concurrent.futures.as_completed(pages):
			f = future.result()
			if f is not None:
				ret.append(f)
	return ret


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


def get_project_links(page: int, game_version: str = GAME_VERSION):
	connection = sqlite3.connect("../mods.db")
	cursor = connection.cursor()
	print("page", page)
	foundIDs = []
	with request.urlopen(get_url(game_version, page)) as url:
		raw_content = BeautifulSoup(url.read(), "lxml")
		ul = raw_content.find("ul", class_="listing listing-project project-listing")
		for li in ul.children:
			if isinstance(li, NavigableString):
				continue
			mod_descriptor = li.find("div", class_="details")

			# name and author
			info_name = mod_descriptor.find("div", class_="info name")

			name_tab = info_name.div.a
			name_link = name_tab.get("href")
			d = cursor.execute("SELECT id, accessed FROM mods WHERE link_extension=? LIMIT 1", (name_link,))    # does this cause performance issues? or does the database handle multiple reads fine?
			found_link = d.fetchone()
			if not found_link:
				foundIDs.append(name_link)
				print("added mod %s" % name_link)
			else:
				if int(time.time()) - found_link[1] < main.CACHE_TIMEOUT:
					print("cache expired on %s" % name_link)
					foundIDs.append(name_link)
				else:
					print("ignoring ID already in db %d" % found_link[0])
	connection.close()
	return foundIDs


def get_content(ext: str):  # TODO - handle exceptions here eg - timeouts
	print("downloading: ", ext)
	try:
		with request.urlopen(CURSEFORGE_HOME + ext, timeout=30) as raw:
			return parse_all.scrape_file_in_results(raw.read(), ext)
	except Exception as e:
		print(e.__repr__())
		print("something went wrong")
		return None


class ModRecord:    # TODO - use tuple/dict instead of this ugly class
	__slots__ = ("_project_id",
	             "_wiki_link",
	             "_issues_link",
	             "_source_link",
	             "_license_link",
	             "_name_link",
	             "_license")

	def __init__(self):
		self._project_id = None
		self._wiki_link = None
		self._issues_link = None
		self._source_link = None
		self._license_link = None
		self._license = None
		self._name_link = None

	def __repr__(self) -> str:
		ret = ""
		ret += str(self._name_link) + " "
		ret += str(self._project_id) + " "
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

	def set_name_link(self, name_link):
		self._name_link = name_link

	def get_project_id(self):
		return self._project_id

	def as_tuple(self): # TODO - perhaps there is a better way to do this, also maybe set accessed time?
		return self._project_id, int(time.time()), self._name_link, self._source_link, self._issues_link, self._wiki_link, self._license_link, self._license
