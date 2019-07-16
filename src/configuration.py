import configparser
import multiprocessing
from pathlib import Path
import sys


from utils import relative_path


CONFIG_FILE = relative_path("config.ini")


class Config:
	# In theory this could be a dict but setting/accessing things globally in python is rather messy
	# better to follow OOP and encapsulate everything

	def __init__(self):
		self.values = {}
		if Path(CONFIG_FILE).is_file():
			self.read_config()
			return
		config = configparser.ConfigParser(allow_no_value=True)
		# TODO - now that we use asynchronous downloads default these to the number of cpus available on the system
		# and only have a parsing thread count, but include a semaphore for the async stuff to avoid overloading
		# the server
		config["processes"] = {
			"# 0 or less defaults to number of cpus on the system": None,
			"parsing": -1
		}

		config["curseforge"] = {  # TODO - support for games other than minecraft?
			"# can be found in curseforge url for mods listing": None,
			"game version": "2020709689:6756"
		}

		config["db"] = {
			"# relative to the source files": None,
			"location": "mods.db",
			"# zero or less means no timeout": None,
			"timeout": 3600
		}

		config["logging"] = {
			"location": "scraper.log",
			"print to stdout": True,
			"log level": "debug"
		}

		config["rate_limiting"] = {
			"# use to only update a portion of the database at once so that the server ": None,
			"# doesn't start returning Http Error 500. 0 or lower will give 'infinite' number": None,
			"max search": 1000
		}
		with open(CONFIG_FILE, "w") as configfile:
			config.write(configfile)
		self.read_config()

	def read_config(self):
		config = configparser.ConfigParser(allow_no_value=True)
		config.read(CONFIG_FILE)

		processes = config["processes"]
		num_proc = int(processes["parsing"])
		self.values["parser_processes"] = num_proc if num_proc > 0 else multiprocessing.cpu_count()

		curseforge = config["curseforge"]
		self.values["game_version"] = curseforge["game version"]

		db = config["db"]
		self.values["db_location"] = relative_path(db["location"])
		self.values["cache_timeout"] = int(db["timeout"])

		log = config["logging"]
		self.values["log_location"] = relative_path(log["location"])
		self.values["log_use_stdout"] = log["print to stdout"]
		self.values["log_level"] = log["log level"]

		rate_limiting = config["rate_limiting"]
		max_search = int(rate_limiting["max search"])
		self.values["max_search"] = max_search if max_search > 0 else sys.maxsize

	def get(self, param):
		return self.values[param]

	def __repr__(self):
		return self.values.__repr__()


# instance
CONFIG = Config()

GAME_VERSION = CONFIG.get("game_version")