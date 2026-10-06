
import json
import boto3


TABLE_NAME = "details.table"
REGION = "ap-south-1"

# Create DynamoDB client
dynamodb = boto3.client("dynamodb", region_name=REGION)


# --------------------------------------------------
# COMMON RESPONSE
# --------------------------------------------------

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


# --------------------------------------------------
# MAIN HANDLER
# --------------------------------------------------

def handler(event, context):

    print("Event:", event)

    try:

        http_method = event.get("httpMethod", "")

        path_parameters = event.get("pathParameters") or {}
        body = event.get("body") or "{}"

        # CORS preflight request
        if http_method == "OPTIONS":
            return response(
                200,
                {"message": "CORS OK"}
            )

        # CREATE
        elif http_method == "POST":
            return handle_post(body)

        # READ
        elif http_method == "GET":
            return handle_get(path_parameters)

        # UPDATE
        elif http_method == "PUT":
            return handle_put(path_parameters, body)

        # DELETE
        elif http_method == "DELETE":
            return handle_delete(path_parameters)

        # Unknown method
        else:
            return response(
                405,
                {"error": "Method not allowed"}
            )

    except Exception as error:

        print("Error:", str(error))

        return response(
            500,
            {"error": str(error)}
        )


# --------------------------------------------------
# CREATE
# POST /contacts
# --------------------------------------------------

def handle_post(body):

    data = json.loads(body)

    item_id = data.get("id")
    name = data.get("name")
    email = data.get("email")

    if not item_id or not name or not email:

        return response(
            400,
            {
                "error": "id, name and email are required"
            }
        )

    dynamodb.put_item(
        TableName=TABLE_NAME,
        Item={
            "id": {"S": item_id},
            "name": {"S": name},
            "email": {"S": email}
        }
    )

    return response(
        201,
        {
            "message": "Contact created successfully",
            "data": data
        }
    )


# --------------------------------------------------
# READ
# GET /contacts
# GET /contacts/{id}
# --------------------------------------------------

def handle_get(path_parameters):

    item_id = path_parameters.get("id")

    # Get ONE contact
    if item_id:

        result = dynamodb.get_item(
            TableName=TABLE_NAME,
            Key={
                "id": {"S": item_id}
            }
        )

        item = result.get("Item")

        if not item:

            return response(
                404,
                {"error": "Contact not found"}
            )

        contact = {
            "id": item["id"]["S"],
            "name": item.get("name", {}).get("S", ""),
            "email": item.get("email", {}).get("S", "")
        }

        return response(
            200,
            contact
        )

    # Get ALL contacts
    result = dynamodb.scan(
        TableName=TABLE_NAME
    )

    contacts = []

    for item in result.get("Items", []):

        contacts.append(
            {
                "id": item["id"]["S"],
                "name": item.get("name", {}).get("S", ""),
                "email": item.get("email", {}).get("S", "")
            }
        )

    return response(
        200,
        contacts
    )


# --------------------------------------------------
# UPDATE
# PUT /contacts/{id}
# --------------------------------------------------

def handle_put(path_parameters, body):

    item_id = path_parameters.get("id")

    if not item_id:

        return response(
            400,
            {"error": "id is required"}
        )

    data = json.loads(body)

    name = data.get("name")
    email = data.get("email")

    if not name or not email:

        return response(
            400,
            {
                "error": "name and email are required"
            }
        )

    result = dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={
            "id": {"S": item_id}
        },
        UpdateExpression="SET #name = :name, #email = :email",
        ExpressionAttributeNames={
            "#name": "name",
            "#email": "email"
        },
        ExpressionAttributeValues={
            ":name": {"S": name},
            ":email": {"S": email}
        },
        ReturnValues="ALL_NEW"
    )

    updated_item = result.get("Attributes", {})

    return response(
        200,
        {
            "message": "Contact updated successfully",
            "data": {
                "id": item_id,
                "name": updated_item.get("name", {}).get("S", ""),
                "email": updated_item.get("email", {}).get("S", "")
            }
        }
    )


# --------------------------------------------------
# DELETE
# DELETE /contacts/{id}
# --------------------------------------------------

def handle_delete(path_parameters):

    item_id = path_parameters.get("id")

    if not item_id:

        return response(
            400,
            {"error": "id is required"}
        )

    dynamodb.delete_item(
        TableName=TABLE_NAME,
        Key={
            "id": {"S": item_id}
        }
    )

    return response(
        200,
        {
            "message": "Contact deleted successfully",
            "id": item_id
        }
    )


# --------------------------------------------------
# LOCAL TEST
# --------------------------------------------------

if __name__ == "__main__":

    with open("event.json") as f:

        event = json.load(f)

    result = handler(event, None)

    print(result)
