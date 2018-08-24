import time
import sqlite3

import downloads_all

NUMBER_DOWNLOADER_PROCESSES = 10
NUMBER_PARSER_PROCESSES = 30
CACHE_TIMEOUT = 60 * 30     # for testing, a 30 minute cache timeout should be good


# TODO - config, logging, running from a terminal
# configs - number of processes for both, whether to download or load from disk, game version, cache timeout (or not)
def main():
	start = time.time()
	conn = sqlite3.connect("../mods.db")
	c = conn.cursor()
	c.execute("""CREATE TABLE IF NOT EXISTS mods 
		(id INTEGER PRIMARY KEY, accessed INTEGER, link_extension TEXT, 
		source TEXT, issues TEXT, wiki TEXT, license_link TEXT, license TEXT)""")
	found_links = downloads_all.init_input_queue(NUMBER_DOWNLOADER_PROCESSES)
	print("found", len(found_links), "mods to use")
	scraped_data = downloads_all.scrape_results(found_links, NUMBER_PARSER_PROCESSES)
	print("everything scraped")
	for mod_record in scraped_data:
		c.execute("DELETE FROM mods WHERE id = ?", (mod_record.get_project_id(),))  # does this cause performance issues?
		c.execute("INSERT INTO mods VALUES (?,?,?,?,?,?,?,?)", mod_record.as_tuple())
	conn.commit()
	c.close()
	conn.close()
	print("completed in: ", time.time() - start)


if __name__ == "__main__":
	main()
