import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient, exceptions

COSMOS_URL = os.environ["COSMOS_URL"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
DB_NAME    = os.environ.get("COSMOS_DB", "pantry")
CONTAINER  = os.environ.get("COSMOS_CONTAINER", "state")
DOC_ID     = "pantry_state"

def get_container():
    client = CosmosClient(COSMOS_URL, COSMOS_KEY)
    db = client.get_database_client(DB_NAME)
    return db.get_container_client(CONTAINER)

def main(req: func.HttpRequest) -> func.HttpResponse:
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    }
    try:
        container = get_container()

        if req.method == "GET":
            try:
                item = container.read_item(item=DOC_ID, partition_key=DOC_ID)
                return func.HttpResponse(json.dumps(item), headers=headers)
            except exceptions.CosmosResourceNotFoundError:
                empty = {
                    "id": DOC_ID,
                    "ingredients": [],
                    "recipes": [],
                    "shopping_checked": {}
                }
                container.upsert_item(empty)
                return func.HttpResponse(json.dumps(empty), headers=headers)

        if req.method == "POST":
            body = req.get_json()
            body["id"] = DOC_ID
            container.upsert_item(body)
            return func.HttpResponse(json.dumps({"ok": True}), headers=headers)

        return func.HttpResponse("Method not allowed", status_code=405, headers=headers)
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e), "type": type(e).__name__}),
            status_code=500,
            headers=headers
        )
