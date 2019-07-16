import logging
import time
from typing import Optional, Set

from bs4 import BeautifulSoup
from bs4.element import NavigableString

from asynchronous import run_single
from configuration import CONFIG
from database import DB
from download import ModRecord, get_content_url


def get_number_pages(raw_bytes: bytes) -> int:
	# requests seems to return the mobile/no js layout here
	page_list = BeautifulSoup(raw_bytes, "lxml").find(
		class_="pagination pagination-top flex items-center")

	link_classes = page_list.find_all("a", class_="pagination-item")
	highest = max([int(l.span.string) for l in link_classes])

	return highest


def fetch_and_get_project_links(url: str) -> Set[str]:
	logging.debug("page %s", url)
	return get_project_links(run_single(url))


def get_project_links(raw: bytes) -> Set[str]:
	raw_content = BeautifulSoup(raw, "lxml")

	classes = raw_content.find_all("div", class_="my-2")
	links = {c.find("a", class_="my-auto").get("href") for c in classes}
	return links


# TODO - probably shouldnt be in this file
def needs_refresh(link: str) -> bool:
	with DB() as db:
		found_link = db.get_cache_info(link)

		if not found_link:
			logging.debug("added mod %s" % link)
			return True
		else:
			if int(time.time()) - found_link[1] > CONFIG.get("cache_timeout"):
				logging.debug("cache expired on %s" % link)
				return True
			else:
				logging.debug("ignoring ID already in db %d" % found_link[0])
				return False


# TODO - maybe this should be moved to a different file
def fetch_and_scrape(ext: str) -> Optional[ModRecord]:
	url = get_content_url(ext)
	try:  # seems to be due to https://www.curseforge.com/minecraft/mc-mods/lan-essentials causing timeouts
		raw_bytes = run_single(url)
	except Exception:
		logging.error("extension {} could not be parsed due to download timeout".format(ext))
		return None

	record = scrape_result(raw_bytes)
	return record


def scrape_result(raw_bytes: bytes) -> Optional[ModRecord]:
	raw_content = BeautifulSoup(raw_bytes, "lxml")
	ret = ModRecord()
	link_bar_outer = raw_content.find("nav", class_="container mx-auto")
	if link_bar_outer is None:  # Seems to be due to internal server error
		logging.error(f"the html was incorrect: {raw_content}")
		return None
	link_bar = link_bar_outer.ul
	for li in link_bar.children:
		if isinstance(li, NavigableString):
			continue
		s = li.get("id")
		link = li.a.get("href")
		if "source" in s:
			ret.set_source_link(link)
		elif "wiki" in s:
			ret.set_wiki_link(link)
		elif "issues" in s:
			ret.set_issues_link(link)
		elif "description" in s:
			ret.set_name_link(link)
		else:
			pass

	sidebar_text = raw_content.find("div", class_="flex flex-col mb-3")
	for div in sidebar_text:
		if isinstance(div, NavigableString):
			continue

		# this is quite ugly...
		# ideally need zip or filter or something...
		counter = 0
		key = None
		for child in div.children:
			if isinstance(child, NavigableString):
				continue
			else:
				if counter == 0:
					key = child.string
					counter += 1
				elif counter == 1:
					if "Project" in key:
						ret.set_project_id(int(child.string))
					if "License" in key.strip():
						ret.set_license(child.string.strip())

	return ret
