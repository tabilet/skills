import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / '_golden'))
from common import *

archive("C01", "Task storage", head())
register_archives([("C01", "Task storage", head(), "none")], link="tabilet/docs/archive-C01.md")
edit(MEMORY / "product.md", "## Users", "Tasks persist as one JSON file (see archive C01).\n\n## Users")
