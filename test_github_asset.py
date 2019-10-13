from github_asset import get_repo


def test_get_repo():
    assert get_repo() == "tamuhey/github_asset"
