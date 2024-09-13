import os
import time
import json
import requests
from datetime import datetime, timedelta, timezone
import pytz


DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
ALERT_API_TOKEN = os.getenv("ALERT_API_TOKEN")


alert_api_url = 'https://api.ukrainealarm.com/api/v3/alerts'
check_region_list = [
    "Сумська область", "Рівненська область", "Тернопільська область", "Івано-Франківська область"
]

ukraine_tz = pytz.timezone('Europe/Kiev')
utc_now = datetime.utcnow()
ukraine_time = pytz.utc.localize(utc_now).astimezone(ukraine_tz)
current_time = ukraine_time.replace(tzinfo=None, microsecond=0)


# discord logic
def send_to_discord_webhook(message):
    discord_webhook_data = {
        'content': message,
        'username': 'oleh-test-webhook'
    }
    discord_webhook_response = requests.post(
        DISCORD_WEBHOOK_URL, data=json.dumps(discord_webhook_data), headers={'Content-Type': 'application/json'}
    )
    if discord_webhook_response.status_code == 204:
        print('Message sent successfully!')
    else:
        print(f'Failed to send message: {response.status_code}, {response.text}')


# alert api logic
def check_active_alerts(alerts):
    reg_alerts = 0
    for alert in alerts:
        last_updated =  datetime.strptime(alert["lastUpdate"], "%Y-%m-%dT%H:%M:%SZ")
        print(last_updated)
        if (current_time - last_updated) <= timedelta(hours=8):
            reg_alerts += 1
    return reg_alerts


def call_regions():
    headers = {
        'accept': 'application/json',
        'Authorization': ALERT_API_TOKEN,
    }
    response = requests.get(alert_api_url, headers=headers)
    region_messages = []
    if response.status_code == 200:
        try:
            data = response.json()
            for region in data:
                if region["regionName"] in check_region_list:
                    reg_alerts = check_active_alerts(region["activeAlerts"])
                    if reg_alerts:
                        region_messages.append(region["regionName"])
            print(region_messages)
            if region_messages:
                send_to_discord_webhook(
                    f"{current_time} - за останню годину тривога почалася в таких областях: {', '.join(region_messages)}"
                )
            else:
                send_to_discord_webhook(f"{current_time} - немає тривог")
        except ValueError:
            print("Response content is not valid JSON:", response.text)
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")

if __name__ == '__main__':
    call_regions()
