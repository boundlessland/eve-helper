import sys
from datetime import datetime

import pandas as pd
import requests
from util import DataLoader

sys.path.append("../")


class EVEApi:
    baseURL = ""
    api = {}

    def __init__(self, configPath):
        self.__dict__.update(DataLoader.loadConfigFromJSON(configPath))
        assert self.baseURL != ""

    def __getter__(self, apiName: str, params: dict):
        assert apiName in self.api.keys()
        response = ""
        try:
            response = requests.get(self.baseURL + self.api[apiName], params=params).text
        except Exception as e:
            print(e)
        return response

    def getIndustrySystems(self):
        params = {"dataSource": "tranquility"}
        return self.__getter__("IndustrySystems", params)


class EVEApiHandler:
    api = None

    def __init__(self, configPath):
        self.api = EVEApi(configPath)

    def getIndustrySystems(self):
        rawData = eval(self.api.getIndustrySystems())
        updateTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        newData = []
        for row in rawData:
            newRow, costIndices = {"solarSystemID": row["solar_system_id"]}, row["cost_indices"]
            for index in costIndices:
                newRow.update({index["activity"]: index["cost_index"]})
            newRow.update({"updateTime": "'" + updateTime + "'"})
            newData.append(newRow)
        return newData
