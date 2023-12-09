import json


def loadConfigFromJSON(filepath: str):
    config = {}
    try:
        config = json.load(open(filepath, 'r'))
    except IOError:
        print('ConfigFile ' + filepath + ' Not Found')
    return config


def dumpConfigToJSON(filepath: str, content: dict):
    with open(filepath, "w") as f:
        json.dump(content, f)
    f.close()
    return
