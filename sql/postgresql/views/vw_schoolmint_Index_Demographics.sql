CREATE VIEW custom."vw_schoolmint_Index_Demographics" AS

/*********************************************************************
Business Summary: Used for Student Recruitment report.

Comments:
2016-08-01  8:00am      Matt         Created
2020-03-10  12:45pm     AGonzalez    Refactored
*********************************************************************/

SELECT
    raw."Account_ID" AS "account_id"
    , raw."Student_ID" AS "student_id"
    , raw."Application_ID" AS "application_id"
    , raw."Students_First_Name" AS "first_name"
    , NULL AS "middle_name" -- does not exist in raw table
    , raw."Students_Last_Name" AS "last_name"
    , raw."Student_Birth_Date" AS "birth_date"
    , raw."Student_Gender" AS "gender"
    , raw."Primary_Guardian_Email" AS "email"
    , raw."Primary_Guardian_First_Name" AS "guardian_first_name"
    , raw."Primary_Guardian_Last_Name" AS "guardian_last_name"
    , raw."Primary_Guardian_mobile_Phone" AS "phone_number"
    , raw."Primary_Guardian_Home_Phone" AS "home_phone_number"
    , raw."StudentAddress_Street_1" AS "street1"
    , raw."StudentAddress_Street_2" AS "street2"
    , raw."StudentAddress_Zip" AS "zipcode"
    , raw."StudentAddress_State" AS "state"
    , raw."StudentAddress_City" AS "city"
    , NULL AS "lives_with" -- does not exist in raw table
    , raw."Application_Type" AS "application_type"
    , NULL AS "created_by" -- does not exist in raw table
    , raw."Submission_Date" AS "submission_date"
    , raw."Application_Status" AS "status"
    , raw."Waitlist_Number" AS "waitlist_number"
    , NULL AS "app_status_timestamp" -- does not exist in raw table
    , raw."Offered_Date" AS "app_offered_date"
    , raw."Last_Update_Date" AS "last_updated"
    , raw."Current_Grade" AS "current_grade_level"
    , raw."Grade_Applying_To" AS "grade_name"
    , raw."School_Applying_to" AS "school_name"
    , raw."Current_School" AS "current_school_name"
    , NULL AS "priorities" -- duplicated in later column
    , raw."District" AS "district_name"
    , NULL AS "school_group" -- does not exist in raw table
    , raw."Account_Preferred_Language" AS "preferred_language"
    , raw."SchoolYear4Digit" AS "SchoolYear4Digit"
    , raw."enrollment_period"
    , raw."last_update_date"
    , raw."last_status_change"
    , raw."studentaddress_coordinates"
    , raw."how_did_you_hear_about_us"
    , raw."free_reduced_lunch"
    , raw."priorities" AS "priorities_custom"
    , stat."statusname"
    , stat."statusDescription"
    , stat."statusgroupname"
	, sc."School" AS "SchoolName_normalized"
	, sc."SchoolID" AS "SchoolID_normalized"
FROM custom."schoolmint_ApplicationData_raw" raw
INNER JOIN custom."schoolmint_ApplicationStatuses" stat
    ON stat."Status" = ind."status"
INNER JOIN custom."schoolmint_SchoolCodes" sc
	ON (ind."school_name" = sc."School" OR sc."SchoolMint_SchoolID" = ind."school_name")
