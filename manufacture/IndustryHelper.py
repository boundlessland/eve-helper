import math
import sys
from collections import defaultdict
from queue import Queue

from manufacture.IndustryEnum import ActivityID, IndustryRigMaterialEfficiency, IndustryStructureMaterialEfficiency, \
    IndustryRigZoneCoefficient
from util.QueryConsole import queryConsole

sys.path.append("../")


class IndustryHelper:
    specialGroups = {
        "Fuel Block": set()
    }

    def __init__(self):
        for k in self.specialGroups.keys():
            items = queryConsole.word2ID(k)
            for it in items:
                self.specialGroups[k].add(it["keyID"])

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
                                                                            [
                                                                                rigMaterialEfficiency + structureMaterialEfficiency,
                                                                                baseMaterialEfficiency],
                                                                            productMaterialDict[product]["maxRuns"])
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

    def buildMaterialTree(self, typeID: int, quantity: int):
        blueprint = queryConsole.getBlueprint(typeID)
        if len(blueprint) == 0:
            root = {"typeID": typeID, "quantity": quantity, "materials": [], "details": {}}
            return root
        materials = queryConsole.getMaterials(blueprint["typeID"], blueprint["activityID"])
        maxRuns = queryConsole.getMaxRuns(blueprint["typeID"])
        root = {"typeID": typeID, "quantity": quantity, "materials": [],
                "details": {"maxRuns": maxRuns, "unitOutput": blueprint["quantity"], "materialDetails": materials,
                            "activityID": blueprint["activityID"]}}
        for material in materials:
            child = self.buildMaterialTree(material["materialTypeID"],
                                           material["quantity"] * int(math.ceil(quantity / blueprint["quantity"])))
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

