# schoolmint_connector
Data pipeline for Schoolmint application data. This pipeline pings Schoolmint's API to generate a report that is sent to an SFTP server. The pipeline then loads that file from the SFTP server to Google Cloud Storage.

## Dependencies:

* Python3
* [Pipenv](https://pipenv.readthedocs.io/en/latest/)
* [Docker](https://www.docker.com/)
* Google Cloud Storage

### Additional Dependencies

This job requires an FTP server for Schoolmint to drop the files on. Our org uses a Digital Ocean droplet, but a SFTP server through any service should work. 
You will need to provide some info about the server to Schoolmint so they can create your API token.

## Getting Started

### Setup Environment

1. Clone this repo

```
$ git clone https://github.com/kippnorcal/ukg-connector.git 
```

2. Install Pipenv

```
$ pip install pipenv
$ pipenv install
```

3. Install Docker

* **Mac**: [https://docs.docker.com/docker-for-mac/install/](https://docs.docker.com/docker-for-mac/install/)
* **Linux**: [https://docs.docker.com/install/linux/docker-ce/debian/](https://docs.docker.com/install/linux/docker-ce/debian/)
* **Windows**: [https://docs.docker.com/docker-for-windows/install/](https://docs.docker.com/docker-for-windows/install/)

4. Create .env file with project secrets

```
DELETE_LOCAL_FILES=1
REJECT_EMPTY_FILES=0

# Google Storage Info
GOOGLE_APPLICATION_CREDENTIALS= # Path to your cred file
BUCKET= # Name of your Cloud Storage Bucket

# FTP Credential Variables
FTP_HOSTNAME=
FTP_USERNAME=
FTP_PWD=
FTP_KEY=
ARCHIVE_MAX_DAYS=60

# API Variables
API_SUFFIXES=
API_DOMAIN_REGIONAL=
API_ACCOUNT_EMAIL_REGIONAL=
API_TOKEN_REGIONAL=

# Slack Notifications
FROM_ADDRESS=
TO_ADDRESS=
MG_API_KEY=
MG_API_URL=
MG_DOMAIN=
FAILURE_EMAIL=  # Address of Slack channel for failure emails

# dbt variables
DBT_ACCOUNT_ID=
DBT_JOB_ID=
DBT_BASE_URL=
DBT_PERSONAL_ACCESS_TOKEN=
```
#### Note on API_SUFFIXES

Our org had a need to get Schoolmint data from multiple API's that had the same name except for the final word in the
name. The automation will iterate over each suffix listed in `API_SUFFIXES` and join them with `API_DOMAIN_REGIONAL` to 
get the full endpoint name. At some point, this will be removed since we are no long using multiple endpoints.

5. Build Docker Image

```
$ docker build -t schoolmint .
```

### Running the Job

Here are the runtime arguments for the job:

| Arg              | Description                                                                                                                     |
|------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `--school-year`  | Required; Determines which school year the job is processing; The value of this arg gets added to a `school_year_4_digit` field |
| `--dbt-refresh`  | Optional; Can run a job in dbt to refresh Schoolmint data                                                                       |
| `--semt-refresh` | Optional; Runs an adhoc dbt job to refresh the source of the SEMT trackers                                                      |


#### Examples

Run the job:
```
docker run --rm -t --scool-year 2025
```

#### Maintenance

The token for Schoolmint's API needs to be updated annually. This can be updated in the .env file
