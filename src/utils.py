import os
from urllib import parse

import configuration


def relative_path(p: str) -> str:
	dirname = os.path.dirname(__file__)
	dirname = os.path.join(dirname, "..")
	return os.path.join(dirname, p)


def get_content_url(ext: str) -> str:
	return CURSEFORGE_HOME + ext


def get_listing_url(game_version: str = "", page: int = 1) -> str:
	if len(game_version) == 0:
		import configuration
		game_version = configuration.GAME_VERSION
	return CURSEFORGE_URL % parse.urlencode({"filter-game-version": game_version, "page": page})


CURSEFORGE_HOME = "https://www.curseforge.com"
CURSEFORGE_URL = CURSEFORGE_HOME + "/minecraft/mc-mods?%s"
