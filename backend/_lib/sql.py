from _lib import *

# from databases import Database

# from multiprocessing.queues import Queue


class Sql(Process):
    lastRunTime = 0

    def __init__(self, lQueue):
        self.__class__.lastRunTime = time.time()
        self.lQueue = lQueue
        self.tableName = "Sql"
        super(Sql, self).__init__(name="SQL")
        self._exception = None
        # Queue.__init__(self,maxsize=maxsize,ctx=get_context())

    @property
    def exception(self):
        return self._exception

    async def main(self):
        self.database = await aiosqlite.connect(Cfg.PATH_SQLLITE)
        await self.tablaInit()
        while 1:
            # asyncio.sleep(0.1)
            elements = self.lQueue.get()
            tableName, typeMsg, funcName, logData, timestamp = elements
            if typeMsg == "err":
                tasks = [asyncio.ensure_future(self.emailSendSMTP(iAddr, elements)) for iAddr in Cfg.SMTP_DST_ADDR]
                for iTask in asyncio.as_completed(tasks):
                    status, resultSend = await iTask
                    await self.putSql((self.tableName, status, f"{funcName}", f"MailSent: {resultSend}", time.time()))
                    print("===email sent===")
            print(elements)
            await self.putSql(elements)
        # await self.tablaLog()

    def run(self):
        loop = asyncio.get_event_loop()
        # asyncio.ensure_future(self.main())
        # loop.run_forever()
        loop.run_until_complete(self.main())

    async def emailSendSMTP(self, dstAddr, elements):
        try:
            tableName, typeMsg, funcName, logData, timestamp = elements
            message = EmailMessage()
            message["From"] = Cfg.SMTP_USERNAME
            message["To"] = dstAddr
            message["Subject"] = "sepoch python infos"
            timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S.%f")
            message.set_content(f"Module: {tableName} \nType: {typeMsg} \nFuncName: {funcName} \nMsg: {logData} \nTime: {timestamp} \n\n\n --Sent via aiosmtplib")
            smtp = aiosmtplib.SMTP(hostname=Cfg.SMTP_HOST, port=Cfg.SMTP_PORT, use_tls=True)
            await smtp.connect()
            # await smtp.starttls()
            await smtp.login(Cfg.SMTP_USERNAME, Cfg.SMTP_PASSWORD)
            await smtp.send_message(message)
            await smtp.quit()
            return "info", logData
        except Exception as e:
            return f"err", e

    async def emailSendMailGun(self, elements):
        tableName, typeMsg, funcName, logData, timestamp = elements
        async with aiohttp.ClientSession() as session:
            try:
                idAuth = aiohttp.BasicAuth(Cfg.MAILGUN_AUTH_API, Cfg.MAILGUN_AUTH_APIKEY)
                async with session.post(Cfg.BTC_HOST, json={"from": "<mailgun@YOUR_DOMAIN_NAME>", "to": ["bar@example.com", "YOU@YOUR_DOMAIN_NAME"], "subject": "sepoch python infos", "text": elements}, auth=idAuth) as P_post:
                    resp = await P_post.text("utf8")
                    print(await P_post.text("utf8"))
                    if P_post.status == 200:
                        await self.putSql((self.tableName, "success", "emailSend", resp, time.time()))
                    else:
                        await self.putSql((self.tableName, "info", "emailSend", resp, time.time()))
            except Exception as e:
                await self.putSql((self.tableName, "err", "emailSend", e, time.time()))
                return e

    async def tablaInit(self):
        for tableName in ["ASSET", "ETH", "BTC", "USDT", "SQL"]:
            try:
                query = f"CREATE TABLE {tableName} (id INTEGER PRIMARY KEY,type TEXT,func TEXT, data TEXT, timestamp REAL)"
                await self.database.execute(query)
                await self.database.commit()
            except Exception as e:
                print(e)

    async def putSql(self, elements):
        tableName, typeMsg, funcName, logData, timestamp = elements
        values = (typeMsg, funcName, logData, timestamp)
        try:
            # async with aiosqlite.connect(self.database) as self.database:
            query = f"INSERT INTO {tableName} (type, func, data, timestamp) VALUES {values}"
            await self.database.execute(query)
            await self.database.commit()
        except Exception as e:
            print(f"table {tableName} already exists")

    async def readSql(self, tableName):
        query = f"SELECT * FROM {tableName}"
        rows = []
        async with self.database.execute(query) as cursor:
            rows = await cursor.fetchall()
        return rows
