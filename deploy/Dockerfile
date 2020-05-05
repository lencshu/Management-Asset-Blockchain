FROM python:3.8-slim
LABEL date=16082019

RUN pip install --no-cache-dir aiohttp
RUN pip install --no-cache-dir aiomysql
RUN pip install --no-cache-dir fastapi
RUN pip install --no-cache-dir uvicorn
RUN pip install --no-cache-dir aiosqlite
RUN pip install --no-cache-dir aiosmtplib
RUN pip install --no-cache-dir aiofiles

WORKDIR /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80","--reload"]

# RUN pip install --no-cache-dir databases[sqlite]

# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r requirements.txt

# docker-compose up --build