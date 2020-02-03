from github_asset import get_repo, get
import os


def test_get_repo():
    assert get_repo() == "tamuhey/github_asset"


def test_get_file():
    fname = "foo.txt"
    if os.path.exists(fname):
        os.remove(fname)
    get(fname)
    assert os.path.exists(fname)
    os.remove(fname)

