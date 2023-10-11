import json


def loadConfigFromJSON(filepath: str):
    config = {}
    try:
        config = json.load(open(filepath, 'r'))
    except IOError:
        print('ConfigFile ' + filepath + ' Not Found')
    return config

