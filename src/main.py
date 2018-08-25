import time
import sqlite3
import sys
from configuration import CONFIG
import downloads_all


# TODO - config improvements, logging
# configs - number of processes for both, whether to download or load from disk, game version, cache timeout (or not)
def main():
	start = time.time()
	conn = sqlite3.connect(CONFIG.get("db_location"))
	c = conn.cursor()
	c.execute("""CREATE TABLE IF NOT EXISTS mods 
		(id INTEGER PRIMARY KEY, accessed INTEGER, link_extension TEXT, 
		source TEXT, issues TEXT, wiki TEXT, license_link TEXT, license TEXT)""")
	found_links = downloads_all.init_input_queue(CONFIG.get("scanner_processes"))
	print("found", len(found_links), "mods to use")
	scraped_data = downloads_all.scrape_results(found_links, CONFIG.get("scraper_processes"))
	print("everything scraped")
	for mod_record in scraped_data:
		c.execute("DELETE FROM mods WHERE id = ?", (mod_record.get_project_id(),))  # does this cause performance issues?
		c.execute("INSERT INTO mods VALUES (?,?,?,?,?,?,?,?)", mod_record.as_tuple())   # TODO - replace rather than delete to allow only certain things to be recached
	conn.commit()
	c.close()
	conn.close()
	print("completed in: ", time.time() - start)


if __name__ == "__main__":
	print(sys.getrecursionlimit())
	# sys.setrecursionlimit(1500)   # TODO - possible crash here due to recursion limit reached (rewrite iteratively if at all possible)
	main()                          # could do something like only run half at once
									# or only add to the queue when it is empty enough
									# beautifulsoup and queue give a very large recursion issue
									# would be nice of python did tail optimisation
									# likely reproduction conditions: small number of workers (?), stable internet with no timeouts, fresh install