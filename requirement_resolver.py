from collections import defaultdict
from pprint import pprint

import pkg_resources

from util import Plugin, plugin_folder, cprint, list_plugins


# global_env = pkg_resources.Environment()


def add_entry(plugin_name):
	plugin = Plugin(plugin_name)
	cprint('adding entries for:', plugin_name)
	pkg_resources.working_set.add_entry(plugin.sp)


def add_entries(plugins):
	for p in plugins:
		add_entry(Plugin(p).name)


def get_pending_requirements(plugin_name, mutable_result=None):
	if mutable_result:
		pending_requirements = mutable_result
	else:
		pending_requirements = defaultdict(list)

	plugin = Plugin(plugin_name)
	cprint('reading requirements for:', plugin_name)

	reqs = pkg_resources.parse_requirements(plugin.requirements.open().readlines())
	# pkg_resources.working_set.resolve(reqs, installer=plugin.installer, env=plugin.environment)
	for r in reqs:
		try:
			pkg_resources.working_set.resolve([r])
		except pkg_resources.VersionConflict as e:
			# pending_requirements[e.req.project_name].append({
			# 	'plugin': plugin,
			# 	'requirement': e.req
			# })
			# pending_requirements[e.dist.project_name].append({
			# 	'plugin': 'CORE',
			# 	'requirement': e.dist
			# })
			# cprint(e.dist, e.req, color='red')
			raise e
		except pkg_resources.DistributionNotFound as e:
			pending_requirements[e.req.project_name].append({
				'plugin': plugin,
				'requirement': e.req
			})
			cprint('\tto be installed:', e.req, color='green')
	return pending_requirements


if __name__ == '__main__':

	add_entries(list_plugins())
	pending_requirements = defaultdict(list)
	for p in list_plugins():
		pending_requirements = get_pending_requirements(Plugin(p).name, mutable_result=pending_requirements)

	pprint(pending_requirements, indent=3)
















# def resolve_version_conflict(name, requirees):
# 	cprint('trying to resolve version conflict for', name, color='yellow')
# 	for i in requirees:
# 		for ii in requirees:
# 			cprint(i['requirement'].__dict__, ii['requirement'])
# 			if i['requirement'] == ii['requirement']:
# 				continue
# 			v1, v2 = i['requirement'].specifier, ii['requirement'].specifier
# 			if v1 in v2:
# 				cprint(i, ii, 'ININININ')
# 			else:
# 				cprint(i, ii, 'NOT IN')
#
#
#
# def resolve_version_conflicts(pending_requirements):
# 	for req_name in pending_requirements:
# 		if len(pending_requirements[req_name]) > 1:
# 			resolve_version_conflict(req_name, pending_requirements[req_name])
# 	pass


# resolve_version_conflicts(pending_requirements)




# for p in plugin_folder.iterdir():
# 	plugin = Plugin(p.name)
# 	cprint('\n', p.name)
