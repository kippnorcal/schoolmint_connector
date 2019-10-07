# schoolmint_connector
Load all SchoolMint Application and Lottery Data into database for analysis.

## Dependencies
* Python3.7
* [Pipenv](https://pipenv.readthedocs.io/en/latest/)
* [Docker](https://www.docker.com/)
    * **Mac**: [https://docs.docker.com/docker-for-mac/install/](https://docs.docker.com/docker-for-mac/install/)
    * **Linux**: [https://docs.docker.com/install/linux/docker-ce/debian/](https://docs.docker.com/install/linux/docker-ce/debian/)
    * **Windows**: [https://docs.docker.com/docker-for-windows/install/](https://docs.docker.com/docker-for-windows/install/)


## Environment setup

### Clone the repo
```
git clone https://github.com/kipp-bayarea/schoolmint_connector.git
```

### Create .env file
```
DB_SERVER=
DB=
DB_USER=
DB_PWD=
DB_SCHEMA=

DB_RAW_TABLE=
DB_RAW_INDEX_TABLE=
SPROC_RAW_PREP=
SPROC_RAW_INDEX_PREP=
SPROC_CHANGE_TRACK=
SPROC_FACT_DAILY=

FTP_HOSTNAME=
FTP_USERNAME=
FTP_PWD=

API_DOMAIN=xxxxx.schoolmint.net
API_ACCOUNT_EMAIL=
API_TOKEN_DATA=
API_TOKEN_DATA_INDEX=

GMAIL_USER=
GMAIL_PWD=
SLACK_EMAIL=
TO_NAME=
TO_ADDRESS=
BCC_ADDRESS=
```

## Run the job

### Build docker image
```
docker build -t schoolmint .
```

### Run
```
docker run -it schoolmint
```

### Run with volume mapping
```
docker run -it -v ${PWD}:/code/ schoolmint
```