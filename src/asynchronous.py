import logging
from asyncio import Future
from typing import Iterable, List, Tuple, Optional

import aiohttp
import asyncio

from download import HEADERS


# this logs errors on failure. I think this is related to https://bugs.python.org/issue37035
async def fetch(session: aiohttp.ClientSession, url: str) -> Optional[bytes]:
	# TODO - protect against ClientConnectionError
	async with session.get(url) as response:
		logging.debug("downloading: %s", url)
		if response.status >= 400:
			logging.error(f"bad response {response.status} for url {url}")
			return None
		return await response.read()

# def download(url: str) -> bytes:
# 	logging.debug("downloading: %s", url)
# 	tries = 0
# 	while tries < TRIES:
# 		try:
# 			with request.urlopen(request.Request(url, headers=HEADERS), timeout=TIMEOUT) as page:
# 				try:
# 					return page.read()
# 				except Exception as e:
# 					logging.warning(e.__repr__())
# 		except urllib.error.HTTPError or socket.timeout as e:
# 			logging.error(e.__repr__(), url)
#
# 		tries += 1
# 	logging.error("page %s timed out too many times", url)
# 	raise Exception("Page timed out too many times")


# type annotation weird due to https://github.com/python/typing/issues/446 I think
# TODO - is it possible to add accept encoding gzip to improve download times?
async def main(*args: str) -> 'Future[Tuple[bytes, ...]]':  # I think this is the correct type...
	# TODO - supply timeout and use multiple try approach in fetch as above (commented)
	async with aiohttp.ClientSession(headers=HEADERS) as session:
		tasks = [fetch(session, arg) for arg in args]

		return await asyncio.gather(*tasks)


def run(urls: Iterable[str]) -> List[Optional[bytes]]:
	task = main(*urls)
	return asyncio.run(task)
