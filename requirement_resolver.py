from collections import defaultdict
from pprint import pprint
from types import MappingProxyType

import pkg_resources

from .util import Plugin, plugin_folder, cprint, list_plugins


# global_env = pkg_resources.Environment()


def add_entry(plugin: Plugin):
	cprint('adding entries for:', plugin.name)
	pkg_resources.working_set.add_entry(plugin.sp)


def add_entries(plugins):
	for p in plugins:
		add_entry(Plugin(p))


def update_pending_requirements(plugin_name, pending_requirements):
	plugin = Plugin(plugin_name)
	cprint('reading requirements for:', plugin_name)

	reqs = pkg_resources.parse_requirements(plugin.requirements.open().readlines())
	# pkg_resources.working_set.resolve(reqs, installer=plugin.installer, env=plugin.environment)
	for r in reqs:
		try:
			pkg_resources.working_set.resolve([r])
		except pkg_resources.VersionConflict as e:
			req_status['conflict'][e.req.project_name].append({
				'plugin': plugin,
				'requirement': e.req
			})
			req_status['conflict'][e.dist.project_name].append({
				'plugin': 'CORE',
				'requirement': e.dist
			})
			# raise e
		except pkg_resources.DistributionNotFound as e:
			pending_requirements[e.req.project_name].append({
				'plugin': plugin,
				'requirement': e.req
			})
			cprint('\tto be installed:', e.req, color='green')













def resolve_version_conflict(requirers):
	status = 'safe'
	for spec1, spec2 in map(lambda a, b: (a['requirement'].specifier, b['requirement'].specifier), requirers, requirers[1:]):
		if spec1 != spec2:
			if spec1 and spec2:
				status = 'conflict'
				break
			else:
				status = 'attention'
	return status




def resolve_version_conflicts(pending_requirements, req_status):
	for req_name in pending_requirements:
		if len(pending_requirements[req_name]) > 1:
			req_status[resolve_version_conflict(pending_requirements[req_name])][req_name].append(pending_requirements[req_name])
		else:
			req_status['safe'][req_name].append(pending_requirements[req_name])






if __name__ == '__main__':

	add_entries(list_plugins())
	req_status = MappingProxyType({
		'safe': defaultdict(list),
		'attention': defaultdict(list),
		'conflict': defaultdict(list)
	})
	pending_requirements = defaultdict(list)
	for p in list_plugins():
		update_pending_requirements(Plugin(p).name)

	# resolve_version_conflicts(pending_requirements, req_status)
	cprint('pending_requirements', color='blue')
	pprint(pending_requirements, indent=3)
	cprint('conflicting_requirements', color='red')
	pprint(req_status['conflict'], indent=3)
	cprint('safe_requirements', color='green')
	pprint(req_status['safe'], indent=3)
	cprint('attention_requirements', color='yellow')
	pprint(req_status['attention'], indent=3)


