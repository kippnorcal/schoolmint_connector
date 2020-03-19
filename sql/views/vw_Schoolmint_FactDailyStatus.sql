CREATE VIEW [custom].[vw_Schoolmint_FactDailyStatus] AS

/*********************************************************************
Business Summary: Retrieves counts in status by date

Comments:
2016-08-01  8:00am      Matt        Created
2020-02-13  10:00am     AGonzalez   Updated reference to target table in consolidation effort
2020-02-28  3:50PM      AGonzalez   Changed
*********************************************************************/
SELECT
    fds.ID
     , fds.School
     , fds.SchoolID
     , fds.SchoolYear4DigitEnd
     , fds.GradeLevel
     , fds.StatusName
     , fds.CountInStatus
     , fds.ReportDate
     , fds.Month_Boolean
     , fds.Sunday_Boolean
     , IIF (EOMONTH(fds.reportdate) = fds.reportdate, 1, 0) AS lastday_month_boolean
     , pm.Goal_Num AS Budget_NumTargetStudents

FROM custom.schoolmint_factdailystatus fds
JOIN custom.Schoolmint_Schoolcodes sc
    ON fds.Schoolid = sc.Schoolid
LEFT JOIN custom.Schoolmint_Progressmonitoring AS pm
    ON pm.Systemschoolid = fds.schoolid
    AND pm.Grade_Level = fds.gradelevel
    AND pm.Schoolyear4digit = fds.SchoolYear4DigitEnd
    AND pm.Goal_Type = 'Budget_NumTargetStudents'

go

