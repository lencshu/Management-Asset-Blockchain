from _lib import *
from _lib.coin import Coin


coin=Coin()
async def main():
    tasks = [asyncio.create_task(coin.emailSendPy("110", "10", "sepoc", iAddr)) for iAddr in Cfg.SMTP_DST_ADDR_DEPOSIT]
    for iTask in asyncio.as_completed(tasks):
        status, resultSend = await iTask
        print(resultSend)

loop=asyncio.get_event_loop()
loop.run_until_complete(main())



# from datetime import datetime
# from typing import List

# from pydantic import BaseModel


# class User(BaseModel):
#     id: int
#     name = "John Doe"
#     signup_ts: datetime = None
#     friends: List[int] = []


# external_data = {
#     "id": "123",
#     "signup_ts": "2017-06-01 12:22",
#     "friends": [1, "2", b"3"],
# }
# user = User(**external_data)
# print(user)

# from enum import Enum, unique
# @unique
# class Order(Enum):
#     SQL = 0
#     BTC = 1
#     ETH = 2
#     USDT = 3
#     ASSET = 4

# print(Order['SQL'].value)
# import asyncio
# from multiprocessing import Process, Queue, Manager
# import aiohttp

# class ApiError(Exception):
#     pass

# from _lib import *

# class Proc(Process):
#     def __init__(self):
#         super(Proc,self).__init__(name="P")
#     def aa(self):
#         raise ApiError("sadsa")

#     def bb(self):
#         self.aa()

#     def run(self):
#         self.bb()

#     @property
#     def exception(self):
#         return None

# proc=Proc()
# try:
#     proc.start()
#     proc.join()
#     print(proc.exception)
# except ApiError as e:
#     print(repr(e))




# try:
#     cc()
# except Exception as e:
#     print(repr(e))

# async def printTask(input):
#     await asyncio.sleep(2)
#     print(input)


# step = 10


# # def listgen(start, end):
# #     listAll = []
# #     print(start, end - (end % step))
# #     for i in range(start, end - (end % step)):
# #         listAll.append(asyncio.ensure_future(printTask(i)))
# #         if (i - start) % step == 0:
# #             yield listAll
# #             listAll = []
# #     else:
# #         listAll = []
# #         for i in range(end - end % step, end):
# #             listAll.append(asyncio.ensure_future(printTask(i)))
# #         yield listAll


# def listgen(start, end):
#     listAll = []
#     for i in range(start, end + 1):
#         listAll.append(asyncio.ensure_future(printTask(i)))
#         if i % step == 0 or i == end:
#             yield listAll
#             listAll = []


# async def main():
#     a = listgen(1, 38)
#     for i in a:
#         for ii in asyncio.as_completed(i):
#             await ii


# async def main():
#     post_data={'jsonrpc': '2.0', 'method': 'omni_getbalance', 'params': ['1G3AFPCo4J5GXbSKPhW1r1VzqnwQUJf5pR', 31], 'id': 1}
#     async with aiohttp.ClientSession() as session:
#         idAuth = aiohttp.BasicAuth(Cfg.USDT_USR, Cfg.USDT_PWD)
#         P_post = await session.post(Cfg.USDT_HOST, json=post_data, auth=idAuth)
#         if P_post.status in [200, 201]:
#             rst = json.loads(await P_post.text())
#             if "result" in rst:
#                 return rst["result"]
#             else:
#                 return None

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())



# from _lib.eth import Eth
# from _lib.btc import Btc
# from _lib.usdt import Usdt
# from _lib.coin import Coin
# from _lib.sql import Sql
# from _lib.log import Log
# from _lib.processCtrl import ProcessCtrl

# queueM = Queue(1000)
# processCtrl=ProcessCtrl(queueM)

# queue = Queue(1000)
# log = Log(queue)

# sqlObj = Sql(queue)
# btcObj = Btc(log)
# ethObj = Eth(log)
# usdtObj = Usdt(log)
# coinObj = Coin("Coin", log)

# processList = []
# processList.append([True, btcObj, Btc, log, 5])
# processList.append([True, sqlObj, Sql, queue, 5])
# processList.append([True, ethObj, Eth, log, 5])
# processList.append([True, usdtObj, Usdt, log, 5])
# processList.append([True, coinObj, Coin, ("Coin", log), 5])
# processCtrl.processList=processList
# processCtrl.start()
# time.sleep(50)

# import time
# from multiprocessing import Process,Queue,Manager


# import asyncio
# from functools import wraps, partial

# # # import uvloop


# # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
# loop = asyncio.get_event_loop()


# def timer(func=None, interval=60):
#     if func is None:
#         return partial(timer, interval=interval)

#     @wraps(func)
#     async def decorated(*args, **kwargs):
#         while True:
#             await asyncio.sleep(interval)
#             await func(*args, **kwargs)
#     return loop.create_task(decorated())


# @timer(interval=1)
# async def func1():
#     print(1)


# @timer(interval=5)
# async def func2():
#     print(2)


# loop.run_forever()


# from apscheduler.schedulers.background import BackgroundScheduler

# class Btc(Process):
#     lastRunTime = 0
#     def __init__(self):
#         self.__class__.lastRunTime = time.time()
#         super(Btc, self).__init__(name="Btc")

#     def run(self):
#         # self.__class__.lastRunTime = time.time()
#         print(f"inside {self.__class__.lastRunTime}")


# def addd(varGlo):
#     varGlo+=1


# from datetime import datetime
# import time

# from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
# from apscheduler.schedulers.background import BackgroundScheduler


# def tick(listGlb):
#     print("Tick! The time is: %s" % datetime.now())
#     listGlb[0][0]=listGlb[0][0]+1
#     print(listGlb[0][0])


# if __name__ == "__main__":
#     queueA=Queue(10)
#     queueB=Queue(10)
#     queueA.put(queueB)
#     mge=Manager()
#     listGlb=mge.list()
#     listGlb.append(mge.list([1]))
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(tick, "interval",args=(listGlb,), seconds=1)
#     scheduler.start()

#     try:
#         while True:
#             print(listGlb)
#             time.sleep(1)
#     except (KeyboardInterrupt, SystemExit):
#         scheduler.shutdown()


# btc=Btc()
# print(Btc.lastRunTime)
# # btc.start()
# # print(Btc.lastRunTime)
# btc=Btc()
# print(Btc.lastRunTime)
# btc.start()
# print(Btc.lastRunTime)


# a=[[1,"info","checkNewTxBTC","1",1585349194.2620656],[2,"info","checkNewTxBTC","2",1585349194.452127]]
# dictData={}
# for iList in a:
#     try:
#         dictData[iList[1]][iList[0]]=[iList[2],iList[3],iList[4]]
#     except:
#         dictData[iList[1]]={}
#         dictData[iList[1]][iList[0]]=[iList[2],iList[3],iList[4]]
# print(dictData)
# time.sleep(2)
# # dictData={{iList[1]:{iList[0]:[iList[2],iList[3],iList[4]]}} for iList in a}


# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# async def root():
#     return {"message": "Hello dasd World"}


# import aiohttp
# import asyncio,json,sys
# import logging

# def log(data):
#     def err(data):
#         print("err"+data)


# log.err("ok")


# def timeit(func):
#     def run(*argv):
#         print(func.__name__)
#         if argv:
#             ret = func(*argv)
#         else:
#             ret = func()
#         return ret
#     return run

# async def main(method,params):
#     print(f"{self.tableName}.{sys._getframe().f_code.co_name}")
#     # headers = {"Content-Type": "application/json", "Connection": "close"}
#     post_data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
#     # encode_json = json.dumps(post_data)
#     async with aiohttp.ClientSession() as session:
#         P_post = await session.post("https://mainnet.infura.io/v3/cda0e04bdae5451cacb715bd22991427", json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1})
#         # P_post = await session.post("http://18.204.2.103:17077", json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1})

#         print(P_post.status,json.loads(await P_post.text()))


# if __name__ == "__main__":
#     loop = asyncio.get_event_loop()
#     asyncio.ensure_future(main("eth_blockNumber", []))
#     loop.run_forever()
