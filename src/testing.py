from urllib import request, parse
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from typing import List
import queue
import threading
import time
import logging
import sqlite3

CURSEFORGE_HOME = "https://minecraft.curseforge.com"
CURSEFORGE_URL = CURSEFORGE_HOME + "/mc-mods?%s"
GAME_VERSION_1_12_2 = "2020709689:6756"
NUMBER_WORKER_THREADS = 7
GAME_VERSION = GAME_VERSION_1_12_2
PAGE_QUEUE = queue.Queue()
RESULTS = queue.Queue()


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
# TODO - maybe - get web content async (and possibly cache it too!)

class ModRecord:
	...


def worker():
	while True:
		item = PAGE_QUEUE.get()
		if item is None:
			break
		RESULTS.put(get_mod_info_list(item))
		PAGE_QUEUE.task_done()


def main():
	a = time.time()

	threads = []
	for i in range(NUMBER_WORKER_THREADS):
		t = threading.Thread(target=worker)
		t.start()
		threads.append(t)

	for i in range(1, get_number_pages() + 1):
		PAGE_QUEUE.put(i)

	# block until all tasks are done
	PAGE_QUEUE.join()
	# stop workers
	for i in range(NUMBER_WORKER_THREADS):
		PAGE_QUEUE.put(None)
	for t in threads:
		t.join(timeout=10)

	with open("data2", "w") as file:
		while not RESULTS.empty():
			list_ = RESULTS.get()
			for i in list_:
				file.write(i.__repr__() + "\n")
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


def get_mod_info_list(page: int = 1, game_version: str = GAME_VERSION) -> List[ModRecord]:
	ret = []
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
			name = name_tab.string
			name_link = name_tab.get("href")

			author_tab = info_name.span.a
			author = author_tab.string
			author_link = author_tab.get("href")

			# stats
			stats_tab = mod_descriptor.find("div", class_="info stats")
			download_count = stats_tab.find("p", class_="e-download-count").string.replace(",", "")
			updated = stats_tab.find("p", class_="e-update-date").abbr.get("data-epoch")

			# description
			description = mod_descriptor.find("div", class_="description").p.string

			modrecord = ModRecord(name, name_link, author, author_link, download_count, updated, description)
			scrape_mod_page(modrecord)

			ret.append(modrecord)
	return ret


def scrape_mod_page(mod_record: ModRecord):
	print("scraping", mod_record._name)
	with request.urlopen(CURSEFORGE_HOME + mod_record._name_link) as page:
		raw_content = BeautifulSoup(page.read(), "lxml")
		for header in raw_content.find("ul", class_="e-menu").find_all("a", class_="external-link"):
			s = header.string.strip().lower()
			link = header.get("href").strip()
			if s == "source":
				mod_record.set_source_link(link)
			elif s == "wiki":
				mod_record.set_wiki_link(link)
			elif s == "issues":
				mod_record.set_issues_link(link)
			else:
				pass

		license_stuff = raw_content.find("ul", class_="cf-details project-details").find("a")
		mod_record.set_license_link(license_stuff.get("href"))
		mod_record.set_license(license_stuff.string.strip() if license_stuff.string is not None else None)


class ModRecord:
	__slots__ = ("_name",
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
		ret += self._name + " "
		ret += self._name_link + " "
		ret += self._author + " "
		ret += self._author_link + " "
		ret += self._download_count + " "
		ret += self._updated + " "
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

	def set_license(self, license):
		self._license = license

	def project_url(self) -> str:
		return CURSEFORGE_HOME + self._name_link


if __name__ == "__main__":
	main()
