import json
import os

BASE_DIRECTORY = os.path.expanduser('~') + '/.config/gfl/'
DATA_DIR = os.path.join(BASE_DIRECTORY, 'data')
CONFIG_FILE = BASE_DIRECTORY + 'config.json'


config = {
    'badges': {
        'open': {
            'badge': '•',
            'color': 'gray'
        },
        'in_progress': {
            'badge': '••',
            'color': 'blue'
        },
        'review': {
            'badge': '•••',
            'color': 'orange'
        },
        'resolved': {
            'badge': '✔',
            'color': 'green'
        }
    },
    'max_results': 100
}

if not os.path.exists(BASE_DIRECTORY):
    os.makedirs(BASE_DIRECTORY)

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    with open(CONFIG_FILE, 'w+') as f:
        json.dump(config, f, indent=4)


BADGES = config['badges']
CREATE_PULL_REQUEST = False
MAX_RESULTS = config['max_results']
