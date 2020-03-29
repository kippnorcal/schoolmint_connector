CREATE VIEW custom."vw_schoolmint_Index_Demographics" AS

/*********************************************************************
Business Summary: Used for Student Recruitment report.

Comments:
2016-08-01  8:00am      Matt         Created
2020-03-10  12:45pm     AGonzalez    Refactored
*********************************************************************/

SELECT
      ind."applicant_id"
    , ind."account_id"
    , ind."student_id"
    , ind."application_id"
    , ind."first_name"
    , ind."middle_name"
    , ind."last_name"
    , ind."birth_date"
    , ind."gender"
    , ind."email"
    , ind."guardian_first_name"
    , ind."guardian_last_name"
    , ind."phone_number"
    , ind."home_phone_number"
    , ind."street1"
    , ind."street2"
    , ind."zipcode"
    , ind."state"
    , ind."city"
    , ind."lives_with"
    , ind."application_type"
    , ind."created_by"
    , ind."submission_date"
    , ind."status"
    , ind."waitlist_number"
    , ind."app_status_timestamp"
    , ind."app_offered_date"
    , ind."last_updated"
    , ind."current_grade_level"
    , ind."grade_name"
    , ind."school_name"
    , ind."current_school_name"
    , ind."priorities"
    , ind."district_name"
    , ind."school_group"
    , ind."preferred_language"
    , ind."SchoolYear4Digit"
    , sel."Enrollment_Period"
    , sel."Last_Update_Date"
    , sel."Last_Status_Change"
    , sel."StudentAddress_Coordinates"
    , sel."How_did_you_hear_about_us"
    , sel."Free_Reduced_Lunch"
    , sel."Priorities" AS "priorities_custom"
    , stat."StatusName"
    , stat."StatusDescription"
    , stat."StatusGroupName"
    , sch."School" AS "SchoolName_normalized"
    , sch."SchoolID" AS "SchoolID_normalized"
FROM custom."schoolmint_ApplicationDataIndex_raw" ind
INNER JOIN custom."schoolmint_ApplicationData_raw" sel
    ON ind."application_id" = sel."Application_ID"
    AND ind."student_id" = sel."SM_Student_ID"
INNER JOIN custom."schoolmint_ApplicationStatuses" stat
    ON stat."Status" = ind."status"
INNER JOIN custom."schoolmint_SchoolCodes" sch
	ON (ind."school_name" = sch."School" OR sch."SchoolMint_SchoolID" = ind."school_name")
