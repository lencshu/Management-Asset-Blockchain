from _lib import *
from _lib.coin import Coin

sem_db = asyncio.Semaphore(Cfg.SEM_DB)

class Usdt(Coin):
    lastRunTime = 0
    
    def __init__(self, log):
        self.__class__.lastRunTime = time.time()
        self.log = log
        self.tableName = "USDT"
        super(Usdt, self).__init__(nameP="Usdt")
        self._exception = None

    @property
    def exception(self):
        return self._exception

    def run(self):
        loop = asyncio.get_event_loop()
        # asyncio.ensure_future(self.main(loop))
        # print(os.getgid())
        loop.run_until_complete(self.main(loop))
        # loop.close()

    async def main(self, loop):
        startTime = time.time()
        self.pool = await aiomysql.create_pool(host=Cfg.DB_HOST_ADDR, port=Cfg.DB_PORT, user=Cfg.DB_USR, password=Cfg.DB_PWD, db=Cfg.DB_TABLE_NAME, loop=loop, charset="utf8", autocommit=True)
        # await self.checkPendingUSDT()
        # self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "USDTasdfs")

        tasks = []
        tasks.append(asyncio.ensure_future(self.checkNewTxUSDT()))
        tasks.append(asyncio.ensure_future(self.checkPendingUSDT()))
        for iTask in asyncio.as_completed(tasks):
            await iTask

        # blockNowUSDT = await super(Usdt, self).dbRun(self.pool, "select detial from jl_extension where type = 'NOW_USDT_BLOCK'")
        # blockNowUSDT = int([k[0] for k in blockNowUSDT][0])
        # listTrades = await self.usdtListTransactions(20, blockNowUSDT)
        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",blockNowUSDT, listTrades)

        # await self.checkNewTxUSDT()

        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"used Time: {time.time()-startTime}")

    async def usdtGetTransactionByTxid(self, idTx):
        # headers = {"user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36", "Content-Type": "application/json", "Connection": "close"}
        async with aiohttp.ClientSession() as session:
            try:
                idAuth = aiohttp.BasicAuth(Cfg.USDT_USR, Cfg.USDT_PWD)
                async with session.post(Cfg.USDT_HOST, headers=headers, json={"jsonrpc": "2.0", "method": "omni_gettransaction", "params": [idTx], "id": 1}, auth=idAuth) as P_post:
                    if P_post.status in [200, 201]:
                        resultOnLine = json.loads(await P_post.text(encoding="utf8"))
                        if "result" in resultOnLine.keys():
                            return resultOnLine["result"]
                        else:
                            return None
                    else:
                        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"{P_post.status}")
                        return None
            except Exception as e:
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", e)
                return "timeout"

    def parsingTxUSDT(self, txDetails):
        """
        解析USDT交易数据，获取from，to，value，fee等
        """
        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "USDT TX Analysis::")
        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", txDetails)
        block_height = 0
        tx_from = 0
        tx_from_input_value = 0
        tx_to_value = 0
        tx_to = 0
        fee = 0
        if txDetails["valid"]:
            fee = txDetails["fee"]
            block_height = txDetails["block"]
            tx_from = txDetails["sendingaddress"]
            tx_from_input_value = txDetails["amount"] + fee
            tx_to_value = txDetails["amount"]
            tx_to = txDetails["referenceaddress"]

        return {"block_height": block_height, "tx_from": tx_from, "tx_from_input_value": tx_from_input_value, "tx_to": tx_to, "tx_to_value": tx_to_value, "fee": fee}

    async def checkPendingUSDT(self):
        """
        获取jl_transaction_btc中的pending的交易
        """
        async with sem_db:
            resultsDB = await super(Usdt, self).dbRun(self.pool, f"select id,tx_hash,tx_status,type,member_id,coin_symbol,`from`,`to`,value_dec,fee FROM jl_transaction_btc where tx_status = 'pending' and network = {Cfg.IF_TEST_NET} and coin_symbol = 'USDT'  order by id asc")
        if len(resultsDB) == 0:
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "No USDT pending")
            return
        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "%s USDT pending" % len(resultsDB))
        for iResult in resultsDB:
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", iResult)
            if iResult is None:
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "This is nnnnone!!!")
                continue
            txDetails = await self.usdtGetTransactionByTxid(iResult[1])
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", txDetails)
            if txDetails is None:
                tx_status = "fail"
                block = 0
                updated_at = int(time.time())
            else:
                if txDetails == "timeout":
                    continue
                tx_data = self.parsingTxUSDT(txDetails)
                if tx_data["block_height"] == 0:
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "pending")
                    tx_status = "pending"
                    continue
                elif txDetails["confirmations"] < Cfg.Cfg.CONFIRMATION_SUCCESS:
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "pending")
                    tx_status = "pending"
                    continue
                else:
                    block = tx_data["block_height"]
                    tx_status = "success"
                    updated_at = int(time.time())
            if tx_status == "success":
                if iResult[3] == 2:  # 2:充值 3:提现 4:场外交易
                    balance_dict = {"type": 1, "member_id": iResult[4], "coin_symbol": iResult[5], "addr": tx_data["tx_to"], "change": tx_data["tx_to_value"], "fee": 0.0, "detial": iResult[1], "detial_type": "chain", "network": Cfg.IF_TEST_NET}
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"deposit success, balance_dict: {balance_dict}")
                    await super(Usdt, self).updateBalance(self.pool, balance_dict)
                    await super(Usdt, self).backupAssetStandAlone(self.pool, tx_data["tx_to"], iResult[4], "USDT", tx_data)
                elif iResult[3] == 3:  # 2:充值 3:提现 4:场外交易
                    change = "%.10f" % float(0.0 - float(tx_data["tx_to_value"]))
                    fee = "%.10f" % float(0.0 - float(tx_data["fee"]))
                    balance_dict = {"type": 10, "member_id": iResult[4], "coin_symbol": iResult[5], "addr": tx_data["tx_from"], "change": change, "fee": fee, "detial": iResult[1], "detial_type": "chain", "network": Cfg.IF_TEST_NET}
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"withdraw success,balance_dict: {balance_dict}")
                    await super(Usdt, self).updateBalance(self.pool, balance_dict)
                    # 申请单状状态【1：待审核、2：审核通过、3：未通过、4：提现失败、5：链上待确认、6：操作处理中】
                    async with sem_db:
                        applysWithdraw = await super(Usdt, self).dbRun(self.pool, "select id,member_id,coin_symbol,addr,value_dec,current,withdraw_fee,pay_from,tx_hash from jl_withdraw_apply where status = 5 ")
                        for iApply in applysWithdraw:
                            if iApply[8] == iResult[1]:
                                await super(Usdt, self).dbRun(self.pool, "update jl_withdraw_apply set status = {} where tx_hash = '{}'".format(2, iResult[1]))
                                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "success withdraw 5->2, write into jl_withdraw_apply")
            if tx_status == "fail":
                update_sql = "update jl_transaction_btc set tx_status = '%s', block = %d, updated_at = %d where tx_hash = '%s' and coin_symbol = 'USDT' " % (tx_status, block, updated_at, iResult[1])
            else:
                update_sql = "update jl_transaction_btc set tx_status = '%s', block = %d, updated_at = %d, value_dec = '%s', fee = '%s' where tx_hash = '%s' and coin_symbol = 'USDT' " % (tx_status, block, updated_at, str(tx_data["tx_to_value"]), str(tx_data["fee"]), iResult[1])
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", update_sql)
            async with sem_db:
                await super(Usdt, self).dbRun(self.pool, update_sql)

    async def usdtListTransactions(self, nbBlock, startBlock):
        """根据coin_symbol用rpc命令与热钱包交互"""
        # headers = {"Content-Type": "application/json", "Connection": "close"}
        # headers=headers,
        async with aiohttp.ClientSession() as session:
            try:
                idAuth = aiohttp.BasicAuth(Cfg.USDT_USR, Cfg.USDT_PWD)
                jsonData = {"jsonrpc": "2.0", "method": "omni_listtransactions", "params": ["*", nbBlock, 0, startBlock], "id": 1}
                async with session.post(Cfg.USDT_HOST, json=jsonData, auth=idAuth) as P_post:
                    if P_post.status in [200, 201]:
                        rst = json.loads(await P_post.text(encoding="utf8"))
                        if "result" in rst:
                            return rst["result"]
                        else:
                            return None
                    else:
                        errMsg = f"{P_post.host} - {P_post.status} - {P_post.reason}"
                        self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", errMsg)
                        return None
            except Exception as e:
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", e)
                return None

    async def checkNewTxUSDTUnit(self, iResult, iTrade):
        insert_transaction_sql = ""
        if iTrade["referenceaddress"] == iResult[0]:
            # 充值
            tx_type = 2
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "seposit USDT to Sepoch {}".format(iResult))
        elif iTrade["sendingaddress"] == iResult[0]:
            # 提币
            tx_type = 3
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "withdraw USDT:{}".format(iResult))
        if tx_type:
            if iTrade["confirmations"] < Cfg.CONFIRMATION_SUCCESS:
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "{} < 6, pending,UID:{}".format(["txid"], iResult[1]))
                insert_transaction_sql = "(%d, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d, %d, 'pending', '', %d, %d)" % (tx_type, iResult[1], "USDT", iTrade["txid"], tx_from, "", tx_to, tx_value, tx_fee, "", "", iTrade["blocktime"], iTrade["block"], int(time.time()), Cfg.IF_TEST_NET)
                insert_sql = "insert into jl_transaction_btc(type,member_id,coin_symbol,tx_hash,`from`,input,`to`,value_dec,fee,`data`,raw,created_at,block,tx_status,rpc_response,updated_at,network) values %s" % insert_transaction_sql
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", insert_sql)
                async with sem_db:
                    await super(Usdt, self).dbRun(self.pool, insert_sql)
                return
            tx_data = self.parsingTxLimitlessUSDT(iTrade)
            tx_from = tx_data["tx_from"]
            tx_to = tx_data["tx_to"]
            tx_value = tx_data["tx_to_value"]
            tx_fee = tx_data["fee"]
            if tx_type == 2:
                balance_dict = {"type": 1, "member_id": iResult[1], "coin_symbol": "USDT", "addr": tx_to, "change": tx_value, "fee": 0.0, "detial": iTrade["txid"], "detial_type": "chain", "network": Cfg.IF_TEST_NET}
            if tx_type == 3:
                change = "%.10f" % float(0.0 - float(tx_data["tx_to_value"]))
                fee = "%.10f" % float(0.0 - float(tx_data["fee"]))
                balance_dict = {"type": 10, "member_id": iResult[1], "coin_symbol": "USDT", "addr": tx_from, "change": change, "fee": fee, "detial": iTrade["txid"], "detial_type": "chain", "network": Cfg.IF_TEST_NET}
                # 申请单状状态【1：待审核、2：审核通过、3：未通过、4：提现失败、5：链上待确认、6：操作处理中】
                async with sem_db:
                    applysWithdraw = await super(Usdt, self).dbRun(self.pool, "select id,member_id,coin_symbol,addr,value_dec,current,withdraw_fee,pay_from,tx_hash from jl_withdraw_apply where status = 5 ")
                    for iApply in applysWithdraw:
                        if iApply[8] == iTrade["txid"]:
                            await super(Usdt, self).dbRun(self.pool, "update jl_withdraw_apply set status = {} where tx_hash = '{}'".format(2, iTrade["txid"]))
                            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "success withdraw 5->2, write into jl_withdraw_apply")
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"success {tx_type},balance_dict: {balance_dict}")
            await super(Usdt, self).updateBalance(self.pool, balance_dict)
            insert_transaction_sql = "(%d, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d, %d, 'success', '', %d, %d)" % (tx_type, iResult[1], "USDT", iTrade["txid"], tx_from, "", tx_to, tx_value, tx_fee, "", "", iTrade["blocktime"], iTrade["block"], int(time.time()), Cfg.IF_TEST_NET)
            insert_sql = "insert into jl_transaction_btc(type,member_id,coin_symbol,tx_hash,`from`,input,`to`,value_dec,fee,`data`,raw,created_at,block,tx_status,rpc_response,updated_at,network) values %s" % insert_transaction_sql
            await super(Usdt, self).backupAssetStandAlone(self.pool, tx_to, iResult[1], "USDT", tx_value)
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", insert_sql)
            async with sem_db:
                await super(Usdt, self).dbRun(self.pool, insert_sql)

    async def checkNewTxUSDT(self):
        """ 查询USDT地址历史交易"""
        async with sem_db:
            allresults = await super(Usdt, self).dbRun(self.pool, "select addr,uid,block,coin_symbol from jl_member_wallets where coin_symbol in ('USDT','_USDT_') and network = %d order by id asc" % Cfg.IF_TEST_NET)
        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "%s usdt addr" % len(allresults))
        async with sem_db:
            tx_hash_all = await super(Usdt, self).dbRun(self.pool, "select tx_hash from jl_transaction_btc where coin_symbol in ('USDT','_USDT_') and tx_hash is not null and network = %d" % Cfg.IF_TEST_NET)
        tx_hash_all = [x[0] for x in tx_hash_all]
        """查找数据库中eth最新block的number"""
        async with sem_db:
            blockNowUSDT = await super(Usdt, self).dbRun(self.pool, "select detial from jl_extension where type = 'NOW_USDT_BLOCK'")
        blockNowUSDT = int([k[0] for k in blockNowUSDT][0])
        listTrades = await self.usdtListTransactions(20, blockNowUSDT)
        if not listTrades:
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "No new trade")
            return
        for iTrade in listTrades:
            tx_type = 0
            if blockNowUSDT < iTrade["block"]:
                blockNowUSDT = iTrade["block"]
            if iTrade["txid"] in tx_hash_all:
                # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "%s already in" % iTrade["txid"])
                continue
            tasksAsync = []
            nbAsync = 1
            for iResult in allresults:
                tasksAsync.append(asyncio.ensure_future(self.checkNewTxUSDTUnit(iResult, iTrade)))
            for iTask in asyncio.as_completed(tasksAsync):
                await iTask
                nbAsync += 1
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", nbAsync)
        async with sem_db:
            await super(Usdt, self).dbRun(self.pool, "update jl_extension set detial = {} where type = 'NOW_USDT_BLOCK'".format(blockNowUSDT + 1))
