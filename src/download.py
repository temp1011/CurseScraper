import time
from urllib import request, parse
from configuration import CONFIG
import logging

CURSEFORGE_HOME = "https://minecraft.curseforge.com"
CURSEFORGE_URL = CURSEFORGE_HOME + "/mc-mods?%s"
# from python docs: https://docs.python.org/3.4/library/urllib.request.html#urllib.request.Request
HEADERS = {
	"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"
}

GAME_VERSION = CONFIG.get("game_version")
TIMEOUT = CONFIG.get("download_timeout")
TRIES = CONFIG.get("download_tries")


def get_listing_url(game_version: str = GAME_VERSION, page: int = 1) -> str:
	return CURSEFORGE_URL % parse.urlencode({"filter-game-version": game_version, "page": page})


def get_content_url(ext: str):
	return CURSEFORGE_HOME + ext


def download(url: str):
	logging.debug("downloading: %s", url)
	tries = 0
	while tries < TRIES:
		with request.urlopen(request.Request(url, headers=HEADERS), timeout=TIMEOUT) as page:
			try:
				return page.read()
			except Exception as e:
				logging.warning(e.__repr__())
		tries += 1
	logging.error("page %s timed out too many times", url)
	raise Exception("Page timed out too many times")


# could use tuple/dict here but this is safer (and not stringly typed!)
class ModRecord:
	__slots__ = ("_project_id",
	             "_wiki_link",
	             "_issues_link",
	             "_source_link",
	             "_name_link",
	             "_license")

	def __init__(self):
		self._project_id = None
		self._wiki_link = None
		self._issues_link = None
		self._source_link = None
		self._license = None
		self._name_link = None

	def __repr__(self) -> str:
		ret = ""
		ret += str(self._name_link) + " "
		ret += str(self._project_id) + " "
		ret += str(self._wiki_link) + " "
		ret += str(self._issues_link) + " "
		ret += str(self._source_link) + " "
		ret += str(self._license)
		return ret

	def set_wiki_link(self, wiki_link):
		self._wiki_link = wiki_link

	def set_issues_link(self, issues_link):
		self._issues_link = issues_link

	def set_source_link(self, source_link):
		self._source_link = source_link

	def set_license(self, lic):
		self._license = lic

	def set_project_id(self, id):
		self._project_id = id

	def set_name_link(self, name_link):
		self._name_link = name_link

	def get_project_id(self):
		return self._project_id

	def test_form(self):    # don't use accessed time for test cases
		return self._project_id, self._name_link, self._source_link, self._issues_link, self._wiki_link, self._license

	def as_tuple(self): # TODO - perhaps there is a better way to do this, also maybe set accessed time?
		return self._project_id, int(time.time()), self._name_link, self._source_link, self._issues_link, self._wiki_link, self._license
