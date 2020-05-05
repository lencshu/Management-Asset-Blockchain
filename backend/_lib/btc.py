from _lib import *
from _lib.coin import Coin
from functools import partial

sem_blockchaininfo = asyncio.Semaphore(Cfg.SEM_BLOCKCHAININFO)
sem_db = asyncio.Semaphore(Cfg.SEM_DB)

class Btc(Coin):
    lastRunTime = 0

    def __init__(self, log):
        self.__class__.lastRunTime = time.time()
        self.log = log
        self.tableName = "BTC"
        super(Btc, self).__init__(nameP="Btc")
        self._pconn, self._cconn = Pipe()
        self._exception = None

    def run(self):
        loop = asyncio.get_event_loop()
        # asyncio.ensure_future(self.main(loop))
        # print(os.getgid())
        loop.run_until_complete(self.main(loop))
        # loop.close()

    async def main(self, loop):
        try:
            startTime = time.time()
            self.pool = await aiomysql.create_pool(host=Cfg.DB_HOST_ADDR, port=Cfg.DB_PORT, user=Cfg.DB_USR, password=Cfg.DB_PWD, db=Cfg.DB_TABLE_NAME, loop=loop, charset="utf8", autocommit=True)
            tasks = []
            tasks.append(asyncio.ensure_future(self.checkNewTxBTC()))
            tasks.append(asyncio.ensure_future(self.checkPendingBTC()))
            for iTask in asyncio.as_completed(tasks):
                await iTask
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"used Time: {time.time()-startTime}")
        except ApiError as e:
            tb = traceback.format_exc()
            self._cconn.send(e)
        # self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "asdasd")

        # self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "111")
        # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "222")
        # self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "212313")
        # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", 11111)
        # self.logPut = partial(self.log, f"{self.tableName}.{sys._getframe().f_code.co_name}")
        # await asyncio.sleep(3)
        # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", 222)

        # await self.checkPendingBTC()
        # result = await self.btcGetTransactionByHash_blockchainInfo("000000000000000000076c612897c9cb481e7a8cb05f0310155d0cc47eae14fa")
        # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", result)
        # await self.checkNewTxBTC()

    @property
    def exception(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        return self._exception

    async def btcGetTransactionByHash_blockchainInfo(self, tx):
        # headers = {"user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36", "Content-Type": "application/json", "Connection": "close"}
        async with sem_blockchaininfo:
            async with aiohttp.ClientSession() as session:
                await asyncio.sleep(Cfg.SEM_BLOCKCHAININFO_TIMEWAITING)
                try:
                    host = f"{Cfg.BTC_HOST_CHECK}/{tx}"
                    async with session.get(host) as P_get:
                        if P_get.status in [200, 201]:
                            resultOnLine = json.loads(await P_get.text(encoding="utf8"))
                            if "block_height" in resultOnLine.keys():
                                return resultOnLine
                            else:
                                return None
                        else:
                            errMsg = f"{host} - {P_get.status} - {P_get.reason}"
                            self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", errMsg)
                            if P_get.status == 429:
                                raise ApiError("ApiError")
                            return None
                except ApiError:
                    raise
                except Exception as e:
                    self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",repr(e))
                    return None

    # 解析BTC交易数据，获取from，to，value，fee等
    def parsingTxBTC(self, tx, addrDbFrom="", addrDbTo=""):
        # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "BTC TX Analysis::")
        try:
            tx_froms = [i["prev_out"]["addr"] for i in tx["inputs"]]
        except Exception as e:
            self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",repr(e))
            return None
        tx_tos = []
        for j in tx["out"]:
            try:
                test = j["addr"]
                tx_tos.append(j)
            except:
                continue
        # tx_tos = [ for j in tx["out"]]
        if addrDbFrom in tx_froms and addrDbFrom in tx_tos:  # 支出
            tx_from = addrDbFrom
            tx_to = list(set(tx_tos).difference(set(tx_froms)))[0]
        elif addrDbFrom in tx_froms:
            tx_from = addrDbFrom
            tx_to = tx_tos[0] if addrDbTo == "" else addrDbTo
        else:
            tx_from = tx_froms[0] if addrDbTo == "" else addrDbTo
            tx_to = addrDbFrom
        # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "tx_from::" + tx_from)
        # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "tx_to::" + tx_to)
        input_values = [k["prev_out"]["value"] for k in tx["inputs"]]
        tx_from_input_value = sum(input_values)
        tx_out = []
        for j in tx["out"]:
            try:
                test = j["addr"]
                tx_out.append(j)
            except:
                continue
        for out in tx_out:
            if tx_to == out["addr"]:
                to_change = out
                break
            # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", list(out.values()))
            if out["addr"] != tx_from and out["addr"] != tx_to:
                continue
            if tx_from == out["addr"]:
                from_change = out
            else:
                to_change = out
        tx_to_value = to_change["value"]
        out_values = [x["value"] for x in tx_out]
        fee = sum(input_values) - sum(out_values)
        # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "tx_to_value::" + str(out["value"]))
        # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "fee::" + str(fee))
        tx_from_input_value = "%.8f" % float(float(tx_from_input_value) / 10 ** 8)
        tx_to_value = "%.8f" % float(float(tx_to_value) / 10 ** 8)
        fee = "%.8f" % float(float(fee) / 10 ** 8)
        if "block_height" in list(tx.keys()):
            return {"block_height": tx["block_height"], "tx_from": tx_from, "tx_from_input_value": tx_from_input_value, "tx_to": tx_to, "tx_to_value": tx_to_value, "fee": fee}
        else:
            return {"tx_from": tx_from, "tx_from_input_value": tx_from_input_value, "tx_to": tx_to, "tx_to_value": tx_to_value, "fee": fee}

    async def getFinalBalance_blockchainInfo(self, addr, coin_symbol="BTC"):
        # headers = {"user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36", "Content-Type": "application/json", "Connection": "close"}
        # headers=headers,
        host = f"{Cfg.BTC_HOST_CHECK}/{addr}"
        # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", host)
        async with sem_blockchaininfo:
            async with aiohttp.ClientSession() as session:
                await asyncio.sleep(Cfg.SEM_BLOCKCHAININFO_TIMEWAITING)
                try:
                    async with session.get(host) as P_get:
                        if P_get.status in [200, 201]:
                            rst = json.loads(await P_get.text(encoding="utf8"))
                            # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", rst["final_balance"])
                            if rst["final_balance"] > 0:
                                balance = "%.10f" % float(float(rst["final_balance"]) / 10 ** 8)
                                update_btc_balance_sql = "update jl_member_wallets set balance = %.12f where addr= '%s' and network = %d and coin_symbol = '%s'" % (float(balance), addr, Cfg.IF_TEST_NET, coin_symbol)
                                self.log.success(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", update_btc_balance_sql)
                                async with sem_db:
                                    await super(Btc, self).dbRun(self.pool, update_btc_balance_sql)
                            return rst["txs"]
                        else:
                            errMsg = f"{host} - {P_get.status} - {P_get.reason}"
                            self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", errMsg)
                            if P_get.reason.strip() == "Too Many Requests":
                                raise ApiError("ApiError")
                            return None
                except ApiError:
                    raise
                except Exception as e:
                    self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",repr(e))
                    return "timeout"

    async def checkPendingBTC(self):
        """
        获取jl_transaction_btc中的pending的交易
        """
        async with sem_db:
            resultsDB = await super(Btc, self).dbRun(self.pool, f"select id,tx_hash,tx_status,type,member_id,coin_symbol,`from`,`to`,value_dec,fee FROM jl_transaction_btc where tx_status = 'pending' and network = {Cfg.IF_TEST_NET} and coin_symbol = 'BTC'  order by id asc")
        count = len(resultsDB)
        if len(resultsDB) == 0:
            # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "0 BTC pending")
            return
        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "%s BTC pending" % count)
        for iResult in resultsDB:
            if iResult is None:
                # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "This is nnnnone!!!")
                continue
            tx = await self.btcGetTransactionByHash_blockchainInfo(iResult[1])
            # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", tx)
            if tx is None:
                continue
                tx_status = "fail"
                block = 0
                updated_at = int(time.time())
            else:
                if tx == "timeout":
                    continue
                tx_data = self.parsingTxBTC(tx, iResult[6], iResult[7])
                if not tx_data:
                    continue
                else:
                    block = tx_data["block_height"]
                    tx_status = "success"
                    updated_at = int(time.time())
            if tx_status == "success":
                if iResult[3] == 2:  # 2:充值 3:提现 4:场外交易
                    balance_dict = {"type": 1, "member_id": iResult[4], "coin_symbol": iResult[5], "addr": tx_data["tx_to"], "change": tx_data["tx_to_value"], "fee": 0.0, "detial": iResult[1], "detial_type": "chain", "network": Cfg.IF_TEST_NET}
                    async with sem_db:
                        await super(Btc, self).updateBalance(self.pool, balance_dict)
                elif iResult[3] == 3:  # 2:充值 3:提现 4:场外交易
                    change = "%.10f" % float(0.0 - float(tx_data["tx_to_value"]))
                    fee = "%.10f" % float(0.0 - float(tx_data["fee"]))
                    balance_dict = {"type": 10, "member_id": iResult[4], "coin_symbol": iResult[5], "addr": tx_data["tx_from"], "change": change, "fee": fee, "detial": iResult[1], "detial_type": "chain", "network": Cfg.IF_TEST_NET}
                    async with sem_db:
                        await super(Btc, self).updateBalance(self.pool, balance_dict)
                        await super(Btc, self).backupAssetStandAlone(self.pool, tx_to, iResult[1], "BTC", change)
            if tx_status == "fail":
                update_sql = "update jl_transaction_btc set tx_status = '%s', block = %d, updated_at = %d where tx_hash = '%s' and coin_symbol = 'BTC' " % (tx_status, block, updated_at, iResult[1])
            else:
                update_sql = "update jl_transaction_btc set tx_status = '%s', block = %d, updated_at = %d, value_dec = '%s', fee = '%s' where tx_hash = '%s' and coin_symbol = 'BTC' " % (tx_status, block, updated_at, str(tx_data["tx_to_value"]), str(tx_data["fee"]), iResult[1])
            self.log.success(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"update: {update_sql}")
            async with sem_db:
                await super(Btc, self).dbRun(self.pool, update_sql)

    async def checkNewTxBTCUnit(self, iResult, tx_hash_all):
        insert_transaction_sql = ""
        coin_symbol = iResult[-1].strip("_")
        if iResult is None:
            # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "This is nnnnone!!!")
            return None
        tx_log = await self.getFinalBalance_blockchainInfo(iResult[0], coin_symbol)
        if tx_log is None:
            # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "tx_log is nnnnone!!!")
            return None
        else:
            if tx_log == "timeout":
                # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "tx_log getFinalBalance_blockchainInfo err timeout!!!")
                return None
            if len(tx_log) == 0:
                # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "tx_log empty!!")
                return None
            for x in tx_log:
                insert_transaction_sql == ""
                if "block_height" not in x:
                    # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "block_height not yet, pending...")
                    continue
                # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", x["hash"])
                if x["hash"] in tx_hash_all:
                    # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "%s already in" % x["hash"])
                    continue
                tx_data = self.parsingTxBTC(x, iResult[0])
                if not tx_data:
                    continue
                tx_from = tx_data["tx_from"]
                tx_to = tx_data["tx_to"]
                tx_value = tx_data["tx_to_value"]
                tx_fee = tx_data["fee"]
                tx_type = 1
                if float(tx_value) < Cfg.BTC_ASSET_USR_SKIP:
                    # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "No valid min amount")
                    continue
                # 查属于平台的交易，且收款地址是平台地址
                if iResult[-1] in ["_BTC_"] and tx_to == iResult[0]:
                    # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "someone send BTC tx to bank...")
                    tx_type = 2
                    balance_dict = {"type": 1, "member_id": iResult[1], "coin_symbol": coin_symbol, "addr": tx_to, "change": tx_value, "fee": 0.0, "detial": x["hash"], "detial_type": "chain", "network": Cfg.IF_TEST_NET}
                    async with sem_db:
                        await super(Btc, self).updateBalance(self.pool, balance_dict)
                if insert_transaction_sql == "":
                    insert_transaction_sql = "(%d, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d, %d, 'success', '', %d, %d)" % (tx_type, iResult[1], coin_symbol, x["hash"], tx_from, "", tx_to, tx_value, tx_fee, "", "", x["time"], x["block_height"], int(time.time()), Cfg.IF_TEST_NET)
                else:
                    insert_transaction_sql = "%s, (%d, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d, %d, 'success', '', %d, %d)" % (insert_transaction_sql, tx_type, iResult[1], coin_symbol, x["hash"], tx_from, "", tx_to, tx_value, tx_fee, "", "", x["time"], x["block_height"], int(time.time()), Cfg.IF_TEST_NET)
                if insert_transaction_sql != "":
                    insert_sql = "insert into jl_transaction_btc(type,member_id,coin_symbol,tx_hash,`from`,input,`to`,value_dec,fee,`data`,raw,created_at,block,tx_status,rpc_response,updated_at,network) values %s" % insert_transaction_sql
                    self.log.success(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", insert_sql)
                    await super(Btc, self).backupAssetStandAlone(self.pool, tx_to, iResult[1], coin_symbol, tx_value)
                    async with sem_db:
                        await super(Btc, self).dbRun(self.pool, insert_sql)

    async def checkNewTxBTC(self):
        """ 查询BTC地址历史交易"""
        async with sem_db:
            allresult = await super(Btc, self).dbRun(self.pool, f"select addr,uid,block,coin_symbol from jl_member_wallets where coin_symbol in ('BTC','_BTC_') and network = {Cfg.IF_TEST_NET} order by id asc")
            # self.log.info(self.tableName,f"{self.tableName}.{sys._getframe().f_code.co_name}", "%s btc addr" % len(allresult))
            tx_hash_all = await super(Btc, self).dbRun(self.pool, f"select tx_hash from jl_transaction_btc where tx_hash is not null and coin_symbol = 'BTC' and network = {Cfg.IF_TEST_NET}")
        tx_hash_all = [x[0] for x in tx_hash_all]
        nbChecked = 0
        tasks = []
        for iResult in allresult:
            tasks.append(asyncio.ensure_future(self.checkNewTxBTCUnit(iResult, tx_hash_all)))
        for iTask in asyncio.as_completed(tasks):
            await iTask
            nbChecked += 1
            # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", nbChecked)
