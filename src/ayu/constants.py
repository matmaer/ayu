import os

WEB_SOCKET_HOST = os.environ.get("AYU_HOST") or "localhost"
WEB_SOCKET_PORT = int(os.environ.get("AYU_PORT", 0)) or 1337
MAX_EVENT_SIZE = 2**30
# WEB_SOCKET_HOST = "localhost"
# WEB_SOCKET_PORT = 1337

OUTCOME_SYMBOLS = {
    "PASSED": ":white_check_mark:",
    "FAILED": ":cross_mark:",
    "XFAILED": "[on green]:cross_mark:[/]",
    "SKIPPED": "[on yellow]:next_track_button: [/]",
    "QUEUED": ":hourglass_not_done:",
}

# Some Plugin Options are not really parseable
# with the given approach, e.g. --cov-reset
# which dest is cov_source
# Will look later into that, and disable it for now

OPTIONS_TO_DISABLE = ["--cov-reset"]
