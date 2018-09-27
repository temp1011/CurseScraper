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
			license TEXT
			)""")
		return self

	def update_or_create(self, mod_record):
		# it doesn't actually matter if the primary key gets replaced since it will be the same
		self.cur.execute("""INSERT OR REPLACE INTO mods
		(id, 
		accessed, 
		link_extension, 
		source, 
		issues, 
		wiki, 
		license)
		VALUES (?, ?, ?, ?, ?, ?, ?)""", mod_record.as_tuple())

	def get_cache_info(self, name_link):
		return self.cur.execute("SELECT id, accessed FROM mods WHERE link_extension=? LIMIT 1", (name_link,)).fetchone()
