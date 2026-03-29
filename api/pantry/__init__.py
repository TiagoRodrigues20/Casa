import azure.functions as func
import json
import os
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    }

    # Step 1: log all env vars to confirm they are present
    cosmos_url = os.environ.get("COSMOS_URL", "MISSING")
    cosmos_key = os.environ.get("COSMOS_KEY", "MISSING")
    logging.info(f"COSMOS_URL present: {cosmos_url != 'MISSING'}")
    logging.info(f"COSMOS_KEY present: {cosmos_key != 'MISSING'}")

    if cosmos_url == "MISSING" or cosmos_key == "MISSING":
        return func.HttpResponse(
            json.dumps({"error": "Missing COSMOS_URL or COSMOS_KEY environment variables"}),
            status_code=500,
            headers=headers
        )

    # Step 2: try to import and connect to Cosmos
    try:
        from azure.cosmos import CosmosClient, exceptions
        client = CosmosClient(cosmos_url, cosmos_key)
        db = client.get_database_client("pantry")
        container = db.get_container_client("state")
    except Exception as e:
        logging.error(f"Cosmos connection error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Cosmos connection failed: {str(e)}"}),
            status_code=500,
            headers=headers
        )

    # Step 3: handle GET
    if req.method == "GET":
        try:
            item = container.read_item(item="pantry_state", partition_key="pantry_state")
            return func.HttpResponse(json.dumps(item), status_code=200, headers=headers)
        except exceptions.CosmosResourceNotFoundError:
            empty = {"id": "pantry_state", "ingredients": [], "recipes": [], "shopping_checked": {}}
            container.upsert_item(empty)
            return func.HttpResponse(json.dumps(empty), status_code=200, headers=headers)
        except Exception as e:
            logging.error(f"GET error: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": f"GET failed: {str(e)}"}),
                status_code=500,
                headers=headers
            )

    # Step 4: handle POST
    if req.method == "POST":
        try:
            body = req.get_json()
            body["id"] = "pantry_state"
            container.upsert_item(body)
            return func.HttpResponse(json.dumps({"ok": True}), status_code=200, headers=headers)
        except Exception as e:
            logging.error(f"POST error: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": f"POST failed: {str(e)}"}),
                status_code=500,
                headers=headers
            )

    return func.HttpResponse(
        json.dumps({"error": "Method not allowed"}),
        status_code=405,
        headers=headers
    )
