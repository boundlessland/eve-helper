import pymysql


def getConnection(sqlConfig: dict, database=None, charset="utf8mb4", cursorClass=pymysql.cursors.SSCursor):
    # 创建数据库连接
    if database is None:
        connection = pymysql.connect(host=sqlConfig["host"], user=sqlConfig["user"],
                                     password=sqlConfig["password"], cursorclass=cursorClass,
                                     autocommit=sqlConfig["autocommit"])
    else:
        connection = pymysql.connect(host=sqlConfig["host"], user=sqlConfig["user"],
                                     password=sqlConfig["password"], database=database,
                                     charset=charset, cursorclass=cursorClass, autocommit=sqlConfig["autocommit"])
    return connection


def getTableNames(sqlConfig: dict, database: str):
    tables = []
    connection = getConnection(sqlConfig, database=database)
    try:
        with connection.cursor() as cursor:
            # 执行SQL查询获取所有表名
            sql = "SHOW TABLES"
            cursor.execute(sql)
            # 获取所有表名
            tables = [_[0] for _ in cursor.fetchall()]
    except Exception as e:
        print(e)
    finally:
        connection.close()
    return tables


def getDatabaseNames(sqlConfig: dict):
    databases = []
    connection = getConnection(sqlConfig)
    try:
        with connection.cursor() as cursor:
            # 执行SQL查询获取所有数据库名
            sql = "SHOW DATABASES"
            cursor.execute(sql)
            # 获取所有数据库名
            databases = [_[0] for _ in cursor.fetchall()]
    except Exception as e:
        print(e)
    finally:
        connection.close()
    return databases


def createDatabase(sqlConfig: dict, database: str):
    connection = getConnection(sqlConfig)
    try:
        with connection.cursor() as cursor:
            # 执行SQL创建数据库
            sql = f"CREATE DATABASE `%s`" % database
            cursor.execute(sql)
    except Exception as e:
        print(e)
    finally:
        connection.close()
    return


def randomSelect(sqlConfig: dict, database: str, table: str, limit: int, fields: list):
    result = []
    connection = getConnection(sqlConfig, database=database)
    try:
        with connection.cursor() as cursor:
            # 随机查询
            fmt = "{}," * len(fields)
            fields = fmt.format(*fields)[:-1]
            sql = "SELECT %s FROM %s LIMIT %d" % (fields, table, limit)
            cursor.execute(sql)
            result = cursor.fetchall()
    except Exception as e:
        print(e)
    finally:
        connection.close()
    return result


def getTableColumns(sqlConfig: dict, database: str, table: str):
    result = []
    connection = getConnection(sqlConfig, database=database)
    try:
        with connection.cursor() as cursor:
            # 执行SQL查询获取表结构
            sql = "SHOW COLUMNS FROM %s" % table
            cursor.execute(sql)
            # 获取所有列名
            result = [_[0] for _ in cursor.fetchall()]
    except Exception as e:
        print(e)
    finally:
        connection.close()
    return result


def insert(sqlConfig: dict, database: str, table: str, columns: list, values: list):
    connection = getConnection(sqlConfig, database=database)
    try:
        with connection.cursor() as cursor:
            fmt = "{}," * len(columns)
            columns = "(" + fmt.format(*columns)[:-1] + ")"
            for v in values:
                values = "(" + fmt.format(*v)[:-1] + ")"
                sql = "INSERT INTO %s %s VALUES %s" % (table, columns, values)
                cursor.execute(sql)
    except Exception as e:
        print(e)
    finally:
        connection.close()
    return


def deleteAll(sqlConfig: dict, database: str, table: str):
    connection = getConnection(sqlConfig, database=database)
    try:
        with connection.cursor() as cursor:
            # 清空表记录
            sql = "DELETE FROM %s" % table
            cursor.execute(sql)
    except Exception as e:
        print(e)
    finally:
        connection.close()
    return


def conditionalSelect(sqlConfig: dict, database: str, table: str, conditions: str, fields: list):
    result = []
    connection = getConnection(sqlConfig, database=database)
    try:
        with connection.cursor() as cursor:
            # 随机查询
            fmt = "{}," * len(fields)
            fields = fmt.format(*fields)[:-1]
            sql = "SELECT %s FROM %s WHERE %s" % (fields, table, conditions)
            cursor.execute(sql)
            result = cursor.fetchall()
    except Exception as e:
        print(e)
    finally:
        connection.close()
    return result
