# save html. So I can work out multiprocessing more quickly.

from urllib import request, parse
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from typing import List
import queue
import threading
import time
import os
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


"""
stuff to save the html just to make development easier.
"""


class FutureCall:
	def __init__(self, func, *args):
		self._func = func
		self._args = args

	def call(self):
		return self._func(*self._args)

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
	with request.urlopen(CURSEFORGE_HOME + ext) as raw_page:
		INPUTS.put(FutureCall(save_file, raw_page.read(), ext))


def save_file(raw_mod_page: str, ext: str):
	with open(os.getcwd()+"/saved_html/"+ext.replace("/", "").replace("projects", ""), "w") as f:
		f.write(BeautifulSoup(raw_mod_page, "lxml").prettify())



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


if __name__ == "__main__":
	main()
