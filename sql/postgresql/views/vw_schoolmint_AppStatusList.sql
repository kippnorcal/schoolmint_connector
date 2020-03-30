CREATE VIEW custom."vw_schoolmint_AppStatusList" AS
 /*********************************************************************
Business Summary: Used for Student Recruitment report.

Comments:
2016-08-01  8:00am      Matt         Created
10/21/2019              pkats        Update to fix missing statuses
2020-02-20  4:00pm      AGonzalez    Updated reference to target table in consolidation effort; Linting
2020-03-10  12:00pm     AGonzalez    Append "Budget_NumTargetStudents Column" so that we can deprecate vw_schoolmint_AppCombined_fix
*********************************************************************/

WITH AppStatusLong AS (
    SELECT "School"
         , CAST("SystemSchoolID" AS VARCHAR) AS "Schoolid"
         , "Schoolyear4digit" AS "Schoolyear4digitend"
         , "Grade_level" AS "Gradelevel"
         , "Goal_type" AS "Statusname"
         , CAST("Goal_num" AS BIGINT) AS "Countinstatus"
    FROM custom."schoolmint_ProgressMonitoring"
    WHERE 1 = 1
      AND "Goal_type" IN ('Budget_NumTargetStudents', 'Expected_NumReturnStudents')

    UNION ALL

    SELECT                       
           sc."School"
         , sc."SchoolID" AS "Schoolid"
         , app."SchoolYear4Digit" AS "Schoolyear4digitend"
         , app."Grade_Applying_To" AS "Gradelevel"
         , sta."StatusName" AS "Statusname"
         , COUNT(*) AS "Countinstatus"
    FROM custom."schoolmint_ApplicationData_raw" app
    INNER JOIN custom."schoolmint_ApplicationStatuses" sta
        ON app."Application_Status" = sta."Status"
    INNER JOIN custom."schoolmint_SchoolCodes" sc
        ON sc."SchoolMint_SchoolID" = app."School_Applying_to"
        OR sc."School" = app."School_Applying_to"
    GROUP BY sc."School"
           , sc."SchoolID"
           , app."SchoolYear4Digit"
           , app."Grade_Applying_To"
           , sta."StatusName"
)

SELECT
      stat."School"
    , stat."Schoolid"
    , stat."Schoolyear4digitend"
    , stat."Gradelevel"
    , stat."Statusname"
    , stat."Countinstatus"
    , bug."Goal_num" AS "Budget_NumTargetStudents"
FROM AppStatusLong stat
LEFT JOIN custom."schoolmint_ProgressMonitoring" bug
    ON stat."Schoolid" = CAST(bug."SystemSchoolID" AS VARCHAR)
    AND stat."Gradelevel" = bug."Grade_level"
    AND stat."Schoolyear4digitend" = bug."Schoolyear4digit"
    AND bug."Goal_type" = 'Budget_NumTargetStudents'
