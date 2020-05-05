from _lib import *


class Log:
    def __init__(self, lQueue):
        self.lQueue = lQueue.put

    def err(self, tableName, funcName, logData):
        self.lQueue((tableName, "err", funcName, str(logData), time.time()))

    def info(self, tableName, funcName, logData):
        self.lQueue((tableName, "info", funcName, str(logData), time.time()))

    def success(self, tableName, funcName, logData):
        self.lQueue((tableName, "success", funcName, str(logData), time.time()))
