from fivetran_connector_sdk import Connector, Operations as op
import requests
from datetime import datetime
# import json

# with open("configuration.json", "r") as file:
#     config = json.load(file)

table_config = [
  {
    "table": "disasters",
    "columns": {
      "id": "STRING",
      "title": "STRING",
      "date": "STRING",
      "country": "STRING",
      "type": "STRING",
      "status": "STRING"
    }
  }
]

class Disaster(Connector):
    @staticmethod
    def schema(configuration):
        return table_config

    @staticmethod
    def update(configuration, state):
        # url = config.get("api_url")
        # params = {
        #     "appname": config.get("app_name"),
        #     "limit": int(config.get("limit")),
        #     "fields[include][]": ["name", "date", "status", "type", "country", "url"],
        #     "sort[]": "date:desc"
        # }
        url = "https://api.reliefweb.int/v2/disasters"
        params = {
            "appname": "disaster_rag_test",
            "limit": 50,
            "fields[include][]": ["name","date","status","type","country","url"],
            "sort[]": "date:desc"
        }

        data_ = requests.get(url, params=params).json().get("data", [])

        #records = []
        for item in data_:
            fields = item["fields"]
            record={
                "id": item.get("id"),
                "title": fields.get("name"),
                "date": fields.get("date").get("changed"),
                "country": (fields.get("country") or [{}])[0].get("name") if fields.get("country") else None,
                "type": fields.get("primary_type", {}).get("name"),
                "status":fields.get("status")
            }
            op.upsert(table="disasters", data=record)
        #     data={
        #         "id": "1",
        #         "title": "test_record",
        #         "date": "2025-10-15",
        #         "country": "US",
        #         "type": "test",
        #         "status": "active"
        #   }
        # )
        new_state = {"last_sync_timestamp": datetime.utcnow().isoformat()}
        op.checkpoint(state=new_state)
        
_disaster_connector = Disaster(update={})
connector = Connector(
    update=_disaster_connector.update,
    schema=_disaster_connector.schema
)
# if __name__ == "__main__":
#         # Create instance
#     connector_instance = Disaster(update=None)
#     # Pass the instance method as a callable using lambda
#     connector_instance.update_method = lambda configuration, state: connector_instance.update(configuration, state)
    
#     # Run debug
#     #connector_instance.debug()
#     data = connector_instance.update(configuration={}, state={})
#     print("Tables returned:", list(data.keys()))
#     print("Sample records:", data["disasters"][:5])
