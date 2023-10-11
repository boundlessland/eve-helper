from datetime import datetime

from util import DataLoader, Dao
import os
import subprocess

from util.EVEApi import EVEApiHandler


class Initializer:
    resourceName = ""
    sqlConfig = {}
    sqlDir = ""

    def __init__(self, sqlConfigPath):
        self.sqlConfig = DataLoader.loadConfigFromJSON(sqlConfigPath)

    def initialize(self):
        self.preInitialize()
        self.checkAndInitialize()

    def SQLFileExec(self, filepath: str):
        # 使用subprocess执行SQL文件并捕获输出结果
        print(filepath + " " + "initializing")
        process = subprocess.Popen(['mysql', '-u', self.sqlConfig["user"], '-p%s' % self.sqlConfig["password"],
                                    '-h', self.sqlConfig["host"], '-D', self.resourceName,
                                    "--default-character-set=utf8"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        output, error = process.communicate(("source " + filepath).encode("utf-8"))
        if error:
            print(error.decode())
            return False
        else:
            return True

    def preInitialize(self):
        pass

    def checkAndInitialize(self):
        pass


class BaseInitializer(Initializer):
    def __init__(self, sqlConfigPath):
        super().__init__(sqlConfigPath)
        self.resourceName = "eve-base"
        self.sqlDir = "resources/" + self.resourceName

    def preInitialize(self):
        existingDatabase = Dao.getDatabaseNames(self.sqlConfig)
        if self.resourceName not in existingDatabase:
            Dao.createDatabase(self.sqlConfig, self.resourceName)
        return

    def checkAndInitialize(self):
        existingTable = Dao.getTableNames(self.sqlConfig, self.resourceName)
        for filename in os.listdir(self.sqlDir):
            if filename.endswith(".sql"):
                if filename[:-4].lower() not in existingTable:
                    filepath = os.path.join(self.sqlDir, filename)
                    result = self.SQLFileExec(filepath)
                    if result:
                        print("%s is initialized" % filename)
                    else:
                        print("%s initializing failed" % filename)
        return


class DailyInitializer(Initializer):
    def __init__(self, sqlConfigPath):
        super().__init__(sqlConfigPath)
        self.resourceName = "eve-daily"
        self.sqlDir = "resources/" + self.resourceName
        self.api = EVEApiHandler("config/EVEApiConfig.json")
        self.interval = 86400

    def preInitialize(self):
        existingDatabase = Dao.getDatabaseNames(self.sqlConfig)
        if self.resourceName not in existingDatabase:
            Dao.createDatabase(self.sqlConfig, self.resourceName)
        return

    def isOutdated(self, time):
        now = datetime.now()
        delta = (now - time).total_seconds()
        if delta > self.interval:
            return True
        else:
            return False

    def checkAndInitialize(self):
        existingTable = Dao.getTableNames(self.sqlConfig, self.resourceName)
        for filename in os.listdir(self.sqlDir):
            if filename.endswith(".sql"):
                tableName = filename[:-4]
                if tableName.lower() not in existingTable:
                    filepath = os.path.join(self.sqlDir, filename)
                    result = self.SQLFileExec(filepath)
                    if result:
                        print("%s is initialized" % filename)
                    else:
                        print("%s initializing failed" % filename)
                sample = Dao.randomSelect(self.sqlConfig, self.resourceName, tableName, 1, ["updateTime"])
                columns = Dao.getTableColumns(self.sqlConfig, self.resourceName, tableName)
                if len(sample) == 0 or self.isOutdated(sample[0][0]):
                    Dao.deleteAll(self.sqlConfig, self.resourceName, tableName)
                    method = getattr(self.api, "get" + tableName)
                    result, values = method(), []
                    for res in result:
                        values.append([res[c] for c in columns])
                    Dao.insert(self.sqlConfig, self.resourceName, tableName, columns, values)
        return


BaseInitializer('config/MySQLConfig.json').initialize()
DailyInitializer('config/MySQLConfig.json').initialize()
