from _lib import *
from _lib.config import Cfg

sem_asset = asyncio.Semaphore(Cfg.SEM_ASSET)


class Coin(Process):
    lastRunTime = 0

    def __init__(self, nameP="ASSET", log=None):
        if log:
            self.tableName = "ASSET"
            self.log = log
        self.__class__.lastRunTime = time.time()
        super(Coin, self).__init__(name=nameP)
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
            # self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "asdasd")

            tasks = []
            tasks.append(asyncio.ensure_future(self.assetControlAllAddr(self.pool)))
            for iTask in asyncio.as_completed(tasks):
                await iTask

            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"used Time: {time.time()-startTime}")
        except ApiError as e:
            self._cconn.send(e)

    @property
    def exception(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        return self._exception

    async def dbRun(self, pool, cmdSql):
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(cmdSql)
                result = await cur.fetchall()
        return result

    async def getHashs(self, pool):
        cmdSql = "select tx_hash from jl_transaction where tx_hash is not null"
        tx_hash_all = await self.dbRun(pool, cmdSql)
        tx_hash_all = [txHash[0] for txHash in tx_hash_all]
        return tx_hash_all

    async def updateTransaction(self, pool, tx_dict):
        """update type,member_id,coin_symbol,tx_hash,`from`,`to`,value_hex,value_dec,gas_hex,gas_dec,gas_price_hex,gas_price_dec,nonce_hex,nonce_dec,`data`,created_at,tx_status,block,updated_at,network into jl_transaction"""
        insert_sql = "insert into jl_transaction (type,member_id,coin_symbol,tx_hash,`from`,`to`,value_hex,value_dec,gas_hex,gas_dec,gas_price_hex,gas_price_dec,nonce_hex,nonce_dec,`data`,created_at,tx_status,block,updated_at,network) values (%d, %d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d, '%s',%d, %d, %d)" % (int(tx_dict["type"]), int(tx_dict["member_id"]), tx_dict["coin_symbol"], tx_dict["tx_hash"], tx_dict["from"], tx_dict["to"], tx_dict["value_hex"], str(tx_dict["value_dec"]), tx_dict["gas_hex"], str(tx_dict["gas_dec"]), tx_dict["gas_price_hex"], str(tx_dict["gas_price_dec"]), tx_dict["nonce_hex"], str(tx_dict["nonce_dec"]), tx_dict["data"], int(time.time()), tx_dict["tx_status"], int(tx_dict["block"], 16), int(time.time()), Cfg.IF_TEST_NET)
        # self.logger.debug("jl_transaction: ", insert_sql)
        await self.dbRun(pool, insert_sql)

    async def getCoins(self, pool, coinList=[]):
        """查币种 非BTC USDT的币种 FIX: 排除EOS and 排除 not enable"""
        if coinList == []:
            cmdSql = "select symbol,unit,ram_status,ram_token_addr,ram_token_decimals from jl_coins where enable = 1  order by listorder desc"
        else:
            cmdSql = "select symbol,unit,ram_status,ram_token_addr,ram_token_decimals from jl_coins where symbol in ({}) and enable = 1  order by listorder desc".format("'" + "','".join(coinList) + "'")
        coinsInfo = await self.dbRun(pool, cmdSql)
        # 获取所有非BTC USDT币种的地址 ram_token_addr
        tokenAddrs = [coin[3].lower() for coin in coinsInfo]
        # self.logger.debug(tokenAddrs)
        return {"tokenAddrs": tokenAddrs, "coinsInfo": coinsInfo}

    async def getAddrs(self, pool, coinList=[]):
        """获取jl_member_wallets所有币种或者指定币种的用户钱包地址"""
        if coinList == []:
            cmdSql = f"select addr,uid,coin_symbol from jl_member_wallets where network={Cfg.IF_TEST_NET} order by id asc"
        else:
            cmdSql = "select addr,uid,coin_symbol from jl_member_wallets where coin_symbol in ({}) and network={} order by id asc".format("'" + "','".join(coinList) + "'", int(Cfg.IF_TEST_NET))
        allresult = await self.dbRun(pool, cmdSql)
        user_addrs = [k[0].lower() for k in allresult]
        return {"user_addrs": user_addrs, "allresult": allresult}

    async def getUsd2Cny(self):
        usdToCny = 7.0
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(Cfg.API_USD2CNY) as P_get:
                    if P_get.status in [200, 201]:
                        dataGet = json.loads(await P_get.text(encoding="utf8"))
                        usdToCny = dataGet["quotes"]["USDCNY"]
                    else:
                        errMsg = f"{P_get.host} - {P_get.status} - {P_get.reason}"
                        self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", errMsg)
                        return None
            except Exception as e:
                self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", repr(e))
                usdToCny = 7.0
        return usdToCny

    async def emailSend(self, uid, amount, coin, mode=1):
        """ mode 1 : user, mode else: manager """
        headers = {"User-Agent": "Mozilla/5.0"}
        payload = {"UID": uid, "amount": amount, "coin": coin}
        # self.logger.info("email sent :{}".format(payload))
        apiUrl = "/api/register/depositmail" if mode == 1 else "/api/register/depositmail2"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(Cfg.WEB_HOST + apiUrl, headers=headers, data=payload) as P_post:
                    if P_post.status in [200, 201]:
                        self.log.success(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"email sent {uid} mode {mode} ok")
                    else:
                        errMsg = f"{P_post.host} - {P_post.status} - {P_post.reason}"
                        self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", errMsg)
                        return None
            except Exception as e:
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", repr(e))
                return "timeout"

    async def emailSendPy(self, uid, amount, coin, dstAddr, info=""):
        try:
            message = EmailMessage()
            message["From"] = Cfg.SMTP_USERNAME
            message["To"] = dstAddr
            message["Subject"] = f"Seposit: {uid} {amount} {coin}"
            timestamp = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S.%f")
            message.set_content(f"用户充值提醒:\n\nuid: {uid} \namount: {amount} \ncoin: {coin} \n备注(如果有):{info} \n\n\n Time: {timestamp}")
            smtp = aiosmtplib.SMTP(hostname=Cfg.SMTP_HOST, port=Cfg.SMTP_PORT, use_tls=True)
            await smtp.connect()
            # await smtp.starttls()
            await smtp.login(Cfg.SMTP_USERNAME, Cfg.SMTP_PASSWORD)
            await smtp.send_message(message)
            await smtp.quit()
            return "ok", f"sent: {dstAddr}"
        except Exception as e:
            return f"err", e

    async def updateBalance(self, pool, balance_dict):
        """ 
        update into jl_balance_log
        """
        # self.logger.debug("=== update balance dict::", balance_dict)
        # 先核对该地址是否为该用户的相应币种的钱包地址
        cmdSql = "select * from jl_member_wallets where uid = %d and coin_symbol = '%s' and addr = '%s' and network = %d" % (balance_dict["member_id"], "_" + balance_dict["coin_symbol"] + "_", balance_dict["addr"], balance_dict["network"])
        wallet = await self.dbRun(pool, cmdSql)
        if len(wallet) == 0:
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "no usr {} {} wallet addr {} in jl_member_wallets".format(balance_dict["member_id"], "_" + balance_dict["coin_symbol"] + "_", balance_dict["addr"]))
            return
        # self.logger.debug("user wallet::", wallet)
        # 核对该tx_hash是否已存在
        tx_count = await self.dbRun(pool, "select balance from jl_balance_log where detial = '{}' and coin_symbol = '{}'".format(balance_dict["detial"], balance_dict["coin_symbol"]))
        if len(tx_count) > 0:
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "tx_hash already exist in jl_balance_log where detial = '{}' and coin_symbol = '{}'".format(balance_dict["detial"], balance_dict["coin_symbol"]))
            return
        # 查该用户最后余额数值
        last_balance_count = await self.dbRun(pool, "select balance from jl_balance_log where member_id = %d and coin_symbol = '%s' and addr = '%s' and network = %d order by id desc limit 1" % (balance_dict["member_id"], balance_dict["coin_symbol"], balance_dict["addr"], balance_dict["network"]))
        if len(last_balance_count) == 0:
            last_balance = 0.0
        else:
            last_balance = last_balance_count[0][0]
            # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"last_balance: {last_balance}")
        balanceChange = balance_dict["change"]
        try:
            balance = round(float(float(balanceChange) + float(last_balance) - float(balance_dict["fee"])), 14)
        except Exception as e:
            self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"{last_balance} {balanceChange}")
        await self.emailSend(str(balance_dict["member_id"]), balance_dict["change"], balance_dict["coin_symbol"], 1)
        tasks = [asyncio.create_task(self.emailSendPy(str(balance_dict["member_id"]), balance_dict["change"], balance_dict["coin_symbol"], iAddr)) for iAddr in Cfg.SMTP_DST_ADDR_DEPOSIT]
        for iTask in asyncio.as_completed(tasks):
            status, resultSend = await iTask
        # await self.emailSend("1002140", balance_dict["change"], balance_dict["coin_symbol"], 2)
        # await self.emailSend("1002131", balance_dict["change"], balance_dict["coin_symbol"], 2)
        # await self.emailSend("1002142", balance_dict["change"], balance_dict["coin_symbol"], 2)
        insert_sql = "insert into jl_balance_log (`type`,member_id,coin_symbol,addr,`change`,balance,fee,detial,detial_type,ctime,network) values (%d, %d,'%s','%s',%.12f,%.14f,%.12f,'%s','%s',%d,%d)" % (balance_dict["type"], balance_dict["member_id"], balance_dict["coin_symbol"], balance_dict["addr"], float(balance_dict["change"]), float(balance), float(balance_dict["fee"]), balance_dict["detial"], balance_dict["detial_type"], int(time.time()), balance_dict["network"])
        self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "=== insert balance log sql:: {}".format(insert_sql))
        await self.dbRun(pool, insert_sql)

    async def rpcViaBTC(self, method, params):
        # headers = {"Content-Type": "application/json", "Connection": "close"}
        post_data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        # encode_json = json.dumps(post_data)
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(Cfg.VIABTC_HOST, json=post_data) as P_post:
                    if P_post.status == 200:
                        rst = json.loads(await P_post.text(encoding="utf8"))
                        if "result" in rst:
                            return None if rst["result"] == "" else rst["result"]
                    else:
                        errMsg = f"{P_post.host} - {P_post.status} - {P_post.reason}"
                        self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", errMsg)
                        return None
            except Exception as e:
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", repr(e))
                return None

    async def updateCoinsPrices(self, pool):
        """ 更新各币种价格 """
        cmdSql = "select id,type,detial,unit from jl_extension where type = 'usd_to_cny' or type = 'usdt_to_USD' order by id asc"
        resultDBs = await self.dbRun(pool, cmdSql)
        if resultDBs[0][3]:
            timestampUpdate = float(resultDBs[0][3])
        else:
            timestampUpdate = 0
        usdToCny = float(resultDBs[0][2])
        if time.time() - float(timestampUpdate) > 60 * 60 * 8.0:
            usdToCny = await self.getUsd2Cny()
            update_sql = "UPDATE jl_extension set detial = {},unit={} WHERE type = 'usd_to_cny'".format(usdToCny, time.time())
            await self.dbRun(pool, update_sql)
        cmdSelect = "select stock,money from jl_exchange_coins where enable = 1 order by listorder desc"
        resultsMatchEngine = await self.dbRun(pool, cmdSelect)
        priceETHInUSD = await self.rpcViaBTC("market.last", ["ETHUSDT"])
        priceBTCInUSD = await self.rpcViaBTC("market.last", ["BTCUSDT"])
        if not priceETHInUSD:
            self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "priceETHInUSD is None, viabtc connection not ok")
            return
        if not priceBTCInUSD:
            self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", "priceBTCInUSD is None, viabtc connection not ok")
            return
        priceETHInUSD = float(priceETHInUSD)
        priceBTCInUSD = float(priceBTCInUSD)
        coinsUSDT = [exPair[0] for exPair in resultsMatchEngine if exPair[1] == "USDT"]
        for exPair in resultsMatchEngine:
            stockMoney = "{}{}".format(exPair[0], exPair[1])
            coinPrice = await self.rpcViaBTC("market.last", [stockMoney])
            if not coinPrice:
                continue
            coinPrice = float(coinPrice)
            if exPair[1] == "USDT":
                coinPriceInUSD = coinPrice
                coinPriceInCny = coinPrice * usdToCny
            elif exPair[1] == "ETH" and exPair[0] not in coinsUSDT:
                coinPriceInUSD = priceETHInUSD * coinPrice
                coinPriceInCny = coinPriceInUSD * usdToCny
            elif exPair[1] == "BTC" and exPair[0] not in coinsUSDT:
                coinPriceInUSD = priceBTCInUSD * coinPrice
                coinPriceInCny = coinPriceInUSD * usdToCny
            else:
                continue
            update_coin_price = "UPDATE jl_coins set usd = {},cny = {} WHERE symbol = '{}'".format(round(coinPriceInUSD, 2), round(coinPriceInCny, 2), exPair[0])
            # self.logger.info("{}: (USD){} (CNY){}".format(exPair[0], coinPriceInUSD, coinPriceInCny))
            await self.dbRun(pool, update_coin_price)

    def isDigit(self, valueInput):
        try:
            float(valueInput)
            return True
        except:
            return False

    async def rpcWallet(self, method, params, coin_symbol="ETH"):
        """根据coin_symbol用rpc命令与热钱包交互"""
        # headers = {"user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36", "Content-Type": "application/json", "Connection": "close"}
        headers = {"Content-Type": "application/json", "Connection": "close"}
        post_data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        # encode_json = json.dumps(post_data)
        async with aiohttp.ClientSession() as session:
            try:
                if coin_symbol == "BTC":
                    idAuth = aiohttp.BasicAuth(Cfg.BTC_USR, Cfg.BTC_PWD)
                    P_post = await session.post(Cfg.BTC_HOST, json=post_data, auth=idAuth)
                elif coin_symbol == "USDT":
                    idAuth = aiohttp.BasicAuth(Cfg.USDT_USR, Cfg.USDT_PWD)
                    P_post = await session.post(Cfg.USDT_HOST, json=post_data, auth=idAuth)
                else:
                    P_post = await session.post(Cfg.ETH_HOST_CHECK, headers=headers, json=post_data)
                    await asyncio.sleep(Cfg.SEM_INFURA_TIMEWAITING)
                if P_post.status in [200, 201]:
                    rst = json.loads(await P_post.text())
                    if "result" in rst:
                        return rst["result"]
                    else:
                        return None
                else:
                    errMsg = f"{P_post.host} - {P_post.status} - {P_post.reason} - {post_data}"
                    self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", errMsg)
                    if P_get.status == 429:
                        raise ApiError("ApiError")
                    return None
            except ApiError:
                raise
            except Exception as e:
                self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", repr(e))
                return None

    async def preTransEthSmallAmount(self, usrAddr, gasPriceETH, gasETH):
        paramPreTransfer = [addrFromWallet, self.wei2ether(Cfg.ETH_PRE_TRANSFER)["changeHex"], gasPriceETH, hex(int(gasETH))]
        usrBalanceResult = await self.rpcAsset(paramPreTransfer, "ETHPreTransfer")
        # logging.warn(f"Step0 - result:{usrBalanceResult} - coinbase ETH transfer to {uidUsr} - param:{paramPreTransfer}")
        return usrBalanceResult

    async def backupAssetStandAlone(self, pool, addr, uid, coin_symbol, coin_amount):
        coin_symbol = coin_symbol.replace("_", "")
        if coin_symbol == "BTC":
            await self.assetControlAllAddrUnit((addr, uid, coin_symbol, coin_amount), None, None, None)
        if coin_symbol == "USDT":
            await self.assetControlAllAddrUnit((addr, uid, coin_symbol, coin_amount), None, None, None)
        else:
            tokensAll = await self.getCoins(pool)
            tokensAll = tokensAll["coinsInfo"]
            pricesCoins = await self.dbRun(pool, "select symbol,usd,cny from jl_coins where enable = 1")
            resultsGas = await self.dbRun(pool, "select id,type,detial from jl_extension where type in ('ETH_gasPrice','ETH_gas','RAM_gas') order by id asc")
            await self.assetControlAllAddrUnit((addr, uid, coin_symbol, None), tokensAll, pricesCoins, resultsGas)

    def wei2ether(self, valueToCvrt):
        if self.isDigit(valueToCvrt):
            changeHex = hex(int(valueToCvrt * 10 ** 18))
            change = valueToCvrt
        else:
            change = "%.14f" % float(float(int(valueToCvrt, 16)) / 10 ** 18)
            changeHex = valueToCvrt
        return {"change": change, "changeHex": changeHex}

    async def getAssetBalanceByAddr(self, coin_symbol, addrUsr, tokenAddr=None, tokenDemical=None):
        coin_symbol = coin_symbol.replace("_", "")
        if coin_symbol == "BTC":
            async with aiohttp.ClientSession() as session:
                await asyncio.sleep(Cfg.SEM_BLOCKCHAININFO_TIMEWAITING)
                try:
                    async with session.get(f"{Cfg.BALANCE_GET_BTC}{addrUsr}") as P_get:
                        if P_get.status in [200, 201]:
                            dataGet = json.loads(await P_get.text(encoding="utf8"))
                            usrBalanceHex = dataGet[addrUsr]["final_balance"]
                            return round(float(float(usrBalanceHex) / 10 ** 8), 10), usrBalanceHex
                        else:
                            errMsg = f"{P_get.host} - {P_get.status} - {P_get.reason}"
                            self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", errMsg)
                            return None
                except Exception as e:
                    self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", repr(e))
                    return None
        elif coin_symbol == "ETH":
            usrBalanceHex = await self.rpcWallet("eth_getBalance", [addrUsr, "latest"])
            if usrBalanceHex != None:
                usrBalance = self.wei2ether(usrBalanceHex)
                return float(usrBalance["change"]), usrBalanceHex
            else:
                return None
        elif coin_symbol == "USDT":
            usrBalanceHex = await self.rpcWallet("omni_getbalance", [addrUsr, 31], "USDT")
            if usrBalanceHex != None:
                usrBalance = float(usrBalanceHex["balance"])
                return usrBalance, usrBalanceHex
            else:
                return None
        else:
            usrAddr = addrUsr[2:]
            params = [{"data": f"0x70a08231000000000000000000000000{usrAddr}", "to": tokenAddr}, "latest"]
            usrBalanceHex = await self.rpcWallet("eth_call", params)
            if usrBalanceHex != None and usrBalanceHex != "0x":
                return float(int(usrBalanceHex, 16)) / (10 ** tokenDemical), usrBalanceHex
            else:
                return None

    async def assetControlAllAddrUnit(self, usrInfos, tokensAll, pricesCoins, resultsGas):
        addrUsr, uidUsr, coin_symbol, usrBalance = usrInfos
        coin_symbol = coin_symbol.replace("_", "")
        if coin_symbol == "BTC":
            if not usrBalance:
                result = await self.getAssetBalanceByAddr(coin_symbol, addrUsr)
                if not result:
                    return None
                usrBalance, usrBalanceHex = result
            if usrBalance < Cfg.BTC_MAX_USR_ASSET:
                return None
            usrBalanceResult = await self.rpcAsset(float(usrBalance), "BTC")
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"Backup usr {usrBalance} ETH assets {usrInfos} - result: {usrBalanceResult}")
        elif coin_symbol == "USDT":
            if not usrBalance:
                result = await self.getAssetBalanceByAddr(coin_symbol, addrUsr)
                if not result:
                    return None
                usrBalance, usrBalanceHex = result
            if usrBalance < Cfg.USDT_MAX_USR_ASSET:
                return None
            await self.rpcAsset([uidUsr, usrBalance], "USDT")
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"Backup usr {usrBalance} USDT assets {usrInfos} - result: {usrBalanceResult}")
        elif coin_symbol == "ETH":
            # self.logger.debug(f"Try ETH {usrInfos}")
            if not usrBalance:
                result = await self.getAssetBalanceByAddr(coin_symbol, addrUsr)
                if not result:
                    return None
                usrBalance, usrBalanceHex = result
            if usrBalance < Cfg.ETH_MAX_USR_ASSET:
                return None
            usrBalanceResult = await self.rpcAsset([uidUsr, usrBalance], "ETH")
            self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"Backup usr {usrBalance} ETH assets {usrInfos} - result: {usrBalanceResult}")

        else:
            # 50usd or 300cny
            coinUSDPrice = [coin[1] for coin in pricesCoins if coin[0] == coin_symbol]
            tokenAddr = [token[3] for token in tokensAll if token[0] == coin_symbol]
            tokenDemical = [token[4] for token in tokensAll if token[0] == coin_symbol]
            if not (len(coinUSDPrice) * len(tokenAddr) * len(tokenDemical)):
                return None
            coinUSDPrice, tokenAddr, tokenDemical = float(coinUSDPrice[0]), tokenAddr[0], tokenDemical[0]
            if not usrBalance:
                result = await self.getAssetBalanceByAddr(coin_symbol, addrUsr, tokenAddr, tokenDemical)
                if not result:
                    return None
                usrBalance, usrBalanceHex = result
            if usrBalance != 0.0:
                usrBalanceHex = usrBalanceHex[2:]
                # usrBalanceHex = hex(int(usrBalanceHex, 16))[2:]
                if usrBalance * coinUSDPrice <= Cfg.USD_MAX_USR_ASSET:
                    return None
                usrBalanceETH = await self.rpcWallet("eth_getBalance", [addrUsr, "latest"])
                usrAssetETH = self.wei2ether(usrBalanceETH)
                if float(usrAssetETH["change"]) < Cfg.ETH_ASSET_USR_MIN:
                    usrBalanceResult = await self.preTransEthSmallAmount(addrUsr, resultsGas[0][2], hex(int(resultsGas[1][2])))
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"Step0 - result:{usrBalanceResult} - coinbase ETH transfer to {uidUsr} - param:{paramPreTransfer}")
                    if not usrBalanceResult[0]:
                        return None
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"Step1 {coin_symbol}>50usd - UID:{uidUsr} - UsrAddr:{addrUsr} - {usrBalance}*{coinUSDPrice} - params:{params}")
                if coin_symbol == "EUSDT":
                    paramsAssets = [{"from": f"{uidUsr}", "to": f"0x{Cfg.ETH_BACKUP_ADDR}", "gas": f"{hex(int(resultsGas[2][2]))}", "gasPrice": f"{resultsGas[0][2]}", "value": f"{usrBalance}", "data": "0x"}]
                    usrBalanceResult = await self.rpcAsset(paramsAssets, coin_symbol)
                    self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"transfer params:{paramsAssets} - Cfg.ETH_BACKUP_ADDR:{Cfg.ETH_BACKUP_ADDR} - usrBalanceHex:{usrBalanceHex}")
                else:
                    paramsAssets = [{"from": f"{uidUsr}", "to": f"{tokenAddr}", "gas": f"{hex(int(resultsGas[2][2]))}", "gasPrice": f"{resultsGas[0][2]}", "value": "0x0", "data": f"0xa9059cbb000000000000000000000000{Cfg.ETH_BACKUP_ADDR}{usrBalanceHex}"}]
                    usrBalanceResult = await self.rpcAsset(paramsAssets, coin_symbol)
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"Step2 - Result:{usrBalanceResult} - transfer params:{paramsAssets} - coinbaseETH:{Cfg.ETH_BACKUP_ADDR} - usrBalanceHex:{usrBalanceHex} ")
        return f"{uidUsr} {coin_symbol} {addrUsr} backuped"

    def taskListGet(self, resultsDB, tokensAll, pricesCoins, resultsGas):
        tasks = []
        lenList = len(resultsDB)
        for index, usrInfos in enumerate(resultsDB):
            addr, uid, coin_symbol = usrInfos
            tasks.append(asyncio.ensure_future(self.assetControlAllAddrUnit((addr, uid, coin_symbol, None), tokensAll, pricesCoins, resultsGas)))
            if index % Cfg.SEM_ASSET == 0 or index == lenList - 1:
                yield tasks
                tasks = []

    async def assetControlAllAddr(self, pool):
        # 300rmb 50usd
        await self.updateCoinsPrices(pool)
        tasks = []
        numCoroutine = 1
        resultsDB = await self.dbRun(pool, f"select addr,uid,coin_symbol from jl_member_wallets where network = {Cfg.IF_TEST_NET} order by uid asc")
        tokensAll = await self.getCoins(pool)
        tokensAll = tokensAll["coinsInfo"]
        pricesCoins = await self.dbRun(pool, "select symbol,usd,cny from jl_coins where enable = 1")
        resultsGas = await self.dbRun(pool, "select id,type,detial from jl_extension where type in ('ETH_gasPrice','ETH_gas','RAM_gas') order by id asc")
        taskGenerator = self.taskListGet(resultsDB, tokensAll, pricesCoins, resultsGas)
        for iTaskGenerator in taskGenerator:
            for iTask in asyncio.as_completed(iTaskGenerator):
                # async with sem_asset:
                result = await iTask
                numCoroutine += 1
                # self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"taskDone: {numCoroutine}")
                print(f"taskDone: {numCoroutine} of {len(resultsDB)}")
                if result:
                    self.log.success(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", f"{result}")

    async def rpcAsset(self, params, coin_symbol="ETH"):
        """根据coin_symbol用rpc命令与热钱包交互"""
        headers = {"Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            try:
                if coin_symbol == "BTC":
                    idAuth = aiohttp.BasicAuth(Cfg.BTC_USR, Cfg.BTC_PWD)
                    async with session.post(Cfg.BTC_HOST, headers=headers, json={"jsonrpc": "2.0", "method": "sendtoaddress", "params": [Cfg.BTC_BACKUP_ADDR, params], "id": 1}, auth=idAuth) as P_post:
                        return None, await P_post.text("utf8")
                elif coin_symbol == "USDT":
                    idAuth = aiohttp.BasicAuth(Cfg.USDT_USR, Cfg.USDT_PWD)
                    usrAddr = params[0]
                    balanceHex = params[3]["balance"]
                    params = [usrAddr, Cfg.USDT_BACKUP_ADDR, 31, balanceHex, Cfg.USDT_BACKUP_ADDR]
                    # http://cw.hubwiz.com/card/c/omni-rpc-api/1/1/22/
                    async with session.post(Cfg.USDT_HOST, headers=headers, json={"jsonrpc": "2.0", "method": "omni_funded_send", "params": params}, auth=idAuth) as P_post:
                        return None, await P_post.text("utf8")
                else:
                    headers = {"Content-Type": "application/json"}
                    if coin_symbol == "ETH":
                        paramsJson = [{"from": str(params[0]), "to": f"0x{Cfg.ETH_BACKUP_ADDR}", "gas": Cfg.ETH_BACKUP_GAS, "gasPrice": Cfg.ETH_BACKUP_GAS_PRICE, "value": str(float(params[1]) - Cfg.ETH_EXCHANGE_FEE), "data": "0xd46e8dd67c5d32be8d46e8dd67c5d32be8058bb8eb970870f072445675058bb8eb970870f072445675"}]
                        P_post = await session.post(Cfg.ETH_HOST, headers=headers, json={"jsonrpc": "2.0", "method": "eth_sendTransaction3", "params": paramsJson, "id": 1})
                    elif coin_symbol == "ETHPreTransfer":
                        paramsJson = [{"from": Cfg.ETH_TO_UID, "to": str(params[0]), "gas": params[3], "gasPrice": params[2], "value": str(params[1]), "data": "0x"}]
                        P_post = await session.post(Cfg.ETH_HOST, headers=headers, json={"jsonrpc": "2.0", "method": "eth_sendTransaction", "params": paramsJson, "id": 1})
                    elif coin_symbol == "EUSDT":
                        paramsJson = params
                        P_post = await session.post(Cfg.ETH_HOST, headers=headers, json={"jsonrpc": "2.0", "method": "eth_sendTransactionEUSDT", "params": paramsJson, "id": 1})
                    else:
                        paramsJson = params
                        P_post = await session.post(Cfg.ETH_HOST, headers=headers, json={"jsonrpc": "2.0", "method": "eth_sendTransaction", "params": paramsJson, "id": 1})
                    if P_post.status in [200, 201]:
                        result = json.loads(await P_post.text())
                        if result["error"]:
                            errMsg = f"{P_post.host} - {P_post.status} - {P_post.reason} - {result}"
                            self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", errMsg)
                            return (None, result)
                        return (True, result)
                    else:
                        errMsg = f"{P_post.host} - {P_post.status} - {P_post.reason}"
                        self.log.err(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", errMsg)
                        return (None, f"{P_post.status} - {await P_post.text()} - Request:{P_post.request.body}")
            except Exception as e:
                self.log.info(self.tableName, f"{self.tableName}.{sys._getframe().f_code.co_name}", repr(e))
                return None, e
