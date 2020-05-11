import json
import logging
import os
import requests


class API:
    """Class for the SchoolMint API connection."""

    def __init__(self, env_suffixes=[""]):
        """Initialize environment variables used to connect to the API."""
        self.endpoints = []
        for suffix in env_suffixes:
            self.endpoints.append(
                {
                    "domain": os.getenv(f"API_DOMAIN{suffix}"),
                    "account_email": os.getenv(f"API_ACCOUNT_EMAIL{suffix}"),
                    "api_token": os.getenv(f"API_TOKEN{suffix}"),
                }
            )

    def _post_demand_export(self, endpoint):
        """
        Post request to SchoolMint API. This triggers report generation 
        and upload to FTP associated with the report.
        
        :param api_token: API token for the report.
        :type api_token: String
        """
        domain = endpoint.get("domain")
        account_email = endpoint.get("account_email")
        api_token = endpoint.get("api_token")
        url = "https://" + domain + "/api/v2/demand_exports"
        headers = {"Api-Token": api_token}
        body = {"account_email": account_email}
        response = requests.post(url, headers=headers, data=body)
        if response.ok:
            j_data = json.loads(response.content.decode())
            logging.info(
                "API Token: " + api_token + " - Status: " + str(j_data["status"])
            )
        else:
            j_data = json.loads(response.content.decode())
            logging.info(
                "API Token: "
                + api_token
                + " - Error Code: "
                + str(j_data["error_code"])
            )
            logging.info("Error Message: " + j_data["error_msg"])
            response.raise_for_status()

    def request_reports(self):
        """Demand export for each API token."""
        for endpoint in self.endpoints:
            self._post_demand_export(endpoint)
