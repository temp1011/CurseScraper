# this is the thing that starts everything
import concurrent.futures
import multiprocessing
import time
import threading

from new_src import downloads_all, parse_all

NUMBER_DOWNLOADER_THREADS = 30
NUMBER_PARSER_PROCESSES = 7


# def main():             # maybe I should just immediately move to cache based model...
# 	a = time.time()     # but startup should still be reasonable fast...
#
# 	downloads_all.init_input_queue()
#
# 	threads = []
# 	for i in range(NUMBER_DOWNLOADER_THREADS):
# 		t = threading.Thread(target=downloads_all.worker)
# 		t.start()
# 		threads.append(t)
# 	downloads_all.INPUTS.join()
# 	downloads_all.TO_PROCESS.join()
# 	for i in range(NUMBER_DOWNLOADER_THREADS):
# 		downloads_all.TO_PROCESS.put(None)
# 	for t in threads:
# 		t.join()
# 	print("everything has finished downloading!")
#
# 	processes = []
# 	for i in range(NUMBER_PARSER_PROCESSES):
# 		p = multiprocessing.Process(target=parse_all.scrape_file_in_results, args=(parse_all.inputs,))
# 		p.start()
# 		processes.append(p)
#
# 	parse_all.inputs.join()     # processes should close themselves if queue is empty
# 	print("all inputs used")
# 	for p in processes:
# 		p.join()
#
# 	print("finished parsing, IO time")
#
# 	print("took:", time.time() - a)

def main():
	a = time.time()

	b = downloads_all.init_input_queue()
	print("found", len(b), "mods to use")
	downloads_all.scrape_results(b)
	print(time.time() - a)
















if __name__ == "__main__":
	main()