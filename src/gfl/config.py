import json
import os

from gfl import statuses

BASE_DIRECTORY = os.path.expanduser('~') + '/.config/gfl/'
DATA_DIR = os.path.join(BASE_DIRECTORY, 'data')
CONFIG_FILE = BASE_DIRECTORY + 'config.json'


config = {
    'badges': {
        statuses.OPEN: {
            'badge': '•',
            'color': 'gray'
        },
        statuses.IN_PROGRESS: {
            'badge': '••',
            'color': 'blue'
        },
        statuses.REVIEW: {
            'badge': '•••',
            'color': 'orange'
        },
        statuses.DONE: {
            'badge': '✔',
            'color': 'green'
        }
    },
    'max_results': 100,
    'create_pull_request': True
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
CREATE_PULL_REQUEST = config['create_pull_request']
MAX_RESULTS = config['max_results']
