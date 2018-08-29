import time
import sqlite3
import sys
from configuration import CONFIG
import downloads_all
import logging
from logging import handlers


# TODO - config improvements, logging
# configs - number of processes for both, whether to download or load from disk, game version, cache timeout (or not)
def main():
	setup_logging()
	start = time.time()
	conn = sqlite3.connect(CONFIG.get("db_location"))
	c = conn.cursor()
	c.execute("""CREATE TABLE IF NOT EXISTS mods 
		(id INTEGER PRIMARY KEY, accessed INTEGER, link_extension TEXT, 
		source TEXT, issues TEXT, wiki TEXT, license_link TEXT, license TEXT)""")
	found_links = downloads_all.init_input_queue(CONFIG.get("scanner_processes"))
	logging.info("found {} mods to use".format(len(found_links)))
	scraped_data = downloads_all.scrape_results(found_links, CONFIG.get("scraper_processes"))
	if len(scraped_data) > 0:
		logging.debug("everything scraped")
	for mod_record in scraped_data:
		c.execute("DELETE FROM mods WHERE id = ?", (mod_record.get_project_id(),))  # does this cause performance issues?
		c.execute("INSERT INTO mods VALUES (?,?,?,?,?,?,?,?)", mod_record.as_tuple())   # TODO - replace rather than delete to allow only certain things to be recached
	conn.commit()
	c.close()
	conn.close()
	logging.info("completed in: {}".format(time.time() - start))


def setup_logging():
	logging.getLogger()
	loghandlers = [	logging.handlers.RotatingFileHandler(CONFIG.get("log_location"), mode="w")]
	if CONFIG.get("log_use_stdout"):
		loghandlers.append(logging.StreamHandler(sys.stdout))
	logging.basicConfig(
		format="%(asctime)s [%(processName)-12.12s] [%(levelname)-7.7s]  %(message)s",
		level=getattr(logging, CONFIG.get("log_level").upper(), None),
		handlers=loghandlers
	)
	logging.debug("Initialised!")
	logging.debug("recursion limit is %d", sys.getrecursionlimit())


if __name__ == "__main__":
	# sys.setrecursionlimit(1500)   # TODO - possible crash here due to recursion limit reached (rewrite iteratively if at all possible)
	main()                          # could do something like only run half at once
									# or only add to the queue when it is empty enough
									# beautifulsoup and queue give a very large recursion issue
									# would be nice of python did tail optimisation
									# likely reproduction conditions: small number of workers (?), stable internet with no timeouts, fresh install
