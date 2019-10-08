import json
import logging
import os
import requests


class API:
    def __init__(self):
        self.domain = os.getenv("API_DOMAIN")
        self.account_email = os.getenv("API_ACCOUNT_EMAIL")
        self.api_tokens = [
            os.getenv("API_TOKEN_DATA"),
            os.getenv("API_TOKEN_DATA_INDEX"),
        ]

    def _post_demand_export(self, api_token):
        """ Post request to SchoolMint API 
        Triggers report generation and upload to FTP associated with the report """
        domain = self.domain
        account_email = self.account_email
        url = "https://" + domain + "/api/v2/demand_exports"
        headers = {"Api-Token": api_token}
        body = {"account_email": account_email}
        response = requests.post(url, headers=headers, data=body)
        if response.ok:
            j_data = json.loads(response.content.decode())
            logging.info(
                "API Token: " + api_token + " - Status: " + str(j_data["status"]) + "\n"
            )
        else:
            j_data = json.loads(response.content.decode())
            logging.info(
                "API Token: "
                + api_token
                + " - Error Code: "
                + str(j_data["error_code"])
            )
            logging.info("Error Message: " + j_data["error_msg"] + "\n")
            response.raise_for_status()

    def request_reports(self):
        """ Demand export for each api token"""
        for api_token in self.api_tokens:
            self._post_demand_export(api_token=api_token)
