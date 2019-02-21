# Installation

Installation is best done using `pipenv` and the provided pipfile.

1. Install pipenv by running `pip3 install --user pipenv` or through your distro's repos (eg. Fedora provides it).
2. Install dependencies by running `pipenv install --ignore-pipfile`. You want to use `--ignore-pipfile` to get the exact version of the dependencies that was used for the current release (it will use pipfile.lock rather than pipfile).
3. Run the program with `pipenv run python3 main.py`.

# Developerization

For deving, install with `pipenv install --dev --ignore-pipfile` instead to get whatever development packages may or may not be required.

Dependencies can be updated with `pipenv install` (optionally with --dev). If dependencies are updated, they need to be tested for functionality, after which the new versions can be locked into pipfile.lock with `pipenv lock` (this causes those specific versions to be installed when `--ignore-pipfile` is specified).
