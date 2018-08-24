# parse the html to get the data out
import multiprocessing
from bs4 import BeautifulSoup
import downloads_all

results = multiprocessing.JoinableQueue()
inputs = multiprocessing.JoinableQueue()


def scrape_file_in_results(raw, ext):   # TODO - include accessed variable (epoch seconds maybe?) for caching
	raw_content = BeautifulSoup(raw, "lxml")
	ret = downloads_all.ModRecord()
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
	ret.set_license(license_stuff.string.strip() if license_stuff.string is not None else None) # TODO - there can be a a link here, find that too. eg - see https://minecraft.curseforge.com/projects/default-lan-port which has a span inside
	ret.set_project_id(int(side_bar.contents[1].contents[3].string))    # TODO - try and make this a little less order dependant
	ret.set_name_link(ext)
	return ret
