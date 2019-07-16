import os


def relative_path(p: str) -> str:
	dirname = os.path.dirname(__file__)
	dirname = os.path.join(dirname, "..")
	return os.path.join(dirname, p)
