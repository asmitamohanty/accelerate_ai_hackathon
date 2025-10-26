from fivetran_connector_sdk import Connector, Operations as op
import requests
from datetime import datetime


table_config = [
  {
    "table": "disasters_200",
    "columns": {
      "id": "STRING",
      "title": "STRING",
      "date": "STRING",
      "country": "STRING",
      "type": "STRING",
      "status": "STRING",
      "description": "STRING"
    }
  }
]

class Disaster(Connector):
    @staticmethod
    def schema(configuration):
        return table_config

    @staticmethod
    def update(configuration, state):

        url = "https://api.reliefweb.int/v2/disasters"
        params = {
            "appname": "disaster_rag_final",
            "limit": 200,
            "fields[include][]": ["name","date","status","type","country","description","url"],
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
                "type": (fields.get("type") or [{}])[0].get("name") if fields.get("type") else None,
                "status":fields.get("status"),
                "description": fields.get("description")
            }
            op.upsert(table="disasters_200", data=record)
            #print(record)

        new_state = {"last_sync_timestamp": datetime.utcnow().isoformat()}
        op.checkpoint(state=new_state)
        
_disaster_connector = Disaster(update={})
connector = Connector(
    update=_disaster_connector.update,
    schema=_disaster_connector.schema
)
