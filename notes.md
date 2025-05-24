- menu dynamic plugin installation+flags (needs uv)
    - Parse valid serializable types
    - Error, when resetting the the str input (empty) still shows that it changed

# features
- some form of result viewer
    - for plugins (https://github.com/pytest-dev/pytest/blob/main/scripts/update-plugin-list.py)
    - general overview
- command preview + builder
- tox-like multi python-version testing
- Improve Filtering/numbers
- Make buttons functional to stop test runs

# generals
- test strategy

# optionals
- align result Icons better on test tree
- using something like watchfiles to detect filechanges and
update the test_tree accordingly (or just stick with a manual refresh)

# fixes
- fix display of skip reason after reset
