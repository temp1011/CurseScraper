import time

# from python docs: https://docs.python.org/3.4/library/urllib.request.html#urllib.request.Request
HEADERS = {
	"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"
}

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

	def set_project_id(self, i_d):
		self._project_id = i_d

	def set_name_link(self, name_link):
		self._name_link = name_link

	def get_project_id(self):
		return self._project_id

	def test_form(self):  # don't use accessed time for test cases
		return self._project_id, self._name_link, self._source_link, self._issues_link, self._wiki_link, self._license

	def as_tuple(self):  # TODO - perhaps there is a better way to do this, also maybe set accessed time?
		return self._project_id, int(
			time.time()), self._name_link, self._source_link, self._issues_link, self._wiki_link, self._license
