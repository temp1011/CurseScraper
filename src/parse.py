from bs4 import BeautifulSoup

from database import DB
from download import download, ModRecord, get_content_url
from bs4.element import NavigableString
from configuration import CONFIG
import logging
import time


def get_number_pages(raw_bytes) -> int:
	# requests seems to return the mobile/no js layout here
	page_list = BeautifulSoup(raw_bytes, "lxml").find(
		class_="pagination pagination-top flex items-center")

	link_classes = page_list.find_all("a", class_="pagination-item")
	highest = max([int(l.span.string) for l in link_classes])

	return highest


# TODO - separate caching logic from this
def get_project_links(url: str):
	raw_content = BeautifulSoup(download(url), "lxml")

	logging.debug("page %s", url)

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


# TODO - should split up downloading part of this
def scrape_result(ext):
	url = get_content_url(ext)
	raw_bytes = download(url)

	raw_content = BeautifulSoup(raw_bytes, "lxml")
	ret = ModRecord()
	link_bar = raw_content.find("nav", class_="container mx-auto").ul
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
		else:
			pass

	sidebar_text = raw_content.find("div", class_="flex flex-col mb-3")
	# print(sidebar_text.prettify())
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

	ret.set_name_link(ext)
	return ret
