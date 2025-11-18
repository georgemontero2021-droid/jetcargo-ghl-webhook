# GoHighLevel - Create Opportunity API

## Endpoint
```
POST https://services.leadconnectorhq.com/opportunities/
```

## Headers
- `Authorization: Bearer <TOKEN>`
- `Version: 2021-07-28`
- `Content-Type: application/json`

## Required Fields
- `pipelineId` (string) - Pipeline ID
- `locationId` (string) - Location ID
- `name` (string) - Opportunity name
- `status` (string) - Possible values: open, won, lost, abandoned, all
- `contactId` (string) - Contact ID

## Optional Fields
- `pipelineStageId` (string) - Stage ID
- `monetaryValue` (number) - Value
- `assignedTo` (string) - User ID
- `customFields` (array) - Custom fields

## Example Request
```json
{
  "pipelineId": "VDm7RPYC2GLUvdpKmBfC",
  "locationId": "ve9EPM428h8vShlRW1KT",
  "name": "First Opps",
  "pipelineStageId": "7915dedc-8f18-44d5-8bc3-77c04e994a10",
  "status": "open",
  "contactId": "mTkSCb1UBjb5tk4OvB69",
  "monetaryValue": 220,
  "assignedTo": "082goXVW3lIExEQPOnd3",
  "customFields": [
    {
      "id": "6dvNaf7VhkQ9snc5vnjJ",
      "key": "my_custom_field",
      "field_value": "9039160788"
    }
  ]
}
```

## Scope Required
- `opportunities.write`
