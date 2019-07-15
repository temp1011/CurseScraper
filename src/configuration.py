import configparser
import os
import socket
from pathlib import Path
import sys


def absolute_path(relative_path):
	return os.path.dirname(os.path.abspath(__file__)) + "/" + relative_path


CONFIG_FILE = absolute_path("../config.ini")


class Config:
# In theory this could be a dict but setting/accessing things globally in python is rather messy
# better to follow OOP and encapsulate everything

	def __init__(self):
		self.values = {}
		if Path(CONFIG_FILE).is_file():
			self.read_config()
			return
		config = configparser.ConfigParser(allow_no_value=True)
		config["processes"] = {
			"finding content": 10,
			"updating content": 10
		}

		config["downloading"] = {
			"# 0 or less will use default timeout for requests": None,
			"timeout": 10,
			"tries": 5
		}

		config["curseforge"] = {  # TODO - support for games other than minecraft?
			"# can be found in curseforge url for mods listing": None,
			"game version": "2020709689:6756"
		}

		config["db"] = {
			"# relative to the source files": None,
			"location": "../mods.db",
			"# zero or less means no timeout": None,
			"timeout": 3600
		}

		config["logging"] = {
			"location": "../scraper.log",
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
		self.values["scanner_processes"] = int(processes["finding content"])
		self.values["scraper_processes"] = int(processes["updating content"])

		curseforge = config["curseforge"]
		self.values["game_version"] = curseforge["game version"]

		db = config["db"]
		self.values["db_location"] = absolute_path(db["location"])
		self.values["cache_timeout"] = int(db["timeout"])

		log = config["logging"]
		self.values["log_location"] = absolute_path(log["location"])
		self.values["log_use_stdout"] = log["print to stdout"]
		self.values["log_level"] = log["log level"]

		downloading = config["downloading"]
		timeout = int(downloading["timeout"])
		if timeout <= 0:
			timeout = socket._GLOBAL_DEFAULT_TIMEOUT
		self.values["download_timeout"] = timeout
		self.values["download_tries"] = int(downloading["tries"])

		rate_limiting = config["rate_limiting"]
		max_search = int(rate_limiting["max search"])
		self.values["max_search"] = max_search if max_search > 0 else sys.maxsize

	def get(self, param):
		return self.values[param]

	def __repr__(self):
		return self.values.__repr__()


# instance
CONFIG = Config()
