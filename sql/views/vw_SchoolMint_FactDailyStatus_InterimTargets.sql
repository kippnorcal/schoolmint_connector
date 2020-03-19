CREATE VIEW [custom].[vw_Schoolmint_FactDailyStatus_InterimTargets] AS

/******************************************************************************************************
Business Summary: Retrieves counts in status by date

Comments:
2020-03-10      2:30pm      AGonzalez   Created to consolidate vw_schoolmint_FactDailyStatus_Application
                                        & _Registration
*********************************************************************************************************/

WITH DistinctReportItems AS (
    SELECT DISTINCT
	    School
	    , SchoolID
	    , SchoolYear4DigitEnd
	    , GradeLevel
	    , ReportDate
	FROM custom.SchoolMint_FactDailyStatus

), ApplicationGoalsSummary AS (
    SELECT
	        a.School
	      , a.SchoolID
	      , a.SchoolYear4DigitEnd
	      , a.GradeLevel
	      , StatusName = 'Application'
	      , ReportDate
	      , CountInStatus = sum(ISNULL(CountInStatus,0))
    FROM  custom.SchoolMint_FactDailyStatus  a
    INNER JOIN custom.schoolmint_ApplicationStatuses s
	    ON a.StatusName = s.StatusName
    WHERE 1=1
	    AND s.[Application] = 1 --ensures that statuses associated with application goals are included
	GROUP BY
	         a.School
	       , a.SchoolID
	       , a.SchoolYear4DigitEnd
	       , a.GradeLevel
	       , ReportDate

), RegistrationGoalsSummary AS (
    SELECT
            a.School,
            a.SchoolID,
            a.SchoolYear4DigitEnd,
            a.GradeLevel,
            StatusName = 'Registration',
            ReportDate,
            CountInStatus = SUM(ISNULL(CountInStatus,0))
        FROM custom.SchoolMint_FactDailyStatus a
        INNER JOIN custom.[schoolmint_ApplicationStatuses] s
            ON a.StatusName = s.StatusName
        WHERE 1=1
            AND s.Registration = 1 --ensures that statuses associated with registration goals are included
        GROUP BY
            a.School,
            a.SchoolID,
            a.SchoolYear4DigitEnd,
            a.GradeLevel,
            ReportDate

)


SELECT
       aa.School
     , aa.SchoolID
     , aa.SchoolYear4DigitEnd
     , aa.GradeLevel
     , StatusName = 'Application'
     , aa.ReportDate
     , CountInStatus = ISNULL(x.CountInStatus, 0)
FROM  DistinctReportItems aa
LEFT OUTER JOIN ApplicationGoalsSummary x
	ON aa.School = x.School
	AND aa.SchoolID = x.SchoolID
	AND aa.SchoolYear4DigitEnd = x.SchoolYear4DigitEnd
    AND aa.GradeLevel = x.GradeLevel
	AND aa.ReportDate = x.ReportDate

UNION ALL

SELECT
       aa.School
     , aa.SchoolID
     , aa.SchoolYear4DigitEnd
     , aa.GradeLevel
     , StatusName = 'Registration'
     , aa.ReportDate
     , CountInStatus = ISNULL(x.CountInStatus, 0)
FROM  DistinctReportItems aa
LEFT OUTER JOIN RegistrationGoalsSummary x
	ON aa.School = x.School
	AND aa.SchoolID = x.SchoolID
	AND aa.SchoolYear4DigitEnd = x.SchoolYear4DigitEnd
    AND aa.GradeLevel = x.GradeLevel
	AND aa.ReportDate = x.ReportDate





go

