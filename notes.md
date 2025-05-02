# features
- some form of result viewer
    - for plugins
    - general overview
- menu dynamic plugin installation+flags (needs uv)
- search by name/tag functionality
- integration of markers/tags
- check if uv is available and project is uv managed (pyproject.toml)

# optionals
- align result Icons better on test tree
- using something like watchfiles to detect filechanges and
update the test_tree accordingly (or just stick with a manual refresh)

# fixes
- fix error if test contains `[/]` Sequence
- fix display of skip reason after reset
