from __future__ import annotations

# from collections.abc import Iterator
# import datetime

# import pathlib
import re

# from textwrap import dedent
# from textwrap import indent
# from typing import Any
from typing import TypedDict

# import packaging.version
import platformdirs
from requests_cache import CachedResponse
from requests_cache import CachedSession
from requests_cache import OriginalResponse
from requests_cache import SQLiteCache

DEVELOPMENT_STATUS_CLASSIFIERS = (
    "Development Status :: 1 - Planning",
    "Development Status :: 2 - Pre-Alpha",
    "Development Status :: 3 - Alpha",
    "Development Status :: 4 - Beta",
    "Development Status :: 5 - Production/Stable",
    "Development Status :: 6 - Mature",
    "Development Status :: 7 - Inactive",
)
ADDITIONAL_PROJECTS = {  # set of additional projects to consider as plugins
    "logassert",
    "logot",
    "nuts",
    "flask_fixture",
    "databricks-labs-pytester",
    "tursu",
}


def _escape_rst(text: str) -> str:
    """Rudimentary attempt to escape special RST characters to appear as
    plain text."""
    text = (
        text.replace("*", "\\*")
        .replace("<", "\\<")
        .replace(">", "\\>")
        .replace("`", "\\`")
    )
    text = re.sub(r"_\b", "", text)
    return text


def _project_response_with_refresh(
    session: CachedSession, name: str, last_serial: int
) -> OriginalResponse | CachedResponse:
    """Get a http cached pypi project

    force refresh in case of last serial mismatch
    """
    response = session.get(f"https://pypi.org/pypi/{name}/json")
    if int(response.headers.get("X-PyPI-Last-Serial", -1)) != last_serial:
        response = session.get(f"https://pypi.org/pypi/{name}/json", refresh=True)
    return response


def _get_session() -> CachedSession:
    """Configures the requests-cache session"""
    cache_path = platformdirs.user_cache_path("pytest-plugin-list")
    cache_path.mkdir(exist_ok=True, parents=True)
    cache_file = cache_path.joinpath("http_cache.sqlite3")
    return CachedSession(backend=SQLiteCache(cache_file))


def _pytest_plugin_projects_from_pypi(session: CachedSession) -> dict[str, int]:
    response = session.get(
        "https://pypi.org/simple",
        headers={"Accept": "application/vnd.pypi.simple.v1+json"},
        refresh=True,
    )
    return {
        name: p["_last-serial"]
        for p in response.json()["projects"]
        if (
            (name := p["name"]).startswith(("pytest-", "pytest_"))
            or name in ADDITIONAL_PROJECTS
        )
    }


class PluginInfo(TypedDict):
    """Relevant information about a plugin to generate the summary."""

    name: str
    summary: str
    last_release: str
    status: str
    requires: str


# async def get_plugin_list() -> dict[str, int]:
async def get_plugin_list() -> list[str]:
    session = _get_session()
    name_2_serial = _pytest_plugin_projects_from_pypi(session)
    return list(name_2_serial.keys())


# def iter_plugins() -> Iterator[PluginInfo]:
#     session = _get_session()
#     name_2_serial = _pytest_plugin_projects_from_pypi(session)
#
#
#     # for name, last_serial in tqdm(name_2_serial.items(), smoothing=0):
#     for name, last_serial in name_2_serial.items():
#         response = _project_response_with_refresh(session, name, last_serial)
#         if response.status_code == 404:
#             # Some packages, like pytest-azurepipelines42, are included in https://pypi.org/simple
#             # but return 404 on the JSON API. Skip.
#             continue
#         response.raise_for_status()
#         info = response.json()["info"]
#         if "Development Status :: 7 - Inactive" in info["classifiers"]:
#             continue
#         for classifier in DEVELOPMENT_STATUS_CLASSIFIERS:
#             if classifier in info["classifiers"]:
#                 status = classifier[22:]
#                 break
#         else:
#             status = "N/A"
#         requires = "N/A"
#         if info["requires_dist"]:
#             for requirement in info["requires_dist"]:
#                 if re.match(r"pytest(?![-.\w])", requirement):
#                     requires = requirement
#                     break
#
#         def version_sort_key(version_string: str) -> Any:
#             """
#             Return the sort key for the given version string
#             returned by the API.
#             """
#             try:
#                 return packaging.version.parse(version_string)
#             except packaging.version.InvalidVersion:
#                 # Use a hard-coded pre-release version.
#                 return packaging.version.Version("0.0.0alpha")
#
#         releases = response.json()["releases"]
#         for release in sorted(releases, key=version_sort_key, reverse=True):
#             if releases[release]:
#                 release_date = datetime.date.fromisoformat(
#                     releases[release][-1]["upload_time_iso_8601"].split("T")[0]
#                 )
#                 last_release = release_date.strftime("%b %d, %Y")
#                 break
#         name = f":pypi:`{info['name']}`"
#         summary = ""
#         if info["summary"]:
#             summary = _escape_rst(info["summary"].replace("\n", ""))
#         yield {
#             "name": name,
#             "summary": summary.strip(),
#             "last_release": last_release,
#             "status": status,
#             "requires": requires,
#         }
