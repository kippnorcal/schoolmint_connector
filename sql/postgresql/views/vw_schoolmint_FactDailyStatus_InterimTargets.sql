CREATE VIEW custom."vw_schoolmint_FactDailyStatus_InterimTargets" AS

/******************************************************************************************************
Business Summary: Retrieves counts in status by date

Comments:
2020-03-10      2:30pm      AGonzalez   Created to consolidate vw_schoolmint_FactDailyStatus_Application
                                        & _Registration
*********************************************************************************************************/

WITH DistinctReportItems AS (
    SELECT DISTINCT
	      "School"
	    , "SchoolID"
	    , "SchoolYear4DigitEnd"
	    , "GradeLevel"
	    , "ReportDate"
	FROM custom."schoolmint_FactDailyStatus"
)

, ApplicationGoalsSummary AS (
    SELECT
          a."School"
        , a."SchoolID"
        , a."SchoolYear4DigitEnd"
        , a."GradeLevel"
        , 'Application' AS "StatusName"
        , a."ReportDate"
        , SUM(COALESCE("CountInStatus",0)) AS "CountInStatus"
    FROM custom."schoolmint_FactDailyStatus"  a
    INNER JOIN custom."schoolmint_ApplicationStatuses" s
	    ON a."StatusName" = s."StatusName"
    WHERE 1=1
	    AND s."Application" = true --ensures that statuses associated with application goals are included
	GROUP BY
          a."School"
        , a."SchoolID"
        , a."SchoolYear4DigitEnd"
        , a."GradeLevel"
        , a."ReportDate"
)

, RegistrationGoalsSummary AS (
    SELECT
          a."School"
        , a."SchoolID"
        , a."SchoolYear4DigitEnd"
        , a."GradeLevel"
        , 'Registration' AS "StatusName"
        , a."ReportDate"
        , SUM(COALESCE("CountInStatus",0)) AS "CountInStatus"
    FROM custom."schoolmint_FactDailyStatus" a
    INNER JOIN custom."schoolmint_ApplicationStatuses" s
        ON a."StatusName" = s."StatusName"
    WHERE 1=1
        AND s."Registration" = true --ensures that statuses associated with registration goals are included
    GROUP BY
          a."School"
        , a."SchoolID"
        , a."SchoolYear4DigitEnd"
        , a."GradeLevel"
        , a."ReportDate"

)


SELECT
       aa."School"
     , aa."SchoolID"
     , aa."SchoolYear4DigitEnd"
     , aa."GradeLevel"
     , 'Application' AS "StatusName"
     , aa."ReportDate"
     , COALESCE(x."CountInStatus", 0) AS "CountInStatus"
FROM  DistinctReportItems aa
LEFT OUTER JOIN ApplicationGoalsSummary x
	ON aa."School" = x."School"
	AND aa."SchoolID" = x."SchoolID"
	AND aa."SchoolYear4DigitEnd" = x."SchoolYear4DigitEnd"
    AND aa."GradeLevel" = x."GradeLevel"
	AND aa."ReportDate" = x."ReportDate"

UNION ALL

SELECT
       aa."School"
     , aa."SchoolID"
     , aa."SchoolYear4DigitEnd"
     , aa."GradeLevel"
     , 'Registration' AS "StatusName"
     , aa."ReportDate"
     , COALESCE(x."CountInStatus", 0) AS "CountInStatus"
FROM  DistinctReportItems aa
LEFT OUTER JOIN RegistrationGoalsSummary x
	ON aa."School" = x."School"
	AND aa."SchoolID" = x."SchoolID"
	AND aa."SchoolYear4DigitEnd" = x."SchoolYear4DigitEnd"
    AND aa."GradeLevel" = x."GradeLevel"
	AND aa."ReportDate" = x."ReportDate"
