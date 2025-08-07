from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
import json, gzip, os

cosmos_client = CosmosClient(os.environ['COSMOS_URI'], credential=os.environ['COSMOS_KEY'])
database = cosmos_client.get_database_client('BillingDB')
container = database.get_container_client('Records')

blob_service = BlobServiceClient.from_connection_string(os.environ['BLOB_CONN_STR'])
archive_container = blob_service.get_container_client('billing-archive')

def read_record(record_id, partition_key):
    try:
        record = container.read_item(item=record_id, partition_key=partition_key)
        return record
    except Exception:
        blob_name = f"{record_id}.json.gz"
        blob_client = archive_container.get_blob_client(blob_name)
        compressed_data = blob_client.download_blob().readall()
        record = json.loads(gzip.decompress(compressed_data))
        return record
