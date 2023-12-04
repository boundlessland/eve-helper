from util import DataLoader, Dao


class QueryConsole:
    def __init__(self, sqlConfigPath):
        self.sqlConfig = DataLoader.loadConfigFromJSON(sqlConfigPath)

    def word2ID(self, word: str):
        participants = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="TrnTranslations",
                                             conditions=f"tcID=8 AND text LIKE '%{word}%'", fields=["*"])
        return participants

    def ID2Word(self, typeID: int, language: str):
        word = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="TrnTranslations",
                                     conditions=f"tcID=8 AND languageID='{language}' AND keyID={typeID}", fields=["*"])
        return word[0]

    def getMaterials(self, typeID: int, activityID: int):
        materials = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="IndustryActivityMaterials",
                                          conditions=f"typeID={typeID} AND activityID={activityID}", fields=["*"])
        return materials

    def getMaxRuns(self, typeID: int):
        maxRuns = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="IndustryBlueprints",
                                        conditions=f"typeID={typeID}", fields=["*"])
        return maxRuns[0]["maxProductionLimit"]

    def getSolarSystem(self, systemName: str):
        participants = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="mapSolarSystems",
                                             conditions=f"solarSystemName LIKE '%{systemName}%'",
                                             fields=["solarSystemID", "solarSystemName", "security"])
        solarSystem = {}
        if len(participants) == 0:
            print("请检查输入，此星系不存在")
        elif len(participants) > 1:
            print("可能查找如下星系，请选择：")
            for participant in participants:
                print(participant["solarSystemName"])
        else:
            solarSystem = participants[0]
        return solarSystem

    def getBlueprint(self, typeID: int):
        blueprint = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="IndustryActivityProducts",
                                          conditions=f"productTypeID={typeID}", fields=["*"])
        if len(blueprint) == 0:
            return {}
        if len(blueprint) > 1:
            # 防止出现多种图对应一种产出的情况（历史原因）
            for bp in blueprint:
                productName = self.ID2Word(typeID, "en")["text"]
                bpoName = self.ID2Word(bp["typeID"], "en")["text"]
                if bpoName.startswith(productName):
                    return bp
            else:
                return {}
        return blueprint[0]

    def getExactProductID(self, productName):
        participants = self.word2ID(productName)
        typeID, language = -1, ""
        for participant in participants:
            if productName == participant["text"]:
                typeID = participant["keyID"]
                language = participant["languageID"]
                break
        else:
            if len(participants) == 0:
                print("请检查输入，此物品不存在")
            elif len(participants) > 1:
                print("可能查找如下物品，请选择：")
                for participant in participants:
                    print(participant["text"])
            else:
                typeID = participants[0]["keyID"]
                language = participants[0]["languageID"]
        return typeID, language


queryConsole = QueryConsole("../config/MySQLConfig.json")
