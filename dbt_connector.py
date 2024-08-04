from datetime import datetime
from os import getenv
from typing import Union

import pytz
import requests


class DbtConnector:

    _BASE_URL = getenv("DBT_BASE_URL")

    def __init__(self, account_id: Union[None, int] = None, job_id: Union[None, int] = None):
        self._account_id = getenv("DBT_ACCOUNT_ID") or account_id
        self._job_id = getenv("DBT_JOB_ID") or job_id

    def _api_url(self, job_id: int) -> str:
        return f"{self._BASE_URL}{self._account_id}/jobs/{job_id}/run/"

    @staticmethod
    def _generate_cause_message() -> str:
        # Get the current time in UTC
        utc_now = datetime.now(pytz.utc)
        pst_timezone = pytz.timezone('US/Pacific')
        pst_now = utc_now.astimezone(pst_timezone).strftime('%Y-%m-%d %H:%M:%S %Z%z')
        utc_now = utc_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')

        return f"Job run via the API at {pst_now} PST ({utc_now} UTC)"

    def run_job(self, job_id: Union[None, int] = None, cause: Union[None, str] = None) -> bool:
        if job_id is not None:
            url = self._api_url(job_id)
        else:
            url = self._api_url(self._job_id)

        headers = {"Authorization": f"Token {getenv('DBT_PERSONAL_ACCESS_TOKEN')}"}

        if cause is None:
            cause = self._generate_cause_message()

        body = {"cause": cause}

        response = requests.post(url, data=body, headers=headers)

        success = response.json()["status"]["code"]
        if success == 200:
            return True
        else:
            return False