README
********

Pre-requisites
===============
TODO SchoolMint reports: Application Data, Application Data Index

Dependencies
=============

* Python3.7
* `Pipenv <https://pipenv.readthedocs.io/en/latest/>`_
* `Docker <https://www.docker.com/>`_
    * Install for `Mac <https://docs.docker.com/docker-for-mac/install/>`_
    * Install for `Linux <https://docs.docker.com/install/linux/docker-ce/debian/>`_
    * Install for `Windows <https://docs.docker.com/docker-for-windows/install/>`_


Environment setup
==================

Clone the repo
---------------
.. code-block:: bash

    git clone https://github.com/kipp-bayarea/schoolmint_connector.git


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

    FTP_HOSTNAME=
    FTP_USERNAME=
    FTP_PWD=
    ARCHIVE_MAX_DAYS=

    API_DOMAIN=
    API_ACCOUNT_EMAIL=
    API_TOKEN_DATA=
    API_TOKEN_DATA_INDEX=
    CURRENT_SCHOOL_YEAR=

    GMAIL_USER=
    GMAIL_PWD=
    SLACK_EMAIL=
    TO_NAME=
    TO_ADDRESS=
    BCC_ADDRESS=

**DELETE_LOCAL_FILES**: Keep downloaded files on the local machine or not. 
This setting doesn't matter when using Docker. Suggested: True.

**DB_SERVER, DB, DB_USER, DB_PWD, DB_SCHEMA**: Variables used by 
`sqlsorcery <https://sqlsorcery.readthedocs.io/en/latest/cookbook/environment.html>`_.

**DB_RAW_TABLE**: Name of the database table that the Application Data 
file data goes into.

**DB_RAW_INDEX_TABLE**: Name of the database table that the Application 
Data Index file data goes into.

**SPROC_RAW_PREP**: Name of the pre-processing sproc that backs up and 
truncates the Application Data table.

**SPROC_RAW_POST**: Name of the post-processing sproc that sets the 
SchoolYear4Digit column and restores from backup if the Application Data table is empty.

**SPROC_RAW_INDEX_PREP**: Name of the pre-processing sproc that backs up 
and truncates the Application Data Index table.

**SPROC_RAW_INDEX_POST**: Name of the post-processing sproc that sets the 
SchoolYear4Digit column and restores from backup if the Application Data 
Index table is empty.

**SPROC_CHANGE_TRACK**: Name of the sproc that generates the Change History 
records.

**SPROC_FACT_DAILY**: Name of the sproc that generates the Fact Daily Status 
records.

**FTP_HOSTNAME, FTP_USERNAME, FTP_PWD**: FTP server connection variables.

**ARCHIVE_MAX_DAYS**: Files older than this number of days will be deleted from the FTP.

**API_DOMAIN, API_ACCOUNT_EMAIL**: SchoolMint API connection credentials.

**API_TOKEN_DATA**: API Token for the Application Data report. Provided by SchoolMint. 
This token must be updated from year to year because each enrollment period has a unique report.

**API_TOKEN_DATA_INDEX**: API Token for the Application Data Index report. Provided by SchoolMint. 
This token must be updated from year to year because each enrollment period has a unique report.

**CURRENT_SCHOOL_YEAR**: 4 digit enrollment school year (eg. 2021 during the 19-20 SY). 
This populates the SchoolYear4Digit column in the raw data tables. 
This must be updated when new reports are acquired for the next school year.

**GMAIL_USER, GMAIL_PWD, TO_NAME, TO_ADDRESS, BCC_ADDRESS**: 
Email credentials and addresses that job status notification emails will be sent to. 
BCC_ADDRESS is optional.


Run the job
================

Build docker image
-------------------
.. code-block:: bash

    docker build -t schoolmint .


Run
----
.. code-block:: bash

    docker run -it schoolmint


Run with volume mapping
------------------------
.. code-block:: bash

    docker run -it -v ${PWD}:/code/ schoolmint
