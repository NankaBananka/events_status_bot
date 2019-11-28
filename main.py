import requests
import json
from jinja2 import Environment, PackageLoader, FileSystemLoader
import os

FLAGS = {
    "Asia/Singapore": ":flag-sg:",
    "Asia/Hong_Kong": ":flag-hk:",
    "Asia/Jakarta": ":flag-id:",
    "America/Los_Angeles": ":flag-us:",
    "Asia/Manila": ":flag-ph:",
    "Australia/Melbourne": ":flag-au:",
    "Australia/Sydney": ":flag-au",
    "Cambodia/Phnom_Penh": ":flag-kh",
    "Cambodia/Siem_Rip": ":flag-kh"
}


querystring = {
    "status":"live",
    "time_filter":"all",
    "order_by": "start_asc",
    "expand": "event_sales_status"
    }


def get_config():
    with open('/data/config.json') as f:
        print("getting parameters")
        parameters = json.load(f)['parameters']

    AUTH_EVENTBRITE = parameters['env']['#AUTH_EVENTBRITE']
    ORG_ID = parameters['env']['ORG_ID']
    WEBHOOK_URL = parameters['env']['#SLACK_WEBHOOK']
    BASE_URL = parameters['env']['BASE_URL']
    HEADERS = {'Authorization': 'Bearer ' + AUTH_EVENTBRITE}

    print(ORG_ID, WEBHOOK_URL, BASE_URL, HEADERS)
    return ORG_ID, WEBHOOK_URL, BASE_URL, HEADERS



def get_tickets_info(event_id, headers, base_url, querystring=querystring):
    url = base_url + "events/" + event_id +"/ticket_classes/"
    querystring = {
        "category": "all",
        "pos": "online"
    }

    response = requests.get(url=url, headers=headers, params=querystring)
    response = json.loads(response.text)

    tickets = []
    for c in response["ticket_classes"]:
        ticket = {}
        ticket["name"] = c["name"]
        ticket["total"] = c[ "quantity_total"]
        ticket["sold"] = c["quantity_sold"]
        if ticket["total"] - ticket["sold"] < 0:
            ticket["available"] = 0 
        else:
             ticket["available"] = ticket["total"] - ticket["sold"]
        tickets.append(ticket)

    return tickets


def get_events(org_id, headers, exclude:list, base_url, querystring=querystring):
    url = base_url + "organizations/" + org_id + '/events/'
    response = requests.get(url=url, headers=headers, params=querystring)
    response = json.loads(response.text)

    events = []
    for event in response['events']:
        if event["id"] not in exclude:
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
            summary["tickets"] = get_tickets_info(event["id"], headers, base_url)
            events.append(summary)

    return events

def send_slack(webhook_url, slack_data):

    # Set the webhook_url to the one provided by Slack when you create the webhook at https://my.slack.com/services/new/incoming-webhook/
    #webhook_url = webhook_url
    #slack_data = slack_data

    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )


def main():

    ORG_ID, webhook_url, BASE_URL, HEADERS = get_config()

    # Template file at ./app/templates/example.json
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    templateLoader = FileSystemLoader( searchpath=THIS_DIR )
    env = Environment( loader=templateLoader )
    env.filters['jsonify'] = json.dumps
    template = env.get_template('template.txt')
    
    events = get_events(org_id=ORG_ID, headers=HEADERS, exclude=["53765820015"], base_url=BASE_URL, querystring=querystring)
    slack_data = template.render(events=events, flags=FLAGS)
    send_slack(webhook_url, json.loads(slack_data))


main()
