Creating the SchoolMint Reports
*********************************

Reference: `SchoolMint Custom Reports table fields documentation <https://schoolmint6.zendesk.com/hc/en-us/articles/360030948152>`_

In the SchoolMint application, for each enrollment period that you want to report on, 
create a new report: 'Automated Application Data Raw XX-XX'

1. Select the enrollment period.
2. Click on the *Reports* menu.
3. Click on the *Custom Reports* menu option.
4. Click on the *Create New Report* button.

.. image:: _static/schoolmint_create_report1.png

5. Enter the report name.
6. For *Report Type*, select 'Application'.

.. image:: _static/schoolmint_create_report2.png

7. Skip to step 3 to add columns to your report. 
Use the toolbar on the left to search for fields. 
Drag and drop them into the report.

:download:`Download sample Automated Application Data Raw file <Automated_Application_Data_Raw_20-21-example.csv>` 

:download:`Download table field mappings for Automated Application Data Raw <SchoolMint Report Definitions - Automated Application Data Raw.csv>`

.. image:: _static/schoolmint_create_report3.png

8. Once you have created both reports, contact SchoolMint support to get the API keys for the reports.
9. You get one token per report, and these will go in your .env file.

Columns for Application Data Raw:

.. code-block:: text

    Application_ID
    SM_Student_ID
    Application_Student_Id
    SIS_Student_Id
    Students_First_Name
    Students_Last_Name
    School_Applying_to
    Grade_Applying_To
    Application_Status
    Waitlist_Number
    Application_Type
    Account_ID
    Account_Preferred_Language
    Current_Grade
    Enrollment_Period
    Submission_Date
    Submitted_By
    Offered_Date
    Accepted_Date
    Registration_Completed_Date
    Last_Update_Date
    Primary_Guardian_First_Name
    Primary_Guardian_Last_Name
    Primary_Guardian_Email
    Primary_Guardian_mobile_Phone
    Primary_Guardian_Home_Phone
    Primary_Guardian_Work_Phone
    Secondary_Guardian_First_Name
    Secondary_Guardian_Last_Name
    Secondary_Guardian_Email
    Secondary_Guardian_mobile_Phone
    Secondary_Guardian_Home_Phone
    Secondary_Guardian_Work_Phone
    Student_ID
    Student_First_Name
    Student_Middle_Name
    Student_Last_Name
    Student_Birth_Date
    Student_Gender
    Current_School
    Last_Status_Change
    StudentAddress_Street_1
    StudentAddress_Street_2
    StudentAddress_City
    StudentAddress_State
    StudentAddress_Zip
    StudentAddress_Coordinates
    District
    How_did_you_hear_about_us
    Student_Most_Used_Language
    Student_Home_Use_Language
    Home_Most_Used_Language
    Extra_Language_Support
    Individualized_Education_Program
    Homeless_Shelter
    NYC_Public_Housing
    Unaccompanied_Youth
    Failing_Grade_School
    Individualized_Education_Program_School
    Individualized_Education_Program_Date
    Special_Education_Services
    Health_Issues
    Free_Reduced_Lunch
    SNAP_TANF
    Priorities
    Ethnicities
    Primary_Guardian_Relation
    Secondary_Guardian_Relation
    Sibling_1_Name
    Sibling_1_Grade
    Sibling_1_School
    Sibling_1_DOB
    Sibling_2_Name
    Sibling_2_Grade
    Sibling_2_School
    Sibling_2_DOB
