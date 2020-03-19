CREATE VIEW [custom].vw_Schoolmint_AppStatusList AS
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
         , Systemschoolid   AS Schoolid
         , Schoolyear4digit AS Schoolyear4digitend
         , Grade_Level      AS Gradelevel
         , Goal_Type        AS Statusname
         , Goal_Num         AS Countinstatus
    FROM Custom.Schoolmint_Progressmonitoring
    WHERE 1 = 1
      AND Goal_Type IN ('Budget_NumTargetStudents', 'Expected_NumReturnStudents')

    UNION ALL
    SELECT                       Sc.School
         ,                       Sc.Schoolid AS Schoolid
         , Schoolyear4digitend = App.Schoolyear4digit
         , Gradelevel          = App.Grade_Applying_To
         , Statusname          = Sta.Statusname
         , Countinstatus       = count(*)
    FROM Custom.Schoolmint_Applicationdata_Raw App
         INNER JOIN Custom.Schoolmint_Applicationstatuses Sta
                        ON App.Application_Status = Sta.[Status]
         INNER JOIN Custom.Schoolmint_Schoolcodes Sc
                        ON Sc.Schoolmint_Schoolid = App.School_Applying_To OR Sc.School = App.School_Applying_To
    GROUP BY Sc.School, Sc.Schoolid
           , App.Schoolyear4digit
           , App.Grade_Applying_To
           , Sta.Statusname
)
SELECT
    stat.School
    ,stat.Schoolid
    , stat.Schoolyear4digitend
    , stat.Gradelevel
    , stat.Statusname
    , stat.Countinstatus
    ,bug.Goal_Num AS Budget_NumTargetStudents

FROM AppStatusLong stat
LEFT JOIN custom.Schoolmint_Progressmonitoring bug --Schoolmint_budgetandexpect_num bug
    ON stat.schoolid = bug.Systemschoolid
    AND stat.gradelevel = bug.Grade_Level
    AND stat.SchoolYear4DigitEnd = bug.Schoolyear4digit
    AND bug.Goal_Type = 'Budget_NumTargetStudents'
go

