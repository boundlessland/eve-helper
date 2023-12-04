from manufacture.IndustryEnum import IndustryRigZoneCoefficient, IndustryRigMaterialEfficiency, \
    IndustryStructureMaterialEfficiency
from manufacture.IndustryHelper import IndustryHelper
from util.QueryConsole import queryConsole


class IndustryFacade:
    def __init__(self):
        self.industryHelper = IndustryHelper()

    def industryCalculatorEntry(self, productName: str, quantity: int, materialEfficiency: int,
                                manufacturingStructure: str,
                                manufacturingRig: str, reactionStructure: str, reactionRig: str, solarSystem: str,
                                baseMaterialEfficiency=10, numberOfProcess=0, decomposeReaction=True,
                                decomposeFuelBlocks=False):
        typeID, language = queryConsole.getExactProductID(productName)
        assert typeID != -1
        blueprint = queryConsole.getBlueprint(typeID)
        assert len(blueprint) > 0, "该物品不可建造"
        solarSystem = queryConsole.getSolarSystem(solarSystem)
        assert len(solarSystem) != 0

        zoneCoefficient = 0
        if solarSystem["security"] > 0.5:
            zoneCoefficient = IndustryRigZoneCoefficient.Highsec.value
        elif solarSystem["security"] > 0:
            zoneCoefficient = IndustryRigZoneCoefficient.Lowsec.value
        elif solarSystem["security"] <= 0:
            zoneCoefficient = IndustryRigZoneCoefficient.Zerosec.value
        if numberOfProcess == 0:
            numberOfProcess = queryConsole.getMaxRuns(queryConsole.getBlueprint(typeID)["typeID"])
        materialEfficiency = materialEfficiency / 100
        baseMaterialEfficiency = baseMaterialEfficiency / 100
        rigMaterialEfficiency = getattr(IndustryRigMaterialEfficiency, manufacturingRig).value * zoneCoefficient
        structureMaterialEfficiency = getattr(IndustryStructureMaterialEfficiency, manufacturingStructure).value
        reactionEfficiency = getattr(IndustryRigMaterialEfficiency, reactionRig).value

        intermediateProducts, rawMaterials, manufacturingChain, materialTree = \
            self.industryHelper.processDecompose(typeID, quantity, numberOfProcess, materialEfficiency,
                                                 baseMaterialEfficiency, rigMaterialEfficiency,
                                                 structureMaterialEfficiency, reactionEfficiency)
        intermediateProducts = [(queryConsole.ID2Word(_[0], language)["text"], _[1]) for _ in
                                intermediateProducts.items()]
        rawMaterials = [(queryConsole.ID2Word(_[0], language)["text"], _[1]) for _ in rawMaterials.items()]
        manufacturingChain = [{"产物": queryConsole.ID2Word(_["product"], language)["text"], "数量": _["quantity"],
                               "原料": [(queryConsole.ID2Word(temp[0], language)["text"], temp[1]) for temp in
                                      _["materials"]]}
                              for _ in reversed(manufacturingChain)]
        return intermediateProducts, rawMaterials, manufacturingChain, materialTree


industry = IndustryFacade()
intermediate, raw, chain, _ = industry.industryCalculatorEntry("神使级", 1, 9, "Sotiyo", "T1", "Tatara", "T2",
                                                               "k8x")
for item in intermediate:
    print(item)
for item in raw:
    print(item)
for item in chain:
    print(item)
