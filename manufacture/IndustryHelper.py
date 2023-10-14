import math
import sys
from collections import defaultdict
from queue import Queue

from manufacture.IndustryEnum import ActivityID, IndustryRigMaterialEfficiency, IndustryStructureMaterialEfficiency, \
    IndustryRigZoneCoefficient

sys.path.append("../")

from util import DataLoader, Dao


def defaultDict():
    pass


class IndustryHelper:
    sqlConfig = {}
    specialGroups = {
        "Fuel Block": set()
    }

    def __init__(self, sqlConfigPath):
        self.sqlConfig = DataLoader.loadConfigFromJSON(sqlConfigPath)
        for k in self.specialGroups.keys():
            items = self.word2ID(k)
            for item in items:
                self.specialGroups[k].add(item["keyID"])

    def word2ID(self, word: str):
        participants = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="TrnTranslations",
                                             conditions=f"tcID=8 AND text LIKE '%{word}%'", fields=["*"])
        return participants

    def ID2Word(self, typeID: int, language: str):
        word = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="TrnTranslations",
                                     conditions=f"tcID=8 AND languageID='{language}' AND keyID={typeID}", fields=["*"])
        return word[0]

    def processDecompose(self, typeID: int, quantity: int, numberOfProcess: int, materialEfficiency: float,
                         baseMaterialEfficiency: float, rigMaterialEfficiency: float,
                         structureMaterialEfficiency: float, reactionEfficiency: float,
                         decomposeFuelBlocks=False, decomposeReaction=True):
        materialTree = self.buildMaterialTree(typeID, quantity)
        materialTree["details"]["maxRuns"] = numberOfProcess
        materialProductDict, productMaterialDict, finalProduct, intermediateProducts, rawMaterials = \
            self.materialTreeTraverse(materialTree, decomposeFuelBlocks, decomposeReaction)
        calculated, materialQ, manufacturingChain = set(), Queue(), []
        materialQ.put(finalProduct)
        intermediateProducts[finalProduct] = quantity
        while not materialQ.empty():
            product = materialQ.get()
            if product in calculated:
                continue
            if materialProductDict[product].issubset(calculated):
                finalQuantity = intermediateProducts[product]
                runs = int(math.ceil(finalQuantity / productMaterialDict[product]["unitOutput"]))
                finalQuantity = runs * productMaterialDict[product]["unitOutput"]
                manufacturingChain.append({"product": product, "quantity": finalQuantity, "materials": []})
                for material in productMaterialDict[product]["materialDetails"]:
                    materialQuantity = 0
                    if productMaterialDict[product]["activityID"] == ActivityID.Reaction.value:
                        materialQuantity = self.finalQuantityCalculator(runs, material["quantity"],
                                                                        [reactionEfficiency],
                                                                        productMaterialDict[product]["maxRuns"])
                    elif productMaterialDict[product]["activityID"] == ActivityID.Manufacturing.value:
                        if product == finalProduct:
                            materialQuantity = self.finalQuantityCalculator(runs, material["quantity"],
                                                                            [rigMaterialEfficiency + structureMaterialEfficiency,
                                                                            materialEfficiency], numberOfProcess)
                        else:
                            materialQuantity = self.finalQuantityCalculator(runs, material["quantity"],
                                                                            [rigMaterialEfficiency + structureMaterialEfficiency,
                                                                            baseMaterialEfficiency], productMaterialDict[product]["maxRuns"])
                    if material["materialTypeID"] in intermediateProducts.keys():
                        intermediateProducts[material["materialTypeID"]] += materialQuantity
                        materialQ.put(material["materialTypeID"])
                    else:
                        rawMaterials[material["materialTypeID"]] += materialQuantity
                    manufacturingChain[-1]["materials"].append((material["materialTypeID"], materialQuantity))
                calculated.add(product)
            else:
                materialQ.put(product)
        return intermediateProducts, rawMaterials, manufacturingChain, materialTree

    def getBlueprint(self, typeID: int):
        blueprint = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="IndustryActivityProducts",
                                          conditions=f"productTypeID={typeID}", fields=["*"])
        if len(blueprint) == 0:
            return {}
        if len(blueprint) > 1:
            # 防止出现多种图对应一种产出的情况（历史原因）
            for bpo in blueprint:
                productName = self.ID2Word(typeID, "en")["text"]
                bpoName = self.ID2Word(bpo["typeID"], "en")["text"]
                if bpoName.startswith(productName):
                    return bpo
            else:
                return {}
        return blueprint[0]

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
        return participants

    def buildMaterialTree(self, typeID: int, quantity: int):
        blueprint = self.getBlueprint(typeID)
        if len(blueprint) == 0:
            root = {"typeID": typeID, "quantity": quantity, "materials": [], "details": {}}
            return root
        materials = self.getMaterials(blueprint["typeID"], blueprint["activityID"])
        maxRuns = self.getMaxRuns(blueprint["typeID"])
        root = {"typeID": typeID, "quantity": quantity, "materials": [],
                "details": {"maxRuns": maxRuns, "unitOutput": blueprint["quantity"], "materialDetails": materials,
                            "activityID": blueprint["activityID"]}}
        for material in materials:
            child = self.buildMaterialTree(material["materialTypeID"], material["quantity"] * int(math.ceil(quantity / blueprint["quantity"])))
            root["materials"].append(child)
        return root

    def materialTreeTraverse(self, materialTree: dict, decomposeFuelBlocks=False, decomposeReaction=True):
        materialProductDict, productMaterialDict, finalProduct, intermediateProducts, rawMaterials = \
            defaultdict(set), defaultdict(dict), materialTree["typeID"], defaultdict(int), defaultdict(int)
        materialQ = Queue()
        materialProductDict[finalProduct] = set()
        productMaterialDict[finalProduct] = materialTree["details"]
        for material in materialTree["materials"]:
            materialQ.put(material)
        while not materialQ.empty():
            material = materialQ.get()
            if (not decomposeFuelBlocks and material["typeID"] in self.specialGroups["Fuel Block"]) \
                    or len(material["materials"]) == 0:
                rawMaterials[material["typeID"]] = 0
            else:
                intermediateProducts[material["typeID"]] = 0
                productMaterialDict[material["typeID"]] = material["details"]
                for subM in material["materials"]:
                    materialQ.put(subM)
                    materialProductDict[subM["typeID"]].add(material["typeID"])
        return materialProductDict, productMaterialDict, finalProduct, intermediateProducts, rawMaterials

    @staticmethod
    def efficiencyDecorator(quantity: int, efficiencySeq: list):
        for efficiency in efficiencySeq:
            quantity = int(math.ceil(quantity * (1 - efficiency)))
        return quantity

    def finalQuantityCalculator(self, runs: int, quantity: int, efficiencySeq: list, maxRuns: int):
        finalQuantity = (runs // maxRuns) * self.efficiencyDecorator(maxRuns * quantity, efficiencySeq) + \
                        self.efficiencyDecorator((runs % maxRuns) * quantity, efficiencySeq)
        return finalQuantity

    # class TreeNode:
    #     def __init__(self, typeID, activityID: int, quantity: int, materials: list):
    #         self.typeID = typeID
    #         self.activityId = activityID
    #         self.quantity = quantity
    #         self.materials = materials

    def industryCalculatorEntry(self, productName: str, quantity: int, materialEfficiency: int,
                                manufacturingStructure: str,
                                manufacturingRig: str, reactionStructure: str, reactionRig: str, solarSystem: str,
                                baseMaterialEfficiency=10, numberOfProcess=0, decomposeReaction=True,
                                decomposeFuelBlocks=False):
        participants = self.word2ID(productName)
        typeID, language = -1, ""
        for participant in participants:
            if productName == participant["text"]:
                typeID = participant["keyID"]
                language = participant["languageID"]
                break
        else:
            if len(participants) == 0:
                print("请检查输入，没有这个物品诶~")
            elif len(participants) > 1:
                print("具体想找哪个物品呢？")
                for participant in participants:
                    print(participant["text"])
            else:
                typeID = participants[0]["keyID"]
                language = participants[0]["languageID"]
        if typeID == -1:
            return
        blueprint = self.getBlueprint(typeID)
        if len(blueprint) == 0:
            print("这个物品无法建造哦~")
            return
        participants = self.getSolarSystem(solarSystem)
        solarSystem = {}
        if len(participants) == 0:
            print("请检查输入，没有这个星系诶~")
        elif len(participants) > 1:
            print("具体想找哪个星系呢？")
            for participant in participants:
                print(participant["solarSystemName"])
        else:
            solarSystem = participants[0]
        if len(solarSystem) == 0:
            return
        zoneCoefficient = 0
        if solarSystem["security"] > 0.5:
            zoneCoefficient = IndustryRigZoneCoefficient.Highsec.value
        elif solarSystem["security"] > 0:
            zoneCoefficient = IndustryRigZoneCoefficient.Lowsec.value
        elif solarSystem["security"] <= 0:
            zoneCoefficient = IndustryRigZoneCoefficient.Zerosec.value
        if numberOfProcess == 0:
            numberOfProcess = self.getMaxRuns(self.getBlueprint(typeID)["typeID"])
        materialEfficiency = materialEfficiency / 100
        baseMaterialEfficiency = baseMaterialEfficiency / 100
        rigMaterialEfficiency = getattr(IndustryRigMaterialEfficiency, manufacturingRig).value * zoneCoefficient
        structureMaterialEfficiency = getattr(IndustryStructureMaterialEfficiency, manufacturingStructure).value
        reactionEfficiency = getattr(IndustryRigMaterialEfficiency, reactionRig).value
        intermediateProducts, rawMaterials, manufacturingChain, materialTree = \
            self.processDecompose(typeID, quantity, numberOfProcess, materialEfficiency, baseMaterialEfficiency,
                                  rigMaterialEfficiency, structureMaterialEfficiency, reactionEfficiency)
        intermediateProducts = [(self.ID2Word(_[0], language)["text"], _[1]) for _ in intermediateProducts.items()]
        rawMaterials = [(self.ID2Word(_[0], language)["text"], _[1]) for _ in rawMaterials.items()]
        manufacturingChain = [{"产物": self.ID2Word(_["product"], language)["text"], "数量": _["quantity"],
                               "原料": [(self.ID2Word(temp[0], language)["text"], temp[1]) for temp in _["materials"]]}
                              for _ in reversed(manufacturingChain)]
        return intermediateProducts, rawMaterials, manufacturingChain, materialTree


helper = IndustryHelper("../config/MySQLConfig.json")
intermediate, raw, chain, _ = helper.industryCalculatorEntry("神使级", 1, 9, "Sotiyo", "T1", "Tatara", "T2",
                                                         "k8x")
for item in intermediate:
    print(item)
for item in raw:
    print(item)
for item in chain:
    print(item)
# print(a.ID2Word(17328, "zh"))
# b, c, d, e = a.processDecompose(12042, 1, 10, 0.1, 0.1, 0.042, 0.01, 0.024)
# print(b)
# print(c)
# print(d)
# print(a.getMaxRuns(17328))
# print(a.getBlueprint(32782))
# tree = a.buildMaterialTree(11567, 1)
# b, c = a.materialTreeTraverse(tree)
# print(b)
# print(c)
# from common import display
#
# display.treeChart(tree)
