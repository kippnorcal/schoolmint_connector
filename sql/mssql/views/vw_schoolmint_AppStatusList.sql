CREATE VIEW [custom].vw_schoolmint_AppStatusList AS
 /*********************************************************************
Business Summary: Used for Student Recruitment report.

Comments:
2016-08-01  8:00am      Matt         Created
10/21/2019              pkats        Update to fix missing statuses
2020-02-20  4:00pm      AGonzalez    Updated reference to target table in consolidation effort; Linting
2020-03-10  12:00pm     AGonzalez    Append "Budget_NumTargetStudents Column" so that we can deprecate vw_schoolmint_AppCombined_fix
*********************************************************************/

WITH AppStatusLong AS (
    SELECT School
         , Systemschoolid AS Schoolid
         , Schoolyear4digit AS Schoolyear4digitend
         , Grade_Level AS Gradelevel
         , Goal_Type AS Statusname
         , Goal_Num AS Countinstatus
    FROM custom.schoolmint_Progressmonitoring
    WHERE 1 = 1
      AND Goal_Type IN ('Budget_NumTargetStudents', 'Expected_NumReturnStudents')

    UNION ALL

    SELECT                       
           sc.School
         , sc.Schoolid AS Schoolid
         , app.Schoolyear4digit AS Schoolyear4digitend
         , app.Grade_Applying_To AS Gradelevel
         , sta.Statusname AS Statusname
         , COUNT(*) AS Countinstatus
    FROM custom.schoolmint_Applicationdata_Raw app
    INNER JOIN Custom.Schoolmint_Applicationstatuses sta
        ON app.Application_Status = sta.[Status]
    INNER JOIN custom.Schoolmint_Schoolcodes sc
        ON sc.Schoolmint_Schoolid = app.School_Applying_To 
        OR sc.School = app.School_Applying_To
    GROUP BY Sc.School, Sc.Schoolid
           , app.Schoolyear4digit
           , app.Grade_Applying_To
           , sta.Statusname
)

SELECT
      stat.School
    , stat.Schoolid
    , stat.Schoolyear4digitend
    , stat.Gradelevel
    , stat.Statusname
    , stat.Countinstatus
    , bug.Goal_Num AS Budget_NumTargetStudents
FROM AppStatusLong stat
LEFT JOIN custom.schoolmint_Progressmonitoring bug --Schoolmint_budgetandexpect_num bug
    ON stat.schoolid = bug.Systemschoolid
    AND stat.gradelevel = bug.Grade_Level
    AND stat.SchoolYear4DigitEnd = bug.Schoolyear4digit
    AND bug.Goal_Type = 'Budget_NumTargetStudents'
