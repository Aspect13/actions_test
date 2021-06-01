import aiohttp
import asyncio
from aiofile import async_open

from .util import Plugin, list_plugins, cprint, repo_file, file_host


async def fetch_json(session, url):
    async with session.get(url) as response:
        print(response.status, response.url)
        return await response.json()


async def download_file(session, url, destination):
    async with session.get(url) as response:
        cprint(response.status, response.url, color='green')
        if response.ok:
            async with async_open(destination, 'wb') as afp:
                await afp.write(await response.read())


async def download_plugin(plugin, repo_data, session, plugins_to_download: set, tasks):
    plugin.metadata = await fetch_json(session, repo_data[plugin.name]['metadata'])
    cprint('Plugin download called', plugin, color='magenta')
    plugin.path.mkdir()
    for f in files_to_download_for_every_plugin:
        tasks.append(asyncio.create_task(
            download_file(session, f"{repo_data[plugin.name]['data'].rstrip('/')}/{f}", plugin.path.joinpath(f))
        ))

    plugins_to_download.add(plugin)
    async for i in resolve_dependencies(plugin, repo_data, session, plugins_to_download, tasks):
        tasks.append(i)
    return 200


async def resolve_dependencies(plugin, repo_data, session, plugins_to_download: set, tasks):
    for pp in plugin.metadata['depends_on']:
        if not Plugin(pp).status_downloaded:
            yield asyncio.create_task(download_plugin(Plugin(pp), repo_data, session, plugins_to_download, tasks))


async def check_for_updates(session, repo_data, plugins_to_update: set, plugins_local):
    for p in plugins_local:
        plugin = Plugin(p)
        try:
            repo_plugin_meta = await fetch_json(session, repo_data[plugin.name]['metadata'])
            if float(plugin.version) < float(repo_plugin_meta['version']):
                plugin.metadata = repo_plugin_meta
                plugin.status_downloaded = False
                plugins_to_update.add(plugin)
        except KeyError:
            pass


async def main(plugins_local, plugins_to_download, plugins_to_update, tasks):
    session = aiohttp.ClientSession()
    async with session:
        repo_data = await fetch_json(session, f'{file_host}/{repo_file.name}')

        for p in plugins_local:
            plugin = Plugin(p)
            # plugin_status[plugin] = plugin.status_downloaded
            if not plugin.status_downloaded:
                tasks.append(asyncio.create_task(download_plugin(plugin, repo_data, session, plugins_to_download, tasks)))
            async for i in resolve_dependencies(plugin, repo_data, session, plugins_to_download, tasks):
                tasks.append(i)
        await check_for_updates(session, repo_data, plugins_to_update, plugins_local)

        while pending := [task for task in tasks if not task.done()]:
            await asyncio.gather(*pending)


files_to_download_for_every_plugin = {'__init__.py', 'metadata.json', 'requirements.txt', '1.jpg'}


if __name__ == '__main__':

    plugins_local = set(list_plugins())
    plugins_to_download = set()
    plugins_to_update = set()
    tasks = []

    asyncio.run(main(plugins_local, plugins_to_download, plugins_to_update, tasks))

    cprint(f'{plugins_to_download=}')
    cprint(f'{plugins_to_update=}')
