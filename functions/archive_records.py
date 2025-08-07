from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
import datetime, json, gzip, os

cosmos_client = CosmosClient(os.environ['COSMOS_URI'], credential=os.environ['COSMOS_KEY'])
database = cosmos_client.get_database_client('BillingDB')
container = database.get_container_client('Records')

blob_service = BlobServiceClient.from_connection_string(os.environ['BLOB_CONN_STR'])
archive_container = blob_service.get_container_client('billing-archive')

def archive_old_records():
    threshold_date = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    query = "SELECT * FROM Records r WHERE r.timestamp < @date"
    items = container.query_items(
        query,
        parameters=[{"name": "@date", "value": threshold_date.isoformat()}],
        enable_cross_partition_query=True
    )

    for item in items:
        record_id = item['id']
        compressed_data = gzip.compress(json.dumps(item).encode('utf-8'))
        blob_name = f"{record_id}.json.gz"
        archive_container.upload_blob(name=blob_name, data=compressed_data, overwrite=True)
        container.delete_item(item=item['id'], partition_key=item['partitionKey'])
