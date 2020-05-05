from _lib import *
from _lib.coin import Coin

sem_ETH = asyncio.Semaphore(Cfg.SEM_ETH)
sem_db = asyncio.Semaphore(Cfg.SEM_DB)
sem_infura = asyncio.Semaphore(Cfg.SEM_INFURA)


class Eth(Coin):
    lastRunTime = 0

    def __init__(self, log):
        self.__class__.lastRunTime = time.time()
        self.log = log
        self.tableName = "ETH"
        super(Eth, self).__init__(nameP="Eth")
        # self.sessionHttp = aiohttp.ClientSession()
        self.block_num_db_recent = 0
        self.block_num_chain_recent = 0
        self.ifCheck = 1
        self._pconn, self._cconn = Pipe()
        self._exception = None

    # def __exit__(self):
    #     self.sessionHttp.close()

    async def main(self, loop):
        try:
            pass
            startTime = time.time()

            self.pool = await aiomysql.create_pool(host=Cfg.DB_HOST_ADDR, port=Cfg.DB_PORT, user=Cfg.DB_USR, password=Cfg.DB_PWD, db=Cfg.DB_TABLE_NAME, loop=loop, charset="utf8", autocommit=True)

            # self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "ETHasda")

            tasks = []
            tasks.append(asyncio.ensure_future(self.checkNewBlock()))
            tasks.append(asyncio.ensure_future(self.checkPendingERC20()))
            for iTask in asyncio.as_completed(tasks):
                await iTask

            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"used Time: {time.time()-startTime}")
        except ApiError as e:
            self._cconn.send(e)
        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",str(os.getpid()))
        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",str(os.getppid()))

        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",Cfg.ETH_HOST)

        # cmdSql = "select type,detial from jl_extension where type in ('RAM_chain_block','NOW_ETH_BLOCK')"
        # result = await super(Eth, self).dbRun(self.pool, cmdSql)
        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",result)

        # result = await super(Eth, self).getCoins(self.pool)
        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",result)

        # resu=await super(Eth,self).getHashs(self.pool)
        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",resu[:10])

        # 没通 1.热钱包 2.viabtc
        # priceETHInUSD = await super(Eth, self).rpcViaBTC("market.last", ["ETHUSDT"])
        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",priceETHInUSD)

        # result = await super(Eth, self).updateCoinsPrices(self.pool)
        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",result)

        # await super(Eth, self).emailSend("1002142","10",'ETH',2)
        # await super(Eth, self).assetControlAllAddr(self.pool)

        # await self.checkPendingERC20()
        # await self.checkNewBlock()

        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",self.block_num_db_recent,self.block_num_chain_recent)
        # await self.getBlockNum()
        # await self.sessionHttp.close()

    def run(self):
        loop = asyncio.get_event_loop()
        # asyncio.ensure_future(self.main(loop))
        # print(os.getgid())
        loop.run_until_complete(self.main(loop))
        # loop.close()

    @property
    def exception(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        return self._exception

    async def getBlockNum(self):
        """查找数据库中eth最新block的number"""
        cmdSql = "select type,detial from jl_extension where type in ('RAM_chain_block')"
        async with sem_db:
            result = await super(Eth, self).dbRun(self.pool, cmdSql)
        block_num = {k[0]: k[1] for k in result}
        self.block_num_db_recent = int(block_num["RAM_chain_block"])
        async with sem_infura:
            self.block_num_chain_recent = await super(Eth, self).rpcWallet("eth_blockNumber", [], "ETH")
        if self.block_num_chain_recent is None:
            self.block_num_chain_recent = 0
            self.ifCheck = 0
            return self.ifCheck
        self.block_num_chain_recent = int(self.block_num_chain_recent, 16)
        if self.block_num_db_recent >= self.block_num_chain_recent:
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "self.block_num_db_recent >= self.block_num_chain_recent")
            self.ifCheck = 0
        if self.block_num_db_recent <= self.block_num_chain_recent:
            # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"{self.block_num_db_recent}<= {self.block_num_chain_recent}")
            self.ifCheck = 1
        # 只有在数据库记录少于链上的记录才继续
        return self.ifCheck

    def wei2ether(self, valueToCvrt):
        if self.isDigit(valueToCvrt):
            changeHex = hex(int(valueToCvrt * 10 ** 18))
            change = valueToCvrt
        else:
            change = "%.14f" % float(float(int(valueToCvrt, 16)) / 10 ** 18)
            changeHex = valueToCvrt
        return {"change": change, "changeHex": changeHex}

    async def migrateToNewWallet(self):
        pass

    async def getValidBlockTxUnit(self, iBlock, tx_hash_all, token_addrs, tokensAll):
        listReturn = []
        # print(f"check No.{self.block_num_chain_recent - iBlock}: {iBlock} of {self.block_num_chain_recent}")
        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"=== block to check: {self.block_num_chain_recent - iBlock}")
        async with sem_infura:
            infosBlock = await super(Eth, self).rpcWallet("eth_getBlockByNumber", [hex(iBlock), True], "ETH")
        if infosBlock is None:
            # self.log.warning("{} is None, block not found".format(iBlock))
            return
        for iTxBlock in infosBlock["transactions"]:
            # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}","==check tx_hash {}===={}=============".format(iTxBlock["hash"], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            if iTxBlock["hash"] in tx_hash_all:
                # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}","----: %s already in db" % iTxBlock["hash"])
                continue
            if iTxBlock["value"] != "0x0":  # QUANTITY - value transferred in Wei.
                changeResult = self.wei2ether(iTxBlock["value"])
                if float(changeResult["change"]) <= Cfg.ETH_ASSET_USR_SKIP:
                    continue
                # ETH充钱
                if not iTxBlock["to"]:
                    # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}",f"----------------------tx_to is none: {iTxBlock}")
                    continue
                listReturn.append(("ETH", iTxBlock))
            else:
                # ERC20交易
                if iTxBlock["input"][0:34] != Cfg.ETH_RAM_TRANS:
                    # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}","unknow function selector: %s" % iTxBlock["input"][0:34])
                    continue
                ram_token_addr = iTxBlock["to"]
                # token_addrs=['0x7fdca98f0d8d7a7429b03f7d81c63e45472d28fc'] #testTemp
                if ram_token_addr not in token_addrs:
                    # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}","ram_token_addr not active")
                    continue
                tx_input = iTxBlock["input"]
                if len(tx_input) > 138:
                    continue
                if tx_input[74:138].lstrip("0") == "":
                    # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}","change is 0000")
                    continue
                tx_to = "0x" + tx_input[34:74]  # user addr in sepoch
                if int(tx_input[11:34]) != 0:
                    continue
                get_token = [k for k in tokensAll if k[3].lower() == ram_token_addr.lower()]
                if get_token == []:
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "No tocken addr in DB !")
                    continue
                coin_symbol = get_token[0][0]
                # 查tx_to的用户id
                # tokensAll=(('ETH', 'ETH', 0, '', 4),('ZRX', 'ZRX', 0, '0x7fdca98f0d8d7a7429b03f7d81c63e45472d28fc', 18),) #testTemp
                listReturn.append((coin_symbol, iTxBlock))
        return listReturn

    def taskListGet(self, start, end, tx_hash_all, token_addrs, tokensAll):
        tasks = []
        for iBlock in range(start, end - (end % Cfg.SEM_ETH)):
            tasks.append(asyncio.ensure_future(self.getValidBlockTxUnit(iBlock, tx_hash_all, token_addrs, tokensAll)))
            if (iBlock - start) % Cfg.SEM_ETH == 0:
                yield tasks
                tasks = []
        else:
            tasks = []
            for iBlock in range(end - (end % Cfg.SEM_ETH), end + 1):
                tasks.append(asyncio.ensure_future(self.getValidBlockTxUnit(iBlock, tx_hash_all, token_addrs, tokensAll)))
            yield tasks

    async def getValidBlockTx(self, coinsInfos):
        txBlocksValide = []
        tokensAll = coinsInfos["coinsInfo"]
        token_addrs = coinsInfos["tokenAddrs"]
        tx_hash_all = await self.getHashs(self.pool)
        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "{} of {} , {}".format(self.block_num_db_recent + 1, self.block_num_chain_recent, self.block_num_chain_recent - self.block_num_db_recent))
        if self.block_num_db_recent + 1 > self.block_num_chain_recent:
            return
        # taskGenerator = self.taskListGet(9863625, 9863650, tx_hash_all, token_addrs, tokensAll)
        taskGenerator = self.taskListGet(self.block_num_db_recent + 1, self.block_num_chain_recent, tx_hash_all, token_addrs, tokensAll)
        for iTaskGenerator in taskGenerator:
            for iTask in asyncio.as_completed(iTaskGenerator):
                result = await iTask
                if result:
                    txBlocksValide.extend(result)
        return txBlocksValide

    async def checkNewBlock(self):
        """
        针对所有erc20币种，
        获取数据库jl_transaction中交易的hash值，
        检查eth_getBlockByNumber，
        如果该block_num的transactions hash不在数据库jl_transaction中的hash中，
        且该block_num的transactions value== "0x0"，
        且to目标地址在数据库的user_addrs中，
        如果txBlock["hash"] == None，那么交易pending,
        否则通过eth_getTransactionReceipt查询交易状态，
        null when no receipt was found，
        status: QUANTITY either 1 (success) or 0 (failure)
        如果状态成功并且存在目标地址，则把转账的value: QUANTITY - value transferred in Wei转换成ETH,
        最后更新到jl_balance_log、jl_balance以及同步撮合引擎的balance
        """
        await self.getBlockNum()
        allAddr = await self.getAddrs(self.pool)
        coinsInfos = await super(Eth, self).getCoins(self.pool)
        tokensAll = coinsInfos["coinsInfo"]
        txBlocksValide = await self.getValidBlockTx(coinsInfos)
        for coin_symbol, iTxBlock in txBlocksValide:
            if coin_symbol == "ETH":
                # ETH
                tx_to = iTxBlock["to"]
                # 查tx_to的用户id
                get_user = [k for k in allAddr["allresult"] if k[0].lower() == tx_to.lower()]
                if len(get_user) == 0:
                    continue
                get_user_id = get_user[0][1]
                # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}","tx_to addr found for user : ", get_user_id)
                if iTxBlock["hash"] == None:
                    tx_status = "pending"
                    # 交易未打包，写入pending
                    transaction_dict = {"type": 2, "member_id": get_user_id, "coin_symbol": "ETH", "tx_hash": iTxBlock["hash"], "from": iTxBlock["from"], "to": iTxBlock["to"], "value_hex": 0, "value_dec": 0, "gas_dec": int(txsReceipts["gasUsed"], 16), "gas_hex": txsReceipts["gasUsed"], "gas_price_dec": int(iTxBlock["gasPrice"], 16), "gas_price_hex": iTxBlock["gasPrice"], "nonce_dec": int(iTxBlock["nonce"], 16), "nonce_hex": iTxBlock["nonce"], "data": iTxBlock["input"], "tx_status": tx_status, "block": iTxBlock["blockNumber"]}
                    await super(Eth, self).updateTransaction(self.pool, transaction_dict)
                    continue
                # eth_getTransactionReceipt 查询交易成功或失败
                async with sem_infura:
                    txsReceipts = await super(Eth, self).rpcWallet("eth_getTransactionReceipt", [iTxBlock["hash"]], "ETH")
                if txsReceipts is None:  # 当前交易打包未完成，pending
                    tx_status = "pending"
                    transaction_dict = {"type": 2, "member_id": get_user_id, "coin_symbol": "ETH", "tx_hash": iTxBlock["hash"], "from": iTxBlock["from"], "to": iTxBlock["to"], "value_hex": 0, "value_dec": 0, "gas_dec": int(txsReceipts["gasUsed"], 16), "gas_hex": txsReceipts["gasUsed"], "gas_price_dec": int(iTxBlock["gasPrice"], 16), "gas_price_hex": iTxBlock["gasPrice"], "nonce_dec": int(iTxBlock["nonce"], 16), "nonce_hex": iTxBlock["nonce"], "data": iTxBlock["input"], "tx_status": tx_status, "block": iTxBlock["blockNumber"]}
                    await super(Eth, self).updateTransaction(self.pool, transaction_dict)
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "ETH txsReceipts is None, pending {}:{}".format(get_user_id, iTxBlock["hash"]))
                    continue
                changeResult = self.wei2ether(iTxBlock["value"])
                change = changeResult["change"]
                change_hex = changeResult["changeHex"]
                confirmationCurrent = self.block_num_chain_recent - int(txsReceipts["blockNumber"], 16)
                if confirmationCurrent < Cfg.CONFIRMATION_SUCCESS:
                    tx_status = "pending"
                    transaction_dict = {"type": 2, "member_id": get_user_id, "coin_symbol": "ETH", "tx_hash": iTxBlock["hash"], "from": iTxBlock["from"], "to": iTxBlock["to"], "value_hex": change_hex, "value_dec": change, "gas_dec": int(txsReceipts["gasUsed"], 16), "gas_hex": txsReceipts["gasUsed"], "gas_price_dec": int(iTxBlock["gasPrice"], 16), "gas_price_hex": iTxBlock["gasPrice"], "nonce_dec": int(iTxBlock["nonce"], 16), "nonce_hex": iTxBlock["nonce"], "data": iTxBlock["input"], "tx_status": tx_status, "block": iTxBlock["blockNumber"]}
                    await super(Eth, self).updateTransaction(self.pool, transaction_dict)
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "ETH Confirmations <6 , pending {}:{}".format(get_user_id, iTxBlock["hash"]))
                    continue
                if txsReceipts["status"] == "0x0":
                    continue
                elif txsReceipts["status"] == "0x1":
                    if float(change) - 0.0 == 0:
                        continue
                    tx_status = "success"
                    # 交易成功，写入success，add balance
                    transaction_dict = {"type": 2, "member_id": get_user_id, "coin_symbol": "ETH", "tx_hash": iTxBlock["hash"], "from": iTxBlock["from"], "to": iTxBlock["to"], "value_hex": change_hex, "value_dec": change, "gas_dec": int(txsReceipts["gasUsed"], 16), "gas_hex": txsReceipts["gasUsed"], "gas_price_dec": int(iTxBlock["gasPrice"], 16), "gas_price_hex": iTxBlock["gasPrice"], "nonce_dec": int(iTxBlock["nonce"], 16), "nonce_hex": iTxBlock["nonce"], "data": iTxBlock["input"], "tx_status": tx_status, "block": iTxBlock["blockNumber"]}
                    await super(Eth, self).updateTransaction(self.pool, transaction_dict)
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", transaction_dict)
                    balance_dict = {"type": 1, "member_id": get_user_id, "coin_symbol": "ETH", "addr": iTxBlock["to"], "change": change, "fee": 0.0, "detial": iTxBlock["hash"], "detial_type": "chain", "network": Cfg.IF_TEST_NET}
                    await super(Eth, self).updateBalance(self.pool, balance_dict)
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"success deposit: {balance_dict}")
                    if float(change) > Cfg.ETH_MAX_USR_ASSET:
                        usrBalanceResult = await self.rpcAsset([get_user_id, change], "ETH")
                        status, dataLog = usrBalanceResult
                        if status:
                            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"Backup usr {get_user_id} ETH assets {change} - result: {dataLog}")
                        else:
                            self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"Backup usr {get_user_id} ETH assets {change} - result: {dataLog}")
            else:
                get_token = [k for k in tokensAll if k[3].lower() == iTxBlock["to"].lower()]
                if get_token == []:
                    # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "No token addr in DB !")
                    continue
                tx_to = "0x" + iTxBlock["input"][34:74]
                get_user = [k for k in allAddr["allresult"] if k[0].lower() == tx_to and k[2] == "_" + coin_symbol + "_"]
                if len(get_user) == 0:
                    continue
                ram_token_decimals = get_token[0][4]
                get_user_id = get_user[0][1]
                if iTxBlock["hash"] == None:
                    tx_status = "pending"
                    # 交易未打包，写入pending
                    transaction_dict = {"type": 2, "member_id": get_user_id, "coin_symbol": coin_symbol, "tx_hash": iTxBlock["hash"], "from": iTxBlock["from"], "to": tx_to, "value_hex": change_hex, "value_dec": change, "gas_dec": int(txsReceipts["gasUsed"], 16), "gas_hex": txsReceipts["gasUsed"], "gas_price_dec": int(iTxBlock["gasPrice"], 16), "gas_price_hex": iTxBlock["gasPrice"], "nonce_dec": int(iTxBlock["nonce"], 16), "nonce_hex": iTxBlock["nonce"], "data": iTxBlock["input"], "tx_status": tx_status, "block": iTxBlock["blockNumber"]}
                    await super(Eth, self).updateTransaction(self.pool, transaction_dict)
                    continue
                # eth_getTransactionReceipt 查询交易成功或失败
                async with sem_infura:
                    txsReceipts = await super(Eth, self).rpcWallet("eth_getTransactionReceipt", [iTxBlock["hash"]], "ETH")
                if txsReceipts is None:  # 当前交易打包未完成，pending
                    tx_status = "pending"
                    # 交易未打包，写入pending
                    transaction_dict = {"type": 2, "member_id": get_user_id, "coin_symbol": coin_symbol, "tx_hash": iTxBlock["hash"], "from": iTxBlock["from"], "to": tx_to, "value_hex": change_hex, "value_dec": change, "gas_dec": int(txsReceipts["gasUsed"], 16), "gas_hex": txsReceipts["gasUsed"], "gas_price_dec": int(iTxBlock["gasPrice"], 16), "gas_price_hex": iTxBlock["gasPrice"], "nonce_dec": int(iTxBlock["nonce"], 16), "nonce_hex": iTxBlock["nonce"], "data": iTxBlock["input"], "tx_status": tx_status, "block": iTxBlock["blockNumber"]}
                    await super(Eth, self).updateTransaction(self.pool, transaction_dict)
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"f{tx_status} deposit: {transaction_dict}")
                    continue
                if txsReceipts["status"] == "0x0":
                    # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "top up tx fail")
                    continue
                change = "%.12f" % float(float(int(tx_input[74:138].lstrip("0"), 16)) / 10 ** ram_token_decimals)
                if float(change) - 0.0 == 0:
                    continue
                change_hex = tx_input[74:138].lstrip("0")
                confirmationCurrent = self.block_num_chain_recent - int(txsReceipts["blockNumber"], 16)
                if confirmationCurrent < Cfg.CONFIRMATION_SUCCESS:
                    tx_status = "pending"
                    transaction_dict = {"type": 2, "member_id": get_user_id, "coin_symbol": coin_symbol, "tx_hash": iTxBlock["hash"], "from": iTxBlock["from"], "to": tx_to, "value_hex": change_hex, "value_dec": change, "gas_dec": int(txsReceipts["gasUsed"], 16), "gas_hex": txsReceipts["gasUsed"], "gas_price_dec": int(iTxBlock["gasPrice"], 16), "gas_price_hex": iTxBlock["gasPrice"], "nonce_dec": int(iTxBlock["nonce"], 16), "nonce_hex": iTxBlock["nonce"], "data": iTxBlock["input"], "tx_status": tx_status, "block": iTxBlock["blockNumber"]}
                    await super(Eth, self).updateTransaction(self.pool, transaction_dict)
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "{} Confirmations <6 , pending {}:{}".format(coin_symbol, get_user_id, iTxBlock["hash"]))
                    continue
                if txsReceipts["status"] == "0x1":
                    tx_status = "success"
                    # 交易成功，写入success，add balance
                    transaction_dict = {"type": 2, "member_id": get_user_id, "coin_symbol": coin_symbol, "tx_hash": iTxBlock["hash"], "from": iTxBlock["from"], "to": tx_to, "value_hex": change_hex, "value_dec": change, "gas_dec": int(txsReceipts["gasUsed"], 16), "gas_hex": txsReceipts["gasUsed"], "gas_price_dec": int(iTxBlock["gasPrice"], 16), "gas_price_hex": iTxBlock["gasPrice"], "nonce_dec": int(iTxBlock["nonce"], 16), "nonce_hex": iTxBlock["nonce"], "data": iTxBlock["input"], "tx_status": tx_status, "block": iTxBlock["blockNumber"]}
                    await super(Eth, self).updateTransaction(self.pool, transaction_dict)  # testTemp
                    balance_dict = {"type": 1, "member_id": get_user_id, "coin_symbol": coin_symbol, "addr": tx_to, "change": change, "fee": 0.0, "detial": iTxBlock["hash"], "detial_type": "chain", "network": Cfg.IF_TEST_NET}
                    await super(Eth, self).updateBalance(self.pool, balance_dict)
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"success deposit: {balance_dict}")
                    await super(Eth, self).backupAssetStandAlone(self.pool, tx_to, get_user_id, coin_symbol, change)
        # 更新数据库中最后同步过的eth block number
        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "RAM_chain_block (block_num_chain_recent) now = {}".format(self.block_num_chain_recent - 1))
        async with sem_db:
            await self.dbRun(self.pool, f"update jl_extension set detial ={self.block_num_chain_recent - 1} where type = 'RAM_chain_block'")

    async def checkPendingERC20(self):
        """
        检查eth的所有pending交易
        """
        async with sem_db:
            allresult = await super(Eth, self).dbRun(self.pool, f"select id,tx_hash,tx_status,type,member_id,coin_symbol,`from`,`to`,value_dec FROM jinglanex.jl_transaction where tx_status = 'pending' and network = {Cfg.IF_TEST_NET} order by id asc")
        if len(allresult) == 0:
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "No Pending")
            return
        tx_hashs = [k[1] for k in allresult]
        tx_hashss = ",".join("'%s'" % s for s in tx_hashs)
        async with sem_db:
            applys = await super(Eth, self).dbRun(self.pool, "select id,member_id,coin_symbol,addr,value_dec,current,withdraw_fee,pay_from,tx_hash from jl_withdraw_apply where status = 5 and tx_hash in (%s)" % (tx_hashss))
        # coins = objChain.getCoins(cur, cfgAll["tokenType"]["ETH"])["coinsInfo"]
        # coins=(('ETH', 'ETH', 0, '', 4),('ZRX', 'ZRX', 0, '0x7fdca98f0d8d7a7429b03f7d81c63e45472d28fc', 18),) #testTemp
        # coin_symbols = [k[0] for k in coins]
        # coin_symbolss = ",".join("'%s'" % s for s in coin_symbols)
        # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}","there r {} {} TX".format(count, coin_symbolss))

        # 申请单状状态【1：待审核、2：审核通过、3：未通过、4：提现失败、5：链上待确认、6：操作处理中】
        for iResult in allresult:
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", iResult)
            if iResult is None:
                # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "no iResult !!!")
                continue
            # print iResult[1]
            async with sem_infura:
                rst = await super(Eth, self).rpcWallet("eth_getTransactionReceipt", [iResult[1]], "ETH")
                # tx = await super(Eth, self).rpcWallet("eth_getTransactionByHash", [iResult[1]], "ETH")
            if rst is None:
                continue
            if rst["blockNumber"] is None:  # pending 交易待打包
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"still pending: {rst}")
                continue
            else:
                # eth_getTransactionReceipt 查询交易成功或失败
                # async with sem_infura:
                #     rst = await super(Eth, self).rpcWallet("eth_getTransactionReceipt", [iResult[1]], "ETH")
                if rst["status"] is None:
                    continue
                if rst["status"] == "0x1":
                    tx_status = "success"
                else:
                    tx_status = "fail"
                block = int(rst["blockNumber"], 16)
                updated_at = int(time.time())
            if tx_status == "success":
                if iResult[3] == 2:  # 1.平台币提现 2:充值 3:提现
                    balance_dict = {"type": 1, "member_id": iResult[4], "coin_symbol": iResult[5], "addr": iResult[7], "change": iResult[8], "fee": 0.0, "detial": iResult[1], "detial_type": "chain", "network": Cfg.IF_TEST_NET}
                    await super(Eth, self).updateBalance(self.pool, balance_dict)
                    update_sql = "update jl_transaction set tx_status = 'success', updated_at = %d where tx_hash = '%s' and coin_symbol = '%s'" % (updated_at, iResult[1], iResult[5])
                    async with sem_db:
                        await super(Eth, self).dbRun(self.pool, update_sql)
                        await super(Eth, self).backupAssetStandAlone(self.pool, iResult[7], iResult[4], iResult[5], iResult[8])
                        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "deposit: pending->success - {}".format(balance_dict))
                # elif iResult[3] == 3 :  # 1.平台币提现 2:充值 3:提现
                elif iResult[3] == 3:  # 1:钱包转账交易 2:存入银行 3:取出银行 4:场外交易
                    # 查询此时余额
                    apply_ones = [k for k in applys if k[-1] == iResult[1]]
                    if len(apply_ones) > 0:
                        apply_one = apply_ones[0]
                        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "the withdraw apply::{}".format(apply_one))
                        # 查询用户平台地址
                        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "查询用户交易所钱包地址")
                        async with sem_db:
                            user_bank_addr = await super(Eth, self).dbRun(self.pool, "select addr from jl_member_wallets where uid = %d and coin_symbol = '_%s_' and status = 1 and network = %d" % (iResult[4], iResult[5], Cfg.IF_TEST_NET))
                        user_bank_addr = user_bank_addr[0]
                        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", user_bank_addr)
                        change = float(0.0 - float(apply_one[4]))
                        balance_dict = {"type": 10, "member_id": iResult[4], "coin_symbol": iResult[5], "addr": user_bank_addr, "change": change, "fee": 0.0, "detial": iResult[1], "detial_type": "withdraw", "network": Cfg.IF_TEST_NET}
                        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", balance_dict)
                        await super(Eth, self).updateBalance(self.pool, balance_dict)
                        fee = float(0.0 - float(apply_one[6]))
                        # fee = float(0.0 - float(apply_one[5]) - float(apply_one[6]))
                        balance_dict = {"type": 10, "member_id": iResult[4], "coin_symbol": iResult[5], "addr": user_bank_addr, "change": fee, "fee": 0.0, "detial": iResult[1] + "-fee", "detial_type": "withdraw_fee", "network": Cfg.IF_TEST_NET}
                        async with sem_db:
                            await super(Eth, self).updateBalance(self.pool, balance_dict)
                            await super(Eth, self).dbRun(self.pool, "update jl_withdraw_apply set status = 2 where status = 5 and tx_hash = '%s'" % (iResult[1]))
                            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "status 5 to be checked on chain -> 2 confirmed: {}-{}-{}-change:{}-fee:{}".format(iResult[4], iResult[5], iResult[1], change, fee))
