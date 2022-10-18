import os

from appwrite.client import Client
from appwrite.query import Query
from appwrite.services.databases import Databases
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

load_dotenv()

app = FastAPI()
client = Client()

(client
 .set_endpoint(os.environ['AW_ENDPOINT'])  # Your API Endpoint
 .set_project(os.environ['AW_PROJECT'])  # Your project ID
 .set_key(os.environ['AW_KEY'])  # Your secret API key
 .set_self_signed()
 )
dbs = Databases(client)


@app.get("/{alias}")
async def index(alias: str):
    response = dbs.list_documents(os.environ['AW_DB'], os.environ['AW_LINKS_COLLECTION'], queries=[
        Query.equal("alias", alias)])

    if response['total'] == 0:
        return {"error": "Alias not found"}
    dbs.update_document(os.environ['AW_DB'], os.environ['AW_LINKS_COLLECTION'], response['documents'][0]['$id'], {
        'clicks': response['documents'][0]['clicks'] + 1
    })
    return RedirectResponse(response['documents'][0]['long_url'])

