param location string = resourceGroup().location
param storageAccountName string
param cosmosAccountName string
param functionAppName string

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
}

resource blobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: storageAccount
  name: 'billing-archive'
  properties: {
    publicAccess: 'None'
  }
}

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
  }
}

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp'
  properties: {
    serverFarmId: '<APP_SERVICE_PLAN_ID>'
    siteConfig: {
      appSettings: [
        {
          name: 'COSMOS_URI'
          value: cosmosAccount.properties.documentEndpoint
        }
        {
          name: 'COSMOS_KEY'
          value: '<COSMOS_KEY>'
        }
        {
          name: 'BLOB_CONN_STR'
          value: '<BLOB_CONN_STR>'
        }
      ]
    }
  }
}
