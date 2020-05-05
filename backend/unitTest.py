from _lib import *
from _lib.eth import Eth
from _lib.btc import Btc
from _lib.usdt import Usdt
from _lib.coin import Coin
from _lib.sql import Sql
from _lib.log import Log
import threading


queue = Queue(1000)
log = Log(queue)

sqlObj = Sql(queue)
btcObj = Btc(log)
ethObj = Eth(log)
usdtObj = Usdt(log)
coinObj = Coin("Asset", log)

if __name__ == "__main__":
    print(Cfg.PATH_SQLLITE)
    sqlObj.daemon = True
    sqlObj.start()

    # usdtObj.daemon = True
    # usdtObj.start()
    # usdtObj.join()

    ethObj.daemon = True
    ethObj.start()
    ethObj.join()
    if ethObj.exception:
        error = ethObj.exception
        print("MainProcess: ", error)

    # btcObj.daemon = True
    # btcObj.start()
    # btcObj.join()
    # if btcObj.exception:
    #     error = btcObj.exception
    #     print("MainProcess: ", error)

    # coinObj.daemon = True
    # coinObj.start()
    # coinObj.join()
    # if coinObj.exception:
    #     error = coinObj.exception
    #     print("MainProcess: ", error)

    sqlObj.join()
