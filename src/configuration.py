import configparser
import os
from pathlib import Path


def absolute_path(relative_path):
	return os.path.dirname(os.path.abspath(__file__)) + "/" + relative_path


CONFIG_FILE = absolute_path("/../config.ini")


class Config:  # In theory these could be a dict but setting/accessing things globally in python is rather messy

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

		config["cache"] = {
			"# zero or less means no timeout": None,
			"timeout": 3600
		}

		config["curseforge"] = {  # TODO - support for games other than minecraft?
			"# can be found in curseforge url for mods listing": None,
			"game version": "2020709689:6756"
		}

		config["db"] = {
			"# relative to the source files": None,
			"location": "/../mods.db"
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

		cache = config["cache"]
		self.values["cache_timeout"] = int(cache["timeout"])

		curseforge = config["curseforge"]
		self.values["game_version"] = curseforge["game version"]

		db = config["db"]
		self.values["db_location"] = absolute_path(db["location"])

	def get(self, param):
		return self.values[param]

	def __repr__(self):
		return self.values.__repr__()


# instance of the config to use
CONFIG = Config()
