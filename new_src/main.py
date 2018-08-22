import time
import sqlite3

from new_src import downloads_all

NUMBER_DOWNLOADER_THREADS = 179
NUMBER_PARSER_PROCESSES = 30


def main():
	a = time.time()
	print(a)
	conn = sqlite3.connect("mods.db")
	c = conn.cursor()
	c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mods';")
	if c.fetchone() is None:
		c.execute("""CREATE TABLE mods 
		(id INTEGER, accessed INTEGER, link_extension TEXT, 
		source TEXT, issues TEXT, wiki TEXT, license_link TEXT, license TEXT)""")

	b = downloads_all.init_input_queue(NUMBER_DOWNLOADER_THREADS)
	print("found", len(b), "mods to use")
	d = downloads_all.scrape_results(b, NUMBER_PARSER_PROCESSES)
	print("everything scraped")
	for mod_record in d:
		c.execute("INSERT INTO mods VALUES (?,?,?,?,?,?,?,?)", mod_record.as_tuple())
	conn.commit()
	c.close()
	print(time.time() - a)


if __name__ == "__main__":
	main()