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
CURSEFORGE_URL = CURSEFORGE_HOME+"/mc-mods?%s"
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
# UPDATE 15/8/18: pages for mod lists are now gotten in parallel, it's much faster
# TODO - get more info: project id, source, issues, wiki, license, created, recent files? if I can get enough for maven that would be very nice
# use pycurl or even shell for better performance?
# logging
# move to database (sqlite)


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
	c = time.time()
	# stop workers
	for i in range(NUMBER_WORKER_THREADS):
		PAGE_QUEUE.put(None)
	for t in threads:
		t.join()

	with open("data2", "w") as file:
		while not RESULTS.empty():
			list_ = RESULTS.get()
			for i in list_:
				file.write(i.__repr__() + "\n")
			RESULTS.task_done()

	print("took:", time.time() - a)


def get_url(game_version: str = GAME_VERSION, page: int = 1) -> str:
	return CURSEFORGE_URL % parse.urlencode({"filter-game-version": game_version, "page": page})


def get_number_pages(game_version: str = GAME_VERSION) -> int:      # curseforge gives us mobile stuff here
	highest = 0
	with request.urlopen(get_url(game_version)) as page:
		page_list = BeautifulSoup(page.read(), "lxml").find(class_="b-pagination-list paging-list j-tablesorter-pager j-listing-pagination")
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
	print(str(page) + " " + str(threading.get_ident()))
	with request.urlopen(get_url(game_version, page)) as url:
		raw_content = BeautifulSoup(url.read(), "lxml")
		ul = raw_content.find(class_="listing listing-project project-listing")
		for li in ul.children:
			if isinstance(li, NavigableString):
				continue
			mod_descriptor = li.find(class_="details")

			# name and author
			info_name = mod_descriptor.find(class_="info name")

			name_tab = info_name.div.a
			name = name_tab.string
			name_link = name_tab.get("href")

			author_tab = info_name.span.a
			author = author_tab.string
			author_link = author_tab.get("href")

			# stats
			stats_tab = mod_descriptor.find(class_="info stats")
			download_count = stats_tab.find(class_="e-download-count").string.replace(",", "")
			updated = stats_tab.find(class_="e-update-date").abbr.get("data-epoch")

			# description
			description = mod_descriptor.find(class_="description").p.string

			modrecord = ModRecord(name, name_link, author, author_link, download_count, updated, description)
			# TODO - here would be where to call to get the page etc. Can then push to the queue from there hopefully

			ret.append(modrecord)

	return ret


class ModRecord:
	def __init__(self, name: str, name_link: str, author: str, author_link: str, download_count: int, updated: int, description: str):
		self.name = name
		self.name_link = name_link
		self.author = author
		self.author_link = author_link
		self.download_count = download_count
		self.updated = updated
		self.description = description

	def __repr__(self) -> str:
		return self.name + " " + self.name_link + " " + self.author + " " + self.author_link + " " + self.download_count + " " + self.updated + " " + self.description

	def project_url(self) -> str:
		return CURSEFORGE_HOME + self.name_link


if __name__ == '__main__':
	main()
