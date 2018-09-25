import sqlite3
from configuration import CONFIG


# TODO - generator for this?
class DB:

	def __init__(self):
		self.conn = sqlite3.connect(CONFIG.get("db_location"))
		self.cur = self.conn.cursor()

	def close(self):
		self.conn.commit()
		self.cur.close()
		self.conn.close()

	def create(self):
		self.cur.execute("""CREATE TABLE 
		IF NOT EXISTS 
			mods 
			(
			id INTEGER PRIMARY KEY, 
			accessed INTEGER, 
			link_extension TEXT, 
			source TEXT, 
			issues TEXT, 
			wiki TEXT, 
			license_link TEXT, 
			license TEXT
			)""")
		return self

	# upsert? insert or ignore?
	def update_or_create(self, mod_record):
		self.cur.execute("DELETE FROM mods WHERE id = ?", (mod_record.get_project_id(),))  # does this cause performance issues?
		self.cur.execute("INSERT INTO mods VALUES (?,?,?,?,?,?,?,?)", mod_record.as_tuple())   # TODO - replace rather than delete to allow only certain things to be recached

	def get_cache_info(self, name_link):
		return self.cur.execute("SELECT id, accessed FROM mods WHERE link_extension=? LIMIT 1", (name_link,)).fetchone()
