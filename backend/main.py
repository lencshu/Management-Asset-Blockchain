from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


from _lib.routes import apis
from _lib import *

app = FastAPI(docs_url="/api/docs", redoc_url="/api/redoc",template_directory='dists')

app.include_router(
    apis,
    responses={404:{"description":"Not Found"}}
)

app.mount("/static/fonts", StaticFiles(directory="dists/static/fonts"), name="fonts")
app.mount("/static/js", StaticFiles(directory="dists/static/js"), name="js")
app.mount("/static/css", StaticFiles(directory="dists/static/css"), name="js")
