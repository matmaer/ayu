# general
- has to be a pytest plugin?
- install plugin on the fly?

# pytest-plugin
- intermediate test results for test tree update
- Final report Infos for stats and overview

# textual-app
- Test Tree for overview
    - test node: (refresh symbol) (marker) DIR/DIR::CLASS::TEST (status)
        - status values: queued/running/passed/failed/skipped
        - use `render_label()`
    - markers (fav)
- Final Report Stats Table
- Overview by failed/skipped/passed

# file-watcher
- on file change update app

# event-forwarder
- Socket vs Websocket?
