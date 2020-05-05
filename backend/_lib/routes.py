from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from functools import wraps, partial
import threading
import random

# from apscheduler.schedulers.background import BackgroundScheduler

from _lib.eth import Eth
from _lib.btc import Btc
from _lib.usdt import Usdt
from _lib.coin import Coin
from _lib.sql import Sql
from _lib.log import Log
from _lib.config import Order
from _lib import *

# processLoop = asyncio.get_event_loop()

apis = APIRouter()

queue = Queue(1000)
log = Log(queue)

sqlObj = Sql(queue)
btcObj = Btc(log)
ethObj = Eth(log)
usdtObj = Usdt(log)
coinObj = Coin("Asset", log)

logData = []
processList = []
processList.append([True, sqlObj, Sql, queue, Cfg.sqlObj_TIMING])
processList.append([True, btcObj, Btc, log, Cfg.btcObj_TIMING])
processList.append([True, ethObj, Eth, log, Cfg.ethObj_TIMING])
processList.append([True, usdtObj, Usdt, log, Cfg.usdtObj_TIMING])
processList.append([True, coinObj, Coin, ("Asset", log), Cfg.coinObj_TIMING])


# def timer(func=None, interval=60):
#     if func is None:
#         return partial(timer, interval=interval)

#     @wraps(func)
#     async def decorated(*args, **kwargs):
#         while True:
#             await asyncio.sleep(interval)
#             await func(*args, **kwargs)

#     return processLoop.create_task(decorated())


class DatePicker(BaseModel):
    start: float = None
    end: float = None


async def readSql(tableName, datePicker=None):
    global logData
    condition = ""
    if datePicker:
        condition = f"WHERE {datePicker.start} < timestamp AND timestamp < {datePicker.end}"
    query = f"SELECT * FROM {tableName} {condition}"
    async with aiosqlite.connect(Cfg.PATH_SQLLITE) as db:
        async with db.execute(query) as cursor:
            logData = await cursor.fetchall()


async def stopProcess(processList, orderP=None):
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


async def startProcessUnit(iProcess):
    flagActive, processObj, className, classArg, timingInterval = iProcess
    if not flagActive:
        print(f"False, No Starting {processObj._name}")
        return {processObj._name: processObj.is_alive()}, (False, processObj, className, classArg, timingInterval)
    try:
        print(f"{processObj._name}: {processObj.is_alive()}")
    except Exception:
        processObj.daemon = True
        processObj.start()
        print("Process init")
    if processObj.exception:
        print(f"error, No Starting {processObj._name}")
        return {processObj._name: processObj.is_alive()}, (False, processObj, className, classArg, timingInterval)
    if not processObj.is_alive():
        print(f"starting {processObj._name}")
        if isinstance(classArg, tuple):
            tableN, logN = classArg
            processObj = className(tableN, logN)
        else:
            processObj = className(classArg)
        processObj.daemon = True
        processObj.start()
    print(f"{processObj._name}: {processObj.is_alive()}")
    return {processObj._name: processObj.is_alive()}, (flagActive, processObj, className, classArg, timingInterval)


processloop = asyncio.new_event_loop()


def loopProcessThread(loop):
    global processList
    asyncio.set_event_loop(loop)
    # tasks=[]
    # tasks = []
    # for iResult in allresult:
    #     tasks.append(asyncio.ensure_future(self.checkNewTxBTCUnit(iResult, tx_hash_all)))
    # for iTask in asyncio.as_completed(tasks):
    #     await iTask
    async def startProcessTimingUnit(index, timingInterval, processList):
        await asyncio.sleep(timingInterval)
        status, processList[index] = await startProcessUnit(processList[index])

    async def startProcessTimingAll(processList):
        sem = asyncio.Semaphore(5)
        while True:
            tasks = []
            for index, iProcess in enumerate(processList):
                flagActive, processObj, className, classArg, timingInterval = iProcess
                status = f"{processObj._name} checking"
                if flagActive:
                    tasks.append(asyncio.ensure_future(startProcessTimingUnit(index, timingInterval, processList)))
                    # await startProcessTimingUnit(index,timingInterval,processList)
            for iTask in asyncio.as_completed(tasks):
                await iTask

    # loop.run_forever()
    # future = asyncio.gather(startProcessTimingAll(processList))
    # future = asyncio.gather(tasks)
    loop.run_until_complete(startProcessTimingAll(processList))


loopThread = threading.Thread(target=loopProcessThread, args=(processloop,))
loopThread.daemon = True
loopThread.start()


@apis.get("/")
async def index():
    return FileResponse("./dists/index.html")


@apis.get("/api/")
async def root():
    return {"message": "Hello World"}


@apis.post("/api/read/{tableName}")
async def readPost(tableName: str, datePicker: DatePicker):
    await readSql(tableName, datePicker)
    return {"result": logData}


@apis.get("/api/status")
async def getStatus():
    global processList
    status = {}
    for iProcess in range(len(processList)):
        flagActive, processObj, className, classArg, timingInterval = processList[iProcess]
        if processObj.exception:
            # print(f"errorApi, No Starting {processObj._name}")
            processList[iProcess] = (False, processObj, className, classArg, timingInterval)
            flagActive, processObj, className, classArg, timingInterval = processList[iProcess]
        status[processObj._name] = {}
        status[processObj._name]["name"] = processObj._name
        status[processObj._name]["active"] = flagActive
        status[processObj._name]["alive"] = processObj.is_alive()
        status[processObj._name]["lastRun"] = className.lastRunTime
        status[processObj._name]["progress"] = round((100 * (time.time() - className.lastRunTime) / Cfg.LIST_TIMING[Order[processObj._name.upper()].value]) % 100, 3)
        # status[processObj._name]["progress"] = random.randint(0, 100)
    return {"status": status}


@apis.get("/api/read/{tableName}")
async def readGet(tableName: str, background_tasks: BackgroundTasks):
    # background_tasks.add_task(readSql,tableName)
    await readSql(tableName)
    return {"result": logData}


@apis.get("/api/readclass/{tableName}")
async def readClass(tableName: str, background_tasks: BackgroundTasks):
    # background_tasks.add_task(readSql,tableName)
    await readSql(tableName)
    dictData = {}
    for iList in logData:
        try:
            dictData[iList[1]][iList[0]] = [iList[2], iList[3], iList[4]]
        except:
            dictData[iList[1]] = {}
            dictData[iList[1]][iList[0]] = [iList[2], iList[3], iList[4]]
    return {"result": dictData}


@apis.get("/api/start")
async def start(background_tasks: BackgroundTasks):
    global processList
    resp = []
    for index, iProcess in enumerate(processList):
        # for iProcess in range(len(processList)):
        flagActive, processObj, className, classArg, timingInterval = iProcess
        status = f"{processObj._name} is not actived"
        if flagActive:
            status, processList[index] = await startProcessUnit(iProcess)
        resp.append(status)
    return resp


@apis.get("/api/stop/{processName}")
async def stop(processName: str):
    global processList
    if processName.lower() not in ["sql", "btc", "eth", "asset", "usdt"]:
        processName = None
    resp = await stopProcess(processList, processName)
    status = [{item[1]._name: item[0]} for item in processList]
    return {"result": resp, "status": status}


# print(Cfg.__dict__)
# print(str(os.getpid()))
