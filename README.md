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

### FTP setup
Create a folder named 'archive' within the FTP directory that SchoolMint is dropping files to.


### Create .env file
```
DELETE_LOCAL_FILES=

DB_SERVER=
DB=
DB_USER=
DB_PWD=
DB_SCHEMA=

DB_RAW_TABLE=
DB_RAW_INDEX_TABLE=
SPROC_RAW_PREP=
SPROC_RAW_POST=
SPROC_RAW_INDEX_PREP=
SPROC_RAW_INDEX_POST=
SPROC_CHANGE_TRACK=
SPROC_FACT_DAILY=

FTP_Hostname=
FTP_Username=
FTP_PWD=
ARCHIVE_MAX_DAYS=

API_DOMAIN=
API_ACCOUNT_EMAIL=
API_TOKEN_DATA=
API_TOKEN_DATA_INDEX=
CURRENT_SCHOOL_YEAR=enrollment school year (eg. 2021 during the 19-20 SY)

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