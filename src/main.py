import concurrent.futures
import sys
from logging import handlers
from typing import List

import database
from download import *
from parse import get_number_pages, get_project_links, needs_refresh, fetch_and_scrape


def main():
	setup_logging()
	start = time.time()

	with database.DB() as db:
		found_links = init_page_queue(CONFIG.get("scanner_processes"))
		found_links = list(filter(needs_refresh, found_links))
		found_links = found_links[:CONFIG.get("max_search")]
		logging.info("found {} mods to use".format(len(found_links)))

		scraped_data = scrape_results(found_links, CONFIG.get("scraper_processes"))
		if len(scraped_data) > 0:
			logging.debug("everything scraped")
		for mod_record in scraped_data:
			db.update_or_create(mod_record)

	logging.info("completed in: {}".format(time.time() - start))


def init_page_queue(number_downloader_threads: int = 1) -> List[str]:
	ret = []
	number_pages = get_number_pages(download(get_listing_url()))
	with concurrent.futures.ProcessPoolExecutor(max_workers=number_downloader_threads) as executor:
		project_ids = {
			executor.submit(get_project_links,
			                get_listing_url(GAME_VERSION, i)):
				i for i in range(1, number_pages + 1)
		}
		for future in concurrent.futures.as_completed(project_ids):
			ret.extend(future.result())
	return ret


def scrape_results(exts: List[str], number_parser_processes: int) -> List[ModRecord]:
	ret = []
	with concurrent.futures.ProcessPoolExecutor(max_workers=number_parser_processes) as executor:
		pages = {executor.submit(fetch_and_scrape, i): i for i in exts}
		for future in concurrent.futures.as_completed(pages):
			f = future.result()
			if f is not None:
				ret.append(f)
	return ret


def setup_logging():
	logging.getLogger()
	loghandlers = [logging.handlers.RotatingFileHandler(CONFIG.get("log_location"), mode="w")]
	if CONFIG.get("log_use_stdout"):
		loghandlers.append(logging.StreamHandler(sys.stdout))
	logging.basicConfig(
		format="%(asctime)s [%(processName)-14.14s] [%(levelname)-7.7s]  %(message)s",
		level=getattr(logging, CONFIG.get("log_level").upper(), None),
		handlers=loghandlers
	)
	logging.debug("Initialised!")


if __name__ == "__main__":
	main()
