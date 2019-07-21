import requests
import json

with open('config.json') as f:
    parameters = json.load(f)['parameters']

querystring = {
    "status":"live",
    "time_filter":"all",
    "order_by": "start_asc"
    }


headers = {
    'Authorization': "Bearer IZT6VTPWISIUIMS45BFE"
}

url = BASE_URL + ORG_ID + '/events/' + '?expand=event_sales_status'
response = requests.get(url=url, headers=headers, params=querystring)

response = json.loads(response.text)

events = []
for event in response['events']:
    if event["id"] != "53765820015":
        summary = {}
        summary["id"] = event["id"]
        summary["name"] = event["name"]["text"]
        summary["url"] = event['url']
        summary["starts"] = event["start"]["local"]
        summary["ends"] = event["end"]["local"]
        summary["timezone"] = event["start"]["timezone"]
        summary["published"] = event["published"]
        summary["capacity"] = event["capacity"]
        summary["event_sales_status"] = event["event_sales_status"]["sales_status"]
        events.append(summary)

for event in events:
    print(event, '\n')