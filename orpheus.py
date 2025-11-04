#!/usr/bin/env python3

import argparse
import json
import os
import re
from urllib.parse import urlparse

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

from orpheus.core import *
from orpheus.music_downloader import beauty_format_seconds
from orpheus.cli import watchdog, menu
from utils.network import set_offline_mode, network_manager
from orpheus.delivery import delivery_pipeline


def _build_media_from_url(orpheus: Orpheus, link: str):
    media_to_download = {}
    url = urlparse(link)
    components = url.path.split('/')

    service_name = None
    for pattern in orpheus.module_netloc_constants:
        if re.findall(pattern, url.netloc):
            service_name = orpheus.module_netloc_constants[pattern]
            break

    if not service_name:
        print(f'URL location "{url.netloc}" is not found in modules!')
        return {}

    media_to_download.setdefault(service_name, [])

    if orpheus.module_settings[service_name].url_decoding is ManualEnum.manual:
        module = orpheus.load_module(service_name)
        media_to_download[service_name].append(module.custom_url_parse(link))
    else:
        if not components or len(components) <= 2:
            print(f'Invalid URL: "{link}"')
            return {}

        url_constants = orpheus.module_settings[service_name].url_constants
        if not url_constants:
            url_constants = {
                'track': DownloadTypeEnum.track,
                'album': DownloadTypeEnum.album,
                'playlist': DownloadTypeEnum.playlist,
                'artist': DownloadTypeEnum.artist
            }

        type_matches = [media_type for url_check, media_type in url_constants.items() if url_check in components]

        if not type_matches:
            print(f'Invalid URL: "{link}"')
            return {}

        media_to_download[service_name].append(
            MediaIdentification(media_type=type_matches[-1], media_id=components[-1])
        )

    return media_to_download


def _build_media_from_command(orpheus: Orpheus, parts):
    modulename = parts[0].lower()
    if modulename not in orpheus.module_list:
        modules = [i for i in orpheus.module_list if ModuleFlags.hidden not in orpheus.module_settings[i].flags]
        print(f'Unknown module name "{modulename}". Must select from: {", ".join(modules)}')
        return {}

    try:
        media_type = DownloadTypeEnum[parts[1].lower()]
    except KeyError:
        options = '/'.join(i.name for i in DownloadTypeEnum)
        print(f'{parts[1].lower()} is not a valid download type! Choose {options}')
        return {}

    ids = parts[2:]
    if not ids:
        print('No media IDs provided.')
        return {}

    return {
        modulename: [MediaIdentification(media_type=media_type, media_id=i) for i in ids]
    }


def _process_download_entries(orpheus: Orpheus, entries):
    path = orpheus.settings['global']['general']['download_path']
    if path.endswith('/'):
        path = path[:-1]
    os.makedirs(path, exist_ok=True)

    tpm = {ModuleModes.covers: '', ModuleModes.lyrics: '', ModuleModes.credits: ''}
    for key in tpm:
        moduleselected = orpheus.settings['global']['module_defaults'][key.name]
        if moduleselected == 'default':
            moduleselected = None
        tpm[key] = moduleselected
    sdm = 'default'

    futures = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        if entry.startswith('http'):
            media_to_download = _build_media_from_url(orpheus, entry)
        else:
            parts = entry.split()
            media_to_download = _build_media_from_command(orpheus, parts) if len(parts) >= 3 else {}

        if not media_to_download:
            continue

        future = delivery_pipeline.submit(orpheus_core_download, orpheus, media_to_download, tpm.copy(), sdm, path)
        futures.append(future)

    for future in futures:
        if hasattr(future, 'result'):
            future.result()


def _interactive_download_input(orpheus: Orpheus):
    while True:
        try:
            entry = input('Enter URL or "service type id" (blank to finish): ').strip()
        except EOFError:
            print('\nExiting download zone input.')
            break
        if not entry:
            break
        _process_download_entries(orpheus, [entry])


def _register_menu_actions(orpheus: Orpheus):
    """Register default interactive menu actions."""

    def process_entries(entries):
        if not entries:
            print('No entries provided.')
            return
        _process_download_entries(orpheus, entries)
    def health_check():
        "Run module health checks"
        for module in sorted(orpheus.module_list):
            if ModuleFlags.hidden in orpheus.module_settings[module].flags:
                continue
            orpheus.run_module_health_check(module)

    def show_config():
        "Display active configuration"
        print(json.dumps(orpheus.settings, indent=2))

    def list_services():
        "List service capabilities"
        for module in sorted(orpheus.module_list):
            info = service_registry.get_service(module)
            capabilities = sorted(info.capabilities) if info else []
            print(f"{module}: {', '.join(capabilities) if capabilities else 'unknown'}")

    def show_ai_hints():
        "Show brain advisories"
        hints = watchdog.display_hints()
        if not hints:
            print('No hints available yet.')
        for hint in hints:
            print(hint)

    def list_modules():
        "List modules"
        for module in sorted(orpheus.module_list):
            print(module)

    def edit_modules_yaml():
        "Edit modules via YAML"
        if yaml is None:
            print('YAML editing requires PyYAML. Install it or run `pip install PyYAML` inside the virtualenv.')
            return
        settings_path = orpheus.settings_location
        with open(settings_path, 'r', encoding='utf-8') as fh:
            raw_data = json.loads(fh.read())
        modules_data = raw_data.get('modules', {})
        yaml_text = yaml.safe_dump(modules_data, sort_keys=True)
        print('Current module configuration (YAML):')
        print(yaml_text)
        print('Enter new YAML (finish with a single dot on its own line to apply, blank line to cancel):')
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                line = ''
            if line.strip() == '.':
                break
            if not line and not lines:
                print('No changes applied.')
                return
            lines.append(line)
        new_yaml = '\n'.join(lines).strip()
        if not new_yaml:
            print('No changes applied.')
            return
        try:
            new_modules = yaml.safe_load(new_yaml)
            if new_modules is None:
                new_modules = {}
            if not isinstance(new_modules, dict):
                raise ValueError('modules YAML must define a mapping')
            raw_data['modules'] = new_modules
            with open(settings_path, 'w', encoding='utf-8') as fh:
                fh.write(json.dumps(raw_data, indent=4))
            orpheus.raw_settings = raw_data
            orpheus.settings = _resolve_env_placeholders(deepcopy(raw_data))
            service_registry.load_from_config(orpheus.settings)
            print('Modules configuration updated. Restart Orpheus for full effect if needed.')
        except Exception as exc:
            print(f'Failed to parse YAML: {exc}')

    def interactive_config_wizard():
        "Interactive configuration wizard"
        settings_path = orpheus.settings_location
        with open(settings_path, 'r', encoding='utf-8') as fh:
            raw_data = json.loads(fh.read())

        general = raw_data.setdefault('global', {}).setdefault('general', {})
        formatting = raw_data['global'].setdefault('formatting', {})
        lyrics_cfg = raw_data['global'].setdefault('lyrics', {})
        advanced = raw_data['global'].setdefault('advanced', {})

        def prompt(message, current):
            try:
                value = input(f'{message} [{current}]: ').strip()
            except EOFError:
                return current
            return value or current

        def prompt_bool(message, current):
            try:
                value = input(f'{message} (y/n) [{"y" if current else "n"}]: ').strip().lower()
            except EOFError:
                return current
            if not value:
                return current
            return value in {'y', 'yes', '1', 'true'}

        general['download_path'] = prompt('Download path', general.get('download_path', './downloads/'))
        general['download_quality'] = prompt('Download quality (hifi/lossless/high/medium/low)', general.get('download_quality', 'hifi'))
        general['search_limit'] = int(prompt('Search limit', general.get('search_limit', 10)))

        formatting['album_format'] = prompt('Album format', formatting.get('album_format', '{name}{explicit}'))
        formatting['track_filename_format'] = prompt('Track filename format', formatting.get('track_filename_format', '{track_number}. {name}'))
        formatting['single_full_path_format'] = prompt('Single full path format', formatting.get('single_full_path_format', '{name}'))

        lyrics_cfg['embed_lyrics'] = prompt_bool('Embed lyrics?', lyrics_cfg.get('embed_lyrics', True))
        lyrics_cfg['embed_synced_lyrics'] = prompt_bool('Embed synced lyrics?', lyrics_cfg.get('embed_synced_lyrics', False))
        lyrics_cfg['save_synced_lyrics'] = prompt_bool('Save synced lyrics (.lrc)?', lyrics_cfg.get('save_synced_lyrics', True))

        advanced['debug_mode'] = prompt_bool('Enable debug logging?', advanced.get('debug_mode', False))
        advanced['ignore_existing_files'] = prompt_bool('Ignore existing files during download?', advanced.get('ignore_existing_files', False))
        advanced['allow_insecure_requests'] = prompt_bool('Allow insecure network requests?', advanced.get('allow_insecure_requests', False))

        with open(settings_path, 'w', encoding='utf-8') as fh:
            fh.write(json.dumps(raw_data, indent=4))
        orpheus.raw_settings = raw_data
        orpheus.settings = _resolve_env_placeholders(deepcopy(raw_data))
        configure_request_session(orpheus.settings['global']['advanced'].get('allow_insecure_requests', False))
        print('Configuration updated.')

    def downloader_status():
        "Downloader interactive center"
        print('Delivery pipeline and queue status:')
        print(' - Jobs executed in this session are visible in logs; real-time queue UI coming soon.')

    def wrap(func):
        def handler():
            func()
            return None
        return handler

    main_screen = menu.create_screen("Orpheus Main Menu")
    diagnostics_screen = menu.create_screen("Diagnostics & Health")
    config_screen = menu.create_screen("Configuration & Services")
    modules_screen = menu.create_screen("Modules")
    downloader_screen = menu.create_screen("Download Zone")

    diagnostics_screen.option('1', 'Run module health checks', wrap(health_check))
    diagnostics_screen.option('2', 'Show brain advisories', wrap(show_ai_hints))

    config_screen.option('1', 'Display active configuration', wrap(show_config))
    config_screen.option('2', 'List service capabilities', wrap(list_services))
    config_screen.option('3', 'Interactive configuration wizard', wrap(interactive_config_wizard))

    modules_screen.option('1', 'List installed modules', wrap(list_modules))
    modules_screen.option('2', 'Run health checks', wrap(health_check))
    modules_screen.option('3', 'Edit modules via YAML', wrap(edit_modules_yaml))

    downloader_screen.option('1', 'Show AI advisories', wrap(show_ai_hints))
    downloader_screen.option('2', 'Show delivery status', wrap(downloader_status))
    downloader_screen.option('3', 'Download entries (each Enter starts job)', lambda: _interactive_download_input(orpheus))

    main_screen.option('1', 'Diagnostics & Health', lambda: diagnostics_screen)
    main_screen.option('2', 'Configuration & services', lambda: config_screen)
    main_screen.option('3', 'AI Center', wrap(show_ai_hints))
    main_screen.option('4', 'Modules', lambda: modules_screen)
    main_screen.option('5', 'Downloader Interactive Center', lambda: downloader_screen)

    menu.set_root(main_screen)


def main():
    print(r'''
   ____             _                    _____  _      
  / __ \           | |                  |  __ \| |     
 | |  | |_ __ _ __ | |__   ___ _   _ ___| |  | | |     
 | |  | | '__| '_ \| '_ \ / _ \ | | / __| |  | | |     
 | |__| | |  | |_) | | | |  __/ |_| \__ \ |__| | |____ 
  \____/|_|  | .__/|_| |_|\___|\__,_|___/_____/|______|
             | |                                       
             |_|                                       
             
            ''')
    
    help_ = 'Use "settings [option]" for orpheus controls (coreupdate, fullupdate, modinstall), "settings [module]' \
           '[option]" for module specific options (update, test, setup), searching by "[search/luckysearch] [module]' \
           '[track/artist/playlist/album] [query]", or just putting in urls. (you may need to wrap the URLs in double' \
           'quotes if you have issues downloading)'
    parser = argparse.ArgumentParser(description='Orpheus: modular music archival')
    parser.add_argument('-p', '--private', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('-o', '--output', help='Select a download output path. Default is the provided download path in config/settings.py')
    parser.add_argument('-lr', '--lyrics', default='default', help='Set module to get lyrics from')
    parser.add_argument('-cv', '--covers', default='default', help='Override module to get covers from')
    parser.add_argument('-cr', '--credits', default='default', help='Override module to get credits from')
    parser.add_argument('-sd', '--separatedownload', default='default', help='Select a different module that will download the playlist instead of the main module. Only for playlists.')
    parser.add_argument('--menu', action='store_true', help='Launch the interactive CLI menu')
    parser.add_argument('arguments', nargs='*', help=help_)
    args = parser.parse_args()

    if args.menu:
        watchdog.record_command('menu')
        orpheus = Orpheus(args.private)
        _register_menu_actions(orpheus)
        menu.run()
        return

    watchdog.record_command(' '.join(args.arguments) if args.arguments else 'help')

    orpheus = Orpheus(args.private)
    if not args.arguments:
        _register_menu_actions(orpheus)
        menu.run()
        return


    orpheus_mode = args.arguments[0].lower()
    if orpheus_mode == 'config':
        if len(args.arguments) == 1:
            print(json.dumps(orpheus.settings, indent=2))
            return
        subcommand = args.arguments[1].lower()
        if subcommand == 'services':
            for module in sorted(orpheus.module_list):
                info = service_registry.get_service(module)
                creds = session_manager.provide_credentials(module)
                print(f"{module}: capabilities={sorted(info.capabilities) if info else []}, credentials={list(creds.keys())}")
        elif subcommand == 'offline':
            state = args.arguments[2].lower() if len(args.arguments) > 2 else 'status'
            if state in {'on', 'true'}:
                set_offline_mode(True)
                print('Offline mode enabled.')
            elif state in {'off', 'false'}:
                set_offline_mode(False)
                print('Offline mode disabled.')
            else:
                print(f'Offline mode is currently {"enabled" if network_manager.offline_mode else "disabled"}.')
        else:
            raise Exception(f'Unknown config option: {subcommand}')
    else:
        path = args.output if args.output else orpheus.settings['global']['general']['download_path']
        if path[-1] == '/': path = path[:-1]  # removes '/' from end if it exists
        os.makedirs(path, exist_ok=True)

        media_types = '/'.join(i.name for i in DownloadTypeEnum)

        if orpheus_mode == 'search' or orpheus_mode == 'luckysearch':
            if len(args.arguments) > 3:
                modulename = args.arguments[1].lower()
                if modulename in orpheus.module_list:
                    try:
                        query_type = DownloadTypeEnum[args.arguments[2].lower()]
                    except KeyError:
                        raise Exception(f'{args.arguments[2].lower()} is not a valid search type! Choose {media_types}')
                    lucky_mode = True if orpheus_mode == 'luckysearch' else False
                    
                    query = ' '.join(args.arguments[3:])
                    module = orpheus.load_module(modulename)
                    items = module.search(query_type, query, limit = (1 if lucky_mode else orpheus.settings['global']['general']['search_limit']))
                    if len(items) == 0:
                        raise Exception(f'No search results for {query_type.name}: {query}')

                    if lucky_mode:
                        selection = 0
                    else:
                        for index, item in enumerate(items, start=1):
                            additional_details = '[E] ' if item.explicit else ''
                            additional_details += f'[{beauty_format_seconds(item.duration)}] ' if item.duration else ''
                            additional_details += f'[{item.year}] ' if item.year else ''
                            additional_details += ' '.join([f'[{i}]' for i in item.additional]) if item.additional else ''
                            if query_type is not DownloadTypeEnum.artist:
                                artists = ', '.join(item.artists) if item.artists is list else item.artists
                                print(f'{str(index)}. {item.name} - {", ".join(artists)} {additional_details}')
                            else:
                                print(f'{str(index)}. {item.name} {additional_details}')
                        
                        selection_input = input('Selection: ')
                        if selection_input.lower() in ['e', 'q', 'x', 'exit', 'quit']: exit()
                        if not selection_input.isdigit(): raise Exception('Input a number')
                        selection = int(selection_input)-1
                        if selection < 0 or selection >= len(items): raise Exception('Invalid selection')
                        print()
                    selected_item: SearchResult = items[selection]
                    media_to_download = {modulename: [MediaIdentification(media_type=query_type, media_id=selected_item.result_id, extra_kwargs=selected_item.extra_kwargs)]}
                elif modulename == 'multi':
                    return  # TODO
                else:
                    modules = [i for i in orpheus.module_list if ModuleFlags.hidden not in orpheus.module_settings[i].flags]
                    raise Exception(f'Unknown module name "{modulename}". Must select from: {", ".join(modules)}') # TODO: replace with InvalidModuleError
            else:
                print(f'Search must be done as orpheus.py [search/luckysearch] [module] [{media_types}] [query]')
                exit() # TODO: replace with InvalidInput
        elif orpheus_mode == 'download':
            if len(args.arguments) > 3:
                modulename = args.arguments[1].lower()
                if modulename in orpheus.module_list:
                    try:
                        media_type = DownloadTypeEnum[args.arguments[2].lower()]
                    except KeyError:
                        raise Exception(f'{args.arguments[2].lower()} is not a valid download type! Choose {media_types}')
                    media_to_download = {modulename: [MediaIdentification(media_type=media_type, media_id=i) for i in args.arguments[3:]]}
                else:
                    modules = [i for i in orpheus.module_list if ModuleFlags.hidden not in orpheus.module_settings[i].flags]
                    raise Exception(f'Unknown module name "{modulename}". Must select from: {", ".join(modules)}') # TODO: replace with InvalidModuleError
            else:
                print(f'Download must be done as orpheus.py [download] [module] [{media_types}] [media ID 1] [media ID 2] ...')
                exit() # TODO: replace with InvalidInput
        elif orpheus_mode == 'settings':
            print('Use `python orpheus.py --menu` or `python orpheus.py config ...` for settings management.')
            return
        elif orpheus_mode == 'sessions':
            print('Sessions management is now handled via the menu or configuration wizard.')
            return
        else:  # if no specific modes are detected, parse as urls, but first try loading as a list of URLs
            arguments = tuple(open(args.arguments[0], 'r')) if len(args.arguments) == 1 and os.path.exists(args.arguments[0]) else args.arguments
            media_to_download = {}
            for link in arguments:
                if link.startswith('http'):
                    url = urlparse(link)
                    components = url.path.split('/')

                    service_name = None
                    for i in orpheus.module_netloc_constants:
                        if re.findall(i, url.netloc): service_name = orpheus.module_netloc_constants[i]
                    if not service_name:
                        raise Exception(f'URL location "{url.netloc}" is not found in modules!')
                    if service_name not in media_to_download: media_to_download[service_name] = []

                    if orpheus.module_settings[service_name].url_decoding is ManualEnum.manual:
                        module = orpheus.load_module(service_name)
                        media_to_download[service_name].append(module.custom_url_parse(link))
                    else:
                        if not components or len(components) <= 2:
                            print(f'\tInvalid URL: "{link}"')
                            exit() # TODO: replace with InvalidInput
                        
                        url_constants = orpheus.module_settings[service_name].url_constants
                        if not url_constants:
                            url_constants = {
                                'track': DownloadTypeEnum.track,
                                'album': DownloadTypeEnum.album,
                                'playlist': DownloadTypeEnum.playlist,
                                'artist': DownloadTypeEnum.artist
                            }

                        type_matches = [media_type for url_check, media_type in url_constants.items() if url_check in components]

                        if not type_matches:
                            print(f'Invalid URL: "{link}"')
                            exit()

                        media_to_download[service_name].append(MediaIdentification(media_type=type_matches[-1], media_id=components[-1]))
                else:
                    print(f'Skipping invalid argument: "{link}"')

        # Prepare the third-party modules similar to above
        tpm = {ModuleModes.covers: '', ModuleModes.lyrics: '', ModuleModes.credits: ''}
        for i in tpm:
            moduleselected = getattr(args, i.name).lower()
            if moduleselected == 'default':
                moduleselected = orpheus.settings['global']['module_defaults'][i.name]
            if moduleselected == 'default':
                moduleselected = None
            tpm[i] = moduleselected
        sdm = args.separatedownload.lower()

        if not media_to_download:
            print('No links given')

        orpheus_core_download(orpheus, media_to_download, tpm, sdm, path)

    hints = watchdog.display_hints()
    if hints:
        print()
        for hint in hints:
            print(f'[AI] {hint}')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n\t^C pressed - abort')
        exit()
