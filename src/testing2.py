from urllib import request, parse
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from typing import List
import queue
import threading
import time
import logging
import sqlite3
from typing import Callable

CURSEFORGE_HOME = "https://minecraft.curseforge.com"
CURSEFORGE_URL = CURSEFORGE_HOME + "/mc-mods?%s"
GAME_VERSION_1_12_2 = "2020709689:6756"
NUMBER_WORKER_THREADS = 30
GAME_VERSION = GAME_VERSION_1_12_2
PAGE_QUEUE = queue.Queue()
RESULTS = queue.Queue()
PROJECT_LINKS = queue.Queue()
INPUTS = queue.Queue()


# TODO in future
# get the urls. Each url then spawns a thread? Or a threadpool works through them.
# Will have to see if bottleneck is bandwidth though
# could get pages in parallel too
#
# UPDATE 15/8/18: pages for mod lists are now gotten in parallel, it's much faster (took: 40.55830955505371)
# TODO - get more info: project id, source, issues, wiki, license, created, recent files? if I can get enough for maven that would be very nice
# CurseMeta will definitely get most of these. I just need to find issues, wiki, source, license. But need to check what the raw API actually returns.
# done - 16/8/18
# use pycurl or even shell for better performance?
# logging
# move to database (sqlite)
# TODO - maybe - get web content async (and possibly cache it too!) - doing now

# TODO - move to worker that takes callable off the queue and executes it. Much easier to expand. - in progress
# start timing thread inpact (higher or lower better?) work out why parsing is so slow (why do cores not go to 100% in system monitor?) - look into multiprocessing


class FutureCall:
	def __init__(self, func, *args):
		self._func = func
		self._args = args

	def call(self):
		return self._func(*self._args)


# def worker():
# 	while True:
# 		if not PAGE_QUEUE.empty():
# 			item = PAGE_QUEUE.get()
# 			if item is None:
# 				return
# 			get_project_ids(item)
# 			print(PAGE_QUEUE.qsize(), PROJECT_LINKS.qsize(), RESULTS.qsize())
# 			PAGE_QUEUE.task_done()
# 		elif not PROJECT_LINKS.empty():
# 			ext = PROJECT_LINKS.get()
# 			if ext is None:
# 				return
# 			print("download", ext)
# 			RESULTS.put(request.urlopen(CURSEFORGE_HOME+ext).read())
# 			print(PAGE_QUEUE.qsize(), PROJECT_LINKS.qsize(), RESULTS.qsize())
# 			PROJECT_LINKS.task_done()


def worker():
	while True:
		item = INPUTS.get()
		if item is None:
			return
		item.call()
		INPUTS.task_done()
		print(INPUTS.qsize())


def main():
	a = time.time()

	threads = []
	for i in range(NUMBER_WORKER_THREADS):
		t = threading.Thread(target=worker)
		t.start()
		threads.append(t)

	for i in range(1, get_number_pages() + 1):
		INPUTS.put(FutureCall(get_project_ids, i))

	# block until all tasks are done
	INPUTS.join()
	print("everything has finished!")
	# stop workers
	for i in range(NUMBER_WORKER_THREADS):
		INPUTS.put(None)
	for t in threads:
		t.join()
	print("starting parsing.....")
	with open("data3", "w") as file:
		while not RESULTS.empty():
			file.write(RESULTS.get().__repr__() + "\n")
			RESULTS.task_done()

	print("took:", time.time() - a)


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

	return highest


def get_project_ids(page: int = 1, game_version: str = GAME_VERSION) -> None:
	print("page", page, threading.get_ident())
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
			INPUTS.put(FutureCall(get_content, name_tab.get("href")))


def get_content(ext: str):
	print("downloading: ", ext)
	with request.urlopen(CURSEFORGE_HOME + ext) as raw:
		INPUTS.put(FutureCall(scrape_file_in_results, raw.read()))


# def scrape_mod_page(mod_record: ModRecord):
# 	print("scraping", mod_record._name)
# 	with request.urlopen(CURSEFORGE_HOME + mod_record._name_link) as page:
# 		raw_content = BeautifulSoup(page.read(), "lxml")
# 		for header in raw_content.find("ul", class_="e-menu").find_all("a", class_="external-link"):
# 			s = header.string.strip().lower()
# 			link = header.get("href").strip()
# 			if s == "source":
# 				mod_record.set_source_link(link)
# 			elif s == "wiki":
# 				mod_record.set_wiki_link(link)
# 			elif s == "issues":
# 				mod_record.set_issues_link(link)
# 			else:
# 				pass
#
# 		license_stuff = raw_content.find("ul", class_="cf-details project-details").find("a")
# 		mod_record.set_license_link(license_stuff.get("href"))
# 		mod_record.set_license(license_stuff.string.strip() if license_stuff.string is not None else None)

def scrape_file_in_results(raw_mod_page: str) -> None:
	ret = ModRecord("", "", "", "", 0, 0, "")
	raw_content = BeautifulSoup(raw_mod_page, "lxml")
	for header in raw_content.find("ul", class_="e-menu").find_all("a", class_="external-link"):
		s = header.string.strip().lower()
		link = header.get("href").strip()
		if s == "source":
			ret.set_source_link(link)
		elif s == "wiki":
			ret.set_wiki_link(link)
		elif s == "issues":
			ret.set_issues_link(link)
		else:
			pass
	side_bar = raw_content.find("ul", class_="cf-details project-details")
	license_stuff = side_bar.find("a")
	ret.set_license_link(license_stuff.get("href"))
	ret.set_license(license_stuff.string.strip() if license_stuff.string is not None else None)
	ret.set_project_id(int(side_bar.contents[1].contents[3].string))    # TODO - ugly hack
	RESULTS.put(ret)


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


with request.urlopen(CURSEFORGE_HOME + "/projects/jei") as raw:
	scrape_file_in_results(raw.read())

if __name__ == "__main__":
	main()
