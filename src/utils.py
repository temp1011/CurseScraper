import os


def relative_path(p: str) -> str:
	dirname = os.path.dirname(__file__)
	return os.path.join(dirname, p)
