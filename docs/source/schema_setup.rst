Schema
*******

Schema Setup
#############

The following database objects are necessary to run the Python code. Refer to the sql folder for the DDL.

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

Stored Procedures
~~~~~~~~~~~~~~~~~~

* sproc_SchoolMint_Create_ChangeTracking_Entries
* sproc_SchoolMint_Create_FactDailyStatus
* sproc_SchoolMint_Index_PrepareTables
* sproc_SchoolMint_Index_PostProcess
* sproc_SchoolMint_Raw_PrepareTables
* sproc_SchoolMint_Raw_PostProcess


ERD
####

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
