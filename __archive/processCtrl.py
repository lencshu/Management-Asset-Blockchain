from _lib import *
from _lib.config import Cfg
from _lib.eth import Eth
from _lib.btc import Btc
from _lib.usdt import Usdt
from _lib.coin import Coin
from _lib.sql import Sql
from _lib.log import Log
from _lib.config import Order


def timer(func=None, interval=60):
    if func is None:
        return partial(timer, interval=interval)

    @wraps(func)
    async def decorated(*args, **kwargs):
        while True:
            await asyncio.sleep(interval, loop=processLoop)
            await func(*args, **kwargs)

    return asyncio.ensure_future(decorated())


class ProcessCtrl(Process):
    lastRunTime = 0

    def __init__(self, lQueue):
        super(ProcessCtrl, self).__init__(name="Process_Ctrl")
        self.tableName = "ASSET"
        self.__class__.lastRunTime = time.time()
        self.lQueue = lQueue
        # self.log = None
        self.processList = []

    def run(self):
        loop = asyncio.get_event_loop()
        # asyncio.ensure_future(self.main(loopA))
        # loop.run_forever()
        loop.run_until_complete(self.main(loop))


    async def main(self, loop):
        startTime = time.time()
        for index, iProcess in enumerate(self.processList):
            flagActive, processObj, className, classArg, timingInterval = iProcess
            if isinstance(classArg, tuple):
                tableN, logN = classArg
                processObj = className(tableN, logN)
            else:
                processObj = className(classArg)
            processObj.daemon = True
            processObj.start()
            self.processList[index][1] = processObj
            print(f"{processObj._name} alive? {processObj.is_alive()}")
        await self.getStatus(self.processList)
        print(os.getgid())
        await self.getStatus(self.processList)
        print(f"used Time: {time.time()-startTime}")

    async def startProcessUnit(self, iProcess):
        flagActive, processObj, className, classArg, timingInterval = iProcess
        try:
            print(f"{processObj._name}: {processObj.is_alive()}")
        except Exception:
            processObj.daemon = True
            processObj.start()
            print("Process init")
        if not processObj.is_alive():
            print("starting processObj")
            if isinstance(classArg, tuple):
                tableN, logN = classArg
                processObj = className(tableN, logN)
            else:
                processObj = className(classArg)
            processObj.daemon = True
            processObj.start()
        print(f"{processObj._name}: {processObj.is_alive()}")
        return {processObj._name: processObj.is_alive()}, (True, processObj, className, classArg, timingInterval)

    async def stopProcess(self, processList, orderP=None):
        if orderP:
            orderP = orderP.upper()
        for iProcess in range(len(processList)):
            flagActive, processObj, className, classArg, timingInterval = processList[iProcess]
            print(f"{processObj._name} alive? {processObj.is_alive()}")
            if not orderP or iProcess == Order[orderP].value:
                try:
                    if processObj.is_alive():
                        if iProcess == Order["SQL"].value:
                            print(f"killing precess {orderP}")
                            processObj.terminate()
                        else:
                            print(f"waiting precess {orderP}")
                            processObj.join()
                except Exception as e:
                    print(e)
                processList[iProcess] = (False, processObj, className, classArg, timingInterval)
        return f"Process {orderP} terminated and disabled"

    async def startProcessTimingUnit(self, index, processList):
        flagActive, processObj, className, classArg, timingInterval = processList[index]
        # while True:
        # await asyncio.sleep(timingInterval)
        status, processList[index] = await self.startProcessUnit(processList[index])
        ptint(status)

    async def startProcessTiming(self, processList):
        # while True:
        for index, iProcess in enumerate(processList):
            flagActive, processObj, className, classArg, timingInterval = iProcess
            status = f"{processObj._name} is not actived"
            if flagActive:
                asyncio.ensure_future(self.startProcessTimingUnit(index, processList))

    async def getStatus(self, processList):
        status = {}
        for iProcess in range(len(processList)):
            # print(processList[iProcess])
            flagActive, processObj, className, classArg, timingInterval = processList[iProcess]
            status[processObj._name] = {}
            status[processObj._name]["alive"] = processObj.is_alive()
            status[processObj._name]["lastRun"] = className.lastRunTime
        print(status)
