import json
import logging
from os import getenv
import requests

class API:
    def __init__(self):
        self.domain = getenv("API_DOMAIN")
        self.account_email = getenv("API_ACCOUNT_EMAIL")

    # Post request to SchoolMint API
    # Triggers report generation and upload to FTP associated with the report
    def post_demand_export(self, api_token):
        domain = self.domain
        account_email = self.account_email
        url = 'https://' + domain + '/api/v2/demand_exports'
        headers = {'Api-Token': api_token}
        body = {'account_email': account_email}
        response = requests.post(url, headers=headers, data=body)
        if (response.ok):
            j_data = json.loads(response.content.decode())
            logging.info("API Token: " + api_token + " - Status: " + str(j_data['status']) + "\n")
        else:
            j_data = json.loads(response.content.decode())
            logging.info("API Token: " + api_token + " - Error Code: " + str(j_data['error_code']))
            logging.info("Error Message: " + j_data['error_msg'] + "\n")
            response.raise_for_status()