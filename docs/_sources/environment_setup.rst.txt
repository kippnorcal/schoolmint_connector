Initial environment setup
==========================

Clone the repo
---------------
.. code-block:: bash

    git clone https://github.com/kippnorcal/schoolmint_connector.git


FTP setup
-----------
Create a folder named 'archive' within the FTP directory that SchoolMint is dropping files to.

.. image:: _static/ftp_archive_folder.png

Create .env file
------------------
.. code-block:: text

    DELETE_LOCAL_FILES=

    DB_SERVER=
    DB=
    DB_SCHEMA=
    DB_USER=
    DB_PWD=

    DB_RAW_TABLE=
    SPROC_RAW_PREP=
    SPROC_RAW_POST=
    SPROC_CHANGE_TRACK=
    SPROC_FACT_DAILY=

    FTP_HOSTNAME=
    FTP_USERNAME=
    FTP_PWD=
    FTP_KEY=
    ARCHIVE_MAX_DAYS=

    API_SUFFIXES=
    
    API_DOMAIN_SUFFIX1=
    API_ACCOUNT_EMAIL_SUFFIX1=
    API_TOKEN_SUFFIX1=

    API_DOMAIN_SUFFIX2=
    API_ACCOUNT_EMAIL_SUFFIX2=
    API_TOKEN_SUFFIX2=

    CURRENT_SCHOOL_YEAR=

    GMAIL_USER=
    GMAIL_PWD=
    SLACK_EMAIL=
    TO_NAME=
    TO_ADDRESS=

**DELETE_LOCAL_FILES**: Keep downloaded files on the local machine or not. 
This setting doesn't matter when using Docker. Suggested: True.

**DB_SERVER, DB, DB_USER, DB_PWD, DB_SCHEMA**: Variables used by 
`sqlsorcery <https://sqlsorcery.readthedocs.io/en/latest/cookbook/environment.html>`_.

**DB_RAW_TABLE**: Name of the database table that the Application Data 
file data goes into.

**SPROC_RAW_PREP**: Name of the pre-processing sproc that backs up and 
truncates the Application Data table.

**SPROC_RAW_POST**: Name of the post-processing sproc that sets the 
SchoolYear4Digit column and restores from backup if the Application Data table is empty.

**SPROC_CHANGE_TRACK**: Name of the sproc that generates the Change History 
records.

**SPROC_FACT_DAILY**: Name of the sproc that generates the Fact Daily Status 
records.

**FTP_HOSTNAME, FTP_USERNAME, FTP_PWD, FTP_KEY**: FTP server connection variables.

**ARCHIVE_MAX_DAYS**: Files older than this number of days will be deleted from the FTP.

**API_SUFFIXES**: Comma separated (no space) list of API suffixes (see following definition)
(eg. _SUFFIX1,_SUFFIX2)

**API_DOMAIN, API_ACCOUNT_EMAIL, API_TOKEN**: SchoolMint API connection credentials to get the report. 
Suffix(es) must be defined in the variable API_SUFFIXES.
If there is only one endpoint, then you only need to include the connection credentials once with one API token.
If there are multiple endpoints, you can repeat these three env variables with a unique suffix.
(eg. API_DOMAIN_SUFFIX1, API_ACCOUNT_EMAIL_SUFFIX1, API_TOKEN_SUFFIX1, API_DOMAIN_SUFFIX2, API_ACCOUNT_EMAIL_SUFFIX2, API_TOKEN_SUFFIX2)
API token must be updated from year to year because each enrollment period has a unique report.

**CURRENT_SCHOOL_YEAR**: 4 digit enrollment school year (eg. 2021 during the 19-20 SY). 
This populates the SchoolYear4Digit column in the raw data tables. 
This must be updated when new reports are acquired for the next school year.

**GMAIL_USER, GMAIL_PWD, TO_NAME, TO_ADDRESS, BCC_ADDRESS**: 
Email credentials and addresses that job status notification emails will be sent to. 
BCC_ADDRESS is optional.

