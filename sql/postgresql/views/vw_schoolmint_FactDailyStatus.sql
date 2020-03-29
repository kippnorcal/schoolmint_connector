CREATE VIEW custom."vw_schoolmint_FactDailyStatus" AS

/*********************************************************************
Business Summary: Retrieves counts in status by date

Comments:
2016-08-01  8:00am      Matt        Created
2020-02-13  10:00am     AGonzalez   Updated reference to target table in consolidation effort
2020-02-28  3:50PM      AGonzalez   Changed
*********************************************************************/
SELECT
      fds."ID"
    , fds."School"
    , fds."SchoolID"
    , fds."SchoolYear4DigitEnd"
    , fds."GradeLevel"
    , fds."StatusName"
    , fds."CountInStatus"
    , fds."ReportDate"
    , fds."Month_Boolean"
    , fds."Sunday_Boolean"
    , CASE
        WHEN DATE_TRUNC('month', fds."ReportDate") + interval '1 month' - interval '1 day' = fds."ReportDate" THEN 1
        ELSE 0
        END AS lastday_month_boolean
    , pm."Goal_num" AS Budget_NumTargetStudents
FROM custom."schoolmint_FactDailyStatus" fds
JOIN custom."schoolmint_SchoolCodes" sc
    ON fds."SchoolID" = sc."SchoolID"
LEFT JOIN custom."schoolmint_ProgressMonitoring" AS pm
    ON CAST(pm."SystemSchoolID" AS VARCHAR) = fds."SchoolID"
    AND pm."Grade_level" = fds."GradeLevel"
    AND pm."Schoolyear4digit" = CAST(fds."SchoolYear4DigitEnd" AS INT)
    AND pm."Goal_type" = 'Budget_NumTargetStudents'
