# Cost-optimization-challenge--Sai-Lakshman
Managing Billing Records in Azure Serverless Architecture

Problem Statement:
------------------
Our Azure serverless system stores billing records in Azure Cosmos DB. Over time, the read-heavy nature and high record size (up to 300 KB) have led to growing storage and cost concerns. Records older than 3 months are rarely accessed, but still need to be retrievable with latency in seconds.

Goals:
------
Reduce storage costs

Ensure zero data loss

No API contract changes

No service downtime

Simple, maintainable architecture

Proposed Solution Overview:
---------------------------
Implement a tiered storage approach:

Active Records (< 3 months) remain in Cosmos DB

Cold Records (> 3 months) are moved to Azure Blob Storage in compressed form

Introduce a read-through caching mechanism that intercepts Cosmos DB read calls and checks Blob Storage if not found

Architecture Diagram:
---------------------
<img width="1536" height="911" alt="ChatGPT Image Aug 7, 2025, 10_54_02 PM" src="https://github.com/user-attachments/assets/7b72c24b-041b-4341-96a1-0b65d95adb4c" />

Detailed Steps
--------------
Step 1: Archival of Cold Data
-----------------------------
Use Azure Functions (Timer Trigger) to move data older than 3 months from Cosmos DB to Azure Blob Storage.

**Pseudocode for Archival:**
```
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
import datetime, json, gzip

cosmos_client = CosmosClient(url, credential)
database = cosmos_client.get_database_client('BillingDB')
container = database.get_container_client('Records')

blob_service = BlobServiceClient.from_connection_string(blob_conn_str)
archive_container = blob_service.get_container_client('billing-archive')

def archive_old_records():
    threshold_date = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    query = "SELECT * FROM Records r WHERE r.timestamp < @date"
    items = container.query_items(query, parameters=[{"name":"@date","value": threshold_date.isoformat()}], enable_cross_partition_query=True)
    for item in items:
        record_id = item['id']
        compressed_data = gzip.compress(json.dumps(item).encode('utf-8'))
        blob_name = f"{record_id}.json.gz"
        archive_container.upload_blob(name=blob_name, data=compressed_data, overwrite=True)
        container.delete_item(item, partition_key=item['partitionKey'])
```

Step 2: Read-through Access Layer
---------------------------------
Use Azure Function Proxy or Middleware in Function App to query Blob Storage if Cosmos returns a miss.

**Pseudocode for Retrieval**
```
def read_record(record_id):
    try:
        record = cosmos_container.read_item(item=record_id, partition_key=key)
        return record
    except Exception:
        blob_name = f"{record_id}.json.gz"
        blob_client = archive_container.get_blob_client(blob_name)
        compressed_data = blob_client.download_blob().readall()
        record = json.loads(gzip.decompress(compressed_data))
        return record
```

Cost Optimization Strategies:
-----------------------------
Cosmos DB TTL: Set TTL to auto-expire old records after archival

Blob Storage Tiering: Use Cool or Archive Tier for blob storage

Compression: Use GZip to reduce record size by 70-90%

Batch Archival: Schedule weekly/monthly archival to reduce read units

Deployment Notes:
-----------------

Use Bicep or Terraform to deploy blob containers, function apps

Setup identity-based access between Function App and Cosmos/Blob

Schedule archival via CRON expressions (Azure Timer Trigger)

No API Contract Change:
-----------------------
Function app exposes same endpoints

Wrap Cosmos + Archive logic in internal service layer

Client calls remain unchanged

No Downtime Transition:
-----------------------
Archive job is non-blocking

No writes are blocked

Retry logic can handle intermittent blob upload failures

Summary:
--------
This tiered-storage solution ensures cost savings by offloading cold data from Cosmos DB while ensuring full availability and consistency without API changes or service downtime. The design prioritizes simplicity using native Azure serverless components.


