import codecs
import copy
import json
import os

from debug_utils import LOG_CURRENT_EXCEPTION

CONFIG_DIR = os.path.join('mods', 'configs', 'gunner_hud')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.json')
LEGACY_CONFIG_PATH = os.path.join('mods', 'configs', 'autoloader_timer', 'config.json')
VIEW_POSITION_KEYS = ('sniper', 'strategic')
# Defaults that 0.6.x and 0.7.0 wrote into every saved config; they are dropped so those views follow arcade again.
FORMER_AIM_VIEW_DEFAULTS = {'sniper': {'x': 120, 'y': 60}, 'strategic': {'x': 180, 'y': 70}}

DEFAULTS = {
    'enabled': True,
    'x': 0,
    'y': 60,
    'fontSize': 14,
    'hideWhenFull': False,
    'reloadChatLine': True,
    'autoreloaderLine': True,
    'magazineLine': True,
    'aresLine': True,
    'aimTimer': {
        'enabled': True,
        'penalty': True,
        'x': 150,
        'y': 0,
    },
    'colors': {
        'count': 'D8D8D8',
        'loaded': 'C7FE48',
        'loading': 'FCAF1A',
        'penalty': 'FF5247',
        'queued': 'D8D8D8',
        'shellTime': 'A8A8A8',
    },
}


def _merged(defaults, loaded):
    result = copy.deepcopy(defaults)
    for key, value in loaded.items():
        if key in defaults and isinstance(defaults[key], dict) and isinstance(value, dict):
            result[key] = _merged(defaults[key], value)
        elif key in defaults:
            result[key] = value
        elif key in VIEW_POSITION_KEYS and isinstance(value, dict) and 'x' in value and 'y' in value:
            result[key] = {'x': value['x'], 'y': value['y']}
    return result


def _without_former_aim_defaults(settings):
    aim = settings['aimTimer']
    for key, former in FORMER_AIM_VIEW_DEFAULTS.items():
        if aim.get(key) == former:
            del aim[key]
    return settings


def _read(path):
    with codecs.open(path, 'r', 'utf-8-sig') as f:
        return _without_former_aim_defaults(_merged(DEFAULTS, json.load(f)))


def load():
    try:
        if os.path.isfile(CONFIG_PATH):
            return _read(CONFIG_PATH)
        if os.path.isfile(LEGACY_CONFIG_PATH):
            settings = _read(LEGACY_CONFIG_PATH)
            save(settings)
            return settings
        save(DEFAULTS)
    except Exception:
        LOG_CURRENT_EXCEPTION()
    return _merged(DEFAULTS, {})


def save(settings):
    try:
        if not os.path.isdir(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        with codecs.open(CONFIG_PATH, 'w', 'utf-8') as f:
            json.dump(settings, f, indent=4, sort_keys=True)
    except Exception:
        LOG_CURRENT_EXCEPTION()
