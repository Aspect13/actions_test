import json
import subprocess
import sys
from distutils import log
from functools import partial, cached_property
from pathlib import Path
from typing import Union

import pkg_resources
from pkg_resources import Environment, Requirement
from termcolor import colored


plugin_folder = Path('plugins')
source_folder = Path('source')
repo_file = source_folder.joinpath('plugins.json')
file_host = 'http://localhost:8000'


def cprint(*args, color='cyan'):
    print(' '.join(colored(str(i), color) for i in args))
# cprint = partial(cprint, color='grey', on_color='on_red')


def install(package: Union[Requirement, str], path: Union[Path, str] = None):
    cprint(package, type(package))
    extra_args = ['-t', str(path)] if path else []
    try:
        response = subprocess.check_call([sys.executable, '-m', 'pip', 'install', str(package), *extra_args])
        assert response == 0
    except (subprocess.CalledProcessError, AssertionError):
        log.error(f'Cannot install module {str(package)}')
        return

    dist = pkg_resources.get_distribution(package)

    cprint('response', response, dist)
    return dist


def list_plugins():
    for i in plugin_folder.iterdir():
        yield i.stem


class Plugin:
    package_folder = 'site-packages'
    requirements_file = 'requirements.txt'
    metadata_file = 'metadata.json'

    @classmethod
    def from_source(cls, name, depends_on=None):
        klass = cls(name, depends_on)
        klass.directory = source_folder
        klass.status_downloaded = False
        return klass

    def __init__(self, name, depends_on: list = None):
        self.status_downloaded = False
        self.directory = plugin_folder
        self.name = name
        self._metadata = {
            "name": self.name,
            "version": "0.1",
            "module": '.'.join([plugin_folder.stem, self.name]),
            "extract": False,
            "depends_on": depends_on or [],
            "init_after": []
        }
        try:
            self.load(self.path)
        except FileNotFoundError:
            self.metadata = self._metadata

    @property
    def path(self):
        return self.directory.joinpath(self.name)

    def load(self, path):
        self.metadata = json.load(path.joinpath(self.metadata_file).open('r'))
        self.status_downloaded = True

    def create(self, rewrite=False):
        if rewrite:
            self.metadata = self._metadata
        if not self.path.exists() or rewrite:
            self._create(self.path)

    def _create(self, path: Path):
        path.mkdir(exist_ok=True)
        path.joinpath('__init__.py').touch(exist_ok=True)
        json.dump(self.metadata, path.joinpath(self.metadata_file).open('w'), ensure_ascii=False, indent=2)
        self.requirements.touch(exist_ok=True)

    @property
    def version(self):
        return self.metadata['version']

    @property
    def sp(self):
        return self.path.joinpath(self.package_folder)

    @property
    def requirements(self):
        return self.path.joinpath(self.requirements_file)

    @cached_property
    def environment(self):
        return Environment([str(self.sp)])

    @cached_property
    def installer(self):
        return partial(install, path=self.sp)

    def __repr__(self):
        return f'<Plugin: {self.name} v={self.version} {"D" if self.status_downloaded else "nD"}>'

    def __hash__(self):
        return hash((self.name, self.version))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def add_to_repo(self):
        repo_data = json.load(repo_file.open('r'))
        repo_data[self.name] = {
            "metadata": f"{file_host}/{self.name}/{self.metadata_file}",
            "requirements": f"{file_host}/{self.name}/{self.requirements_file}",
            "data": f"{file_host}/{self.name}/"
        }
        json.dump(repo_data, repo_file.open('w'), ensure_ascii=False, indent=2)




if __name__ == '__main__':
    for p in range(7):
        plugin = Plugin.from_source(f'plug_{p}')
        plugin.create()
        plugin.add_to_repo()
    Plugin('new_plugin', depends_on=['plug_6']).create()

