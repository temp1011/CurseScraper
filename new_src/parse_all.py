# parse the html to get the data out
import multiprocessing
from bs4 import BeautifulSoup
from new_src import downloads_all

results = multiprocessing.JoinableQueue()
inputs = multiprocessing.JoinableQueue()


def scrape_file_in_results(raw):
	raw_content = BeautifulSoup(raw, "lxml")
	ret = downloads_all.ModRecord("", "", "", "", 0, 0, "")
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
	ret.set_project_id(int(side_bar.contents[1].contents[3].string))    # TODO - try and make this a little less order dependant
