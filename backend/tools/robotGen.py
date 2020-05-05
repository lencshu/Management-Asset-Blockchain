import time
import requests, json
import random

# import threading
# from threading import Thread
# from multiprocessing import Process
import aiohttp
import asyncio

sem = asyncio.Semaphore(1)

ROBOT_API = "http://47.56.174.107/api/register/robot-register2"

async def callRobotApi():
    # await asyncio.sleep(random.random()*50)
    async with sem:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(ROBOT_API) as P_get:
                    if P_get.status in [200, 201]:
                        dataGet = json.loads(await P_get.text(encoding="utf8"))
                        return dataGet["data"]
                    else:
                        errMsg = f"{P_get.host} - {P_get.status} - {P_get.reason}"
                        return None
            except Exception as e:
                print(e)


async def main():
    tasks = [asyncio.create_task(callRobotApi()) for i in range(3000)]
    for iTask in asyncio.as_completed(tasks):
        resp = await iTask
        print(resp)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


"""

def main():
    for i in range(3000):
        reponse=requests.get('http://161.117.231.228:8082/api/register/robot-register2')
        print(json.loads(reponse.text)["data"]["user"])

# url='http://161.117.231.228:8082/api/register/robot-register2'

# process_list = []
# for i in range(5):
#     p = Process(target=requests.get,args=(url,)) #实例化进程对象
#     p.start()
#     process_list.append(p)



# threads = []
# for i in range(10):
#     t = Thread(target=main)
#     t.start()
#     threads.append(t)


timeStart=time.time()
main()
# for i in process_list:
#     p.join()
# for t in threads:
#     t.join()
print(f"time: {time.time()-timeStart}")


import asyncio
import time
from aiohttp import ClientSession

async def getRobot(url,waitTime):
    async with ClientSession() as session:
        asyncio.sleep(waitTime)
        async with session.get(url) as response:
            response = await response.read()
            print(response)


loop = asyncio.get_event_loop()
url = 'http://161.117.231.228:8082/api/register/robot-register2'
tasks = []
for i in range(10):
    task = asyncio.ensure_future(getRobot(url,i))
    tasks.append(task)


timeStart=time.time()
loop.run_until_complete(asyncio.wait(tasks))
print(f"time: {time.time()-timeStart}") """
