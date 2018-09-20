from bs4 import BeautifulSoup
from downloads_all import download, ModRecord
from bs4.element import NavigableString
import sqlite3
from configuration import CONFIG
import logging
import time


def get_number_pages(raw_bytes) -> int:  # curseforge gives us mobile stuff here
	highest = 0
	page_list = BeautifulSoup(raw_bytes, "lxml").find(
		class_="b-pagination-list paging-list j-tablesorter-pager j-listing-pagination")
	for li in page_list.children:
		if isinstance(li, NavigableString):
			continue

		link_class = li.find("a")
		if link_class is not None:
			link = link_class.get("href")
			if link is not None:
				page_number = int(link.split("page")[1].replace("=", ""))
				highest = max(page_number, highest)

	return highest


def get_project_links(url: str):
	raw_content = BeautifulSoup(download(url), "lxml")

	connection = sqlite3.connect(CONFIG.get("db_location"))
	cursor = connection.cursor()
	logging.debug("page %s", url)
	foundIDs = []
	ul = raw_content.find("ul", class_="listing listing-project project-listing")
	for li in ul.children:
		if isinstance(li, NavigableString):
			continue
		mod_descriptor = li.find("div", class_="details")

		info_name = mod_descriptor.find("div", class_="info name")

		name_tab = info_name.div.a
		name_link = name_tab.get("href")
		found_link = cursor.execute("SELECT id, accessed FROM mods WHERE link_extension=? LIMIT 1", (name_link,)).fetchone()

		if not found_link:
			foundIDs.append(name_link)
			logging.debug("added mod %s" % name_link)
		else:
			if int(time.time()) - found_link[1] > CONFIG.get("cache_timeout"):
				logging.debug("cache expired on %s" % name_link)
				foundIDs.append(name_link)
			else:
				logging.debug("ignoring ID already in db %d" % found_link[0])
	cursor.close()
	connection.close()
	return foundIDs


def scrape_result(url, ext):
	raw_bytes = download(url)

	raw_content = BeautifulSoup(raw_bytes, "lxml")
	ret = ModRecord()
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
	ret.set_license(get_license_string(license_stuff))
	ret.set_project_id(int(side_bar.contents[1].contents[3].string))  # TODO - try and make this a little less order dependant
	ret.set_name_link(ext)
	return ret


def get_license_string(license_stuff):
	if license_stuff.string:
		return license_stuff.string.strip()
	else:
		return license_stuff.span.get("title")
