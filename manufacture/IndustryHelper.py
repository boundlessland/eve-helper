import math
import sys
from collections import defaultdict
from queue import Queue

from manufacture.IndustryEnum import ActivityID

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
                self.specialGroups[k].add(item[1])

    def word2ID(self, word: str):
        participants = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="TrnTranslations",
                                             conditions=f"tcID=8 AND text LIKE '%{word}%'", fields=["*"])
        return participants

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
            if materialProductDict[product].issubset(calculated):
                finalQuantity = intermediateProducts[product]
                runs = int(math.ceil(finalQuantity / productMaterialDict[product]["unitOutput"]))
                manufacturingChain.append({"product": product, "quantity": finalQuantity, "materials": []})
                if productMaterialDict[product]["activityID"] == ActivityID.Reaction.value:
                    for material in productMaterialDict[product]["materialDetails"]:
                        materialQuantity = self.finalQuantityCalculator(runs, material[3], [reactionEfficiency],
                                                                        productMaterialDict[product]["maxRuns"])
                        if material[2] in intermediateProducts.keys():
                            intermediateProducts[material[2]] += materialQuantity
                            materialQ.put(material[2])
                        else:
                            rawMaterials[material[2]] += materialQuantity
                        manufacturingChain[-1]["materials"].append((material[2], materialQuantity))
                elif productMaterialDict[product]["activityID"] == ActivityID.Manufacturing.value:
                    for material in productMaterialDict[product]["materialDetails"]:
                        if product == finalProduct:
                            materialQuantity = self.finalQuantityCalculator(runs, material[3],
                                                                            [materialEfficiency, rigMaterialEfficiency,
                                                                             structureMaterialEfficiency],
                                                                            numberOfProcess)
                        else:
                            materialQuantity = self.finalQuantityCalculator(runs,  material[3],
                                                                            [baseMaterialEfficiency, rigMaterialEfficiency,
                                                                            structureMaterialEfficiency],
                                                                            productMaterialDict[product]["maxRuns"])
                        if material[2] in productMaterialDict.keys():
                            intermediateProducts[material[2]] += materialQuantity
                            materialQ.put(material[2])
                        else:
                            rawMaterials[material[2]] += materialQuantity
                        manufacturingChain[-1]["materials"].append((material[2], materialQuantity))
                calculated.add(product)
            else:
                materialQ.put(product)
        return intermediateProducts, rawMaterials, manufacturingChain

    def getBlueprint(self, typeID: int):
        blueprint = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="IndustryActivityProducts",
                                          conditions=f"productTypeID={typeID}", fields=["*"])
        if len(blueprint) == 0:
            return ()
        return blueprint[0]

    def getMaterials(self, typeID: int, activityID: int):
        materials = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="IndustryActivityMaterials",
                                          conditions=f"typeID={typeID} AND activityID={activityID}", fields=["*"])
        return materials

    def getMaxRuns(self, typeID: int):
        maxRuns = Dao.conditionalSelect(self.sqlConfig, database="eve-base", table="IndustryBlueprints",
                                        conditions=f"typeID={typeID}", fields=["*"])
        return maxRuns[0][1]

    def buildMaterialTree(self, typeID: int, quantity: int):
        blueprint = self.getBlueprint(typeID)
        if len(blueprint) == 0:
            root = {"typeID": typeID, "quantity": quantity, "materials": [], "details": {}}
            return root
        materials = self.getMaterials(blueprint[0], blueprint[1])
        maxRuns = self.getMaxRuns(blueprint[0])
        root = {"typeID": typeID, "quantity": quantity, "materials": [],
                "details": {"maxRuns": maxRuns, "unitOutput": blueprint[3], "materialDetails": materials,
                            "activityID": blueprint[1]}}
        for material in materials:
            child = self.buildMaterialTree(material[2], material[3] * int(math.ceil(quantity / blueprint[3])))
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
        finalQuantity = (runs // maxRuns) * quantity * self.efficiencyDecorator(maxRuns, efficiencySeq) + \
                        self.efficiencyDecorator((runs % maxRuns) * quantity, efficiencySeq)
        return finalQuantity

    # class TreeNode:
    #     def __init__(self, typeID, activityID: int, quantity: int, materials: list):
    #         self.typeID = typeID
    #         self.activityId = activityID
    #         self.quantity = quantity
    #         self.materials = materials

    def entry(self, word: str, materialEfficiency: int, baseMaterialEfficiency=10, decomposeReaction=True):
        pass


a = IndustryHelper("../config/MySQLConfig.json")
b, c, d = a.processDecompose(12042, 1, 10, 0.1, 0.1, 0.042, 0.01, 0.024)
print(b)
print(c)
print(d)
# print(a.getMaxRuns(17328))
# print(a.getBlueprint(32782))
# tree = a.buildMaterialTree(11567, 1)
# b, c = a.materialTreeTraverse(tree)
# print(b)
# print(c)
# from common import display
#
# display.treeChart(tree)
