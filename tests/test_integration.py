import asyncio
from types import MappingProxyType

import pytest
from collections import defaultdict

from ..plugin_loader import main
from ..requirement_resolver import add_entries, update_pending_requirements, resolve_version_conflicts
from ..util import list_plugins, Plugin


def setup():
    add_entries(list_plugins())


@pytest.fixture(scope='module')
def pending_requirements_setup(request):

    pending_requirements = defaultdict(list)
    for p in list_plugins():
        update_pending_requirements(Plugin(p).name, pending_requirements)
    return pending_requirements


@pytest.fixture(scope='function')
def status_requirements_setup(request):
    return MappingProxyType({
        'safe': defaultdict(list),
        'attention': defaultdict(list),
        'conflict': defaultdict(list)
    })


def test_critical(pending_requirements_setup, status_requirements_setup):
    resolve_version_conflicts(pending_requirements_setup, status_requirements_setup)
    assert not status_requirements_setup['conflict'], 'Conflicts during version compatibility check'


def test_attention(pending_requirements_setup, status_requirements_setup):
    resolve_version_conflicts(pending_requirements_setup, status_requirements_setup)
    assert not status_requirements_setup['attention'], f"Some requirements need attention: {status_requirements_setup['attention']}"


def test_plugin_download():
    import subprocess
    plugins_to_download = set()
    plugins_to_update = set()
    plugins_local = set(list_plugins())
    tasks = []

    http_server = subprocess.Popen(args=['python', '-m', 'http.server', '--directory', './source'], stdout=subprocess.PIPE)
    try:
        asyncio.run(main(plugins_local, plugins_to_download, plugins_to_update, tasks))
    finally:
        http_server.terminate()
        pass

    l1 = len(set(list_plugins()))
    l2 = len(plugins_local) + len(plugins_to_download)

    import shutil
    for i in plugins_to_download:
        shutil.rmtree(i.path.absolute(), ignore_errors=True)

    assert l1 == l2


