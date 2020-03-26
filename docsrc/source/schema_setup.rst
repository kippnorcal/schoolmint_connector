Schema
*******

Schema Setup
#############

Automatic Setup
~~~~~~~~~~~~~~~~

Navigate to sql/mssql, and set up a locally hosted MSSQL database in Docker for development:

.. code-block:: bash

    $ docker-compose up -d

Connect to the database in your favorite database IDE, and create your Database and Schema. Update your .env file to match.

Navigate to the main project folder, and create the database objects automatically in the database:

.. code-block:: bash

    $ docker build -t schoolmint .
    $ docker run -it --network host schoolmint --mssql


After the code is finished running, you should have the following tables, views, and sprocs:

Tables
~~~~~~~

* schoolmint_ApplicationData_changehistory
* schoolmint_ApplicationData_raw
* schoolmint_ApplicationData_raw_backup
* schoolmint_ApplicationDataIndex_raw
* schoolmint_ApplicationDataIndex_raw_backup
* schoolmint_ApplicationStatuses
* SchoolMint_FactDailyStatus
* SchoolMint_lk_Enrollment
* Schoolmint_Progressmonitoring
* SchoolMint_SchoolCodes

Views
~~~~~~
* vw_SchoolMint_AppStatusList
* vw_SchoolMint_FactDailyStatus_InterimTargets
* vw_Schoolmint_FactDailyStatus
* vw_Schoolmint_FactProgressMonitoring
* vw_Schoolmint_Index_Demographics
* vw_SchoolMint_ProgressMonitoring

Stored Procedures
~~~~~~~~~~~~~~~~~~

* sproc_SchoolMint_Create_ChangeTracking_Entries
* sproc_SchoolMint_Create_FactDailyStatus
* sproc_SchoolMint_Index_PrepareTables
* sproc_SchoolMint_Index_PostProcess
* sproc_SchoolMint_Raw_PrepareTables
* sproc_SchoolMint_Raw_PostProcess

Lookup Tables
##############

The following lookup tables need to be populated:

* **SchoolMint_lk_Enrollment**: Load the data from sql/data/lk_enrollment.csv into this table.
* **Schoolmint_Progressmonitoring**: Refer to the template (provided separately).
* **SchoolMint_SchoolCodes**: Load the data from sql/data/application_statuses.csv into this table.

Final ERD
##########

`View ERD on LucidChart <https://www.lucidchart.com/invitations/accept/47fd9583-9736-4174-983a-ec526ec2851c>`_


Tables & Processes
####################

(click image to view larger)

.. image:: _static/schoolmint_schema_tables.png
    :target: _static/schoolmint_schema_tables.png


Views
#######

(click image to view larger)

.. image:: _static/schoolmint_schema_views.png
    :target: _static/schoolmint_schema_views.png
