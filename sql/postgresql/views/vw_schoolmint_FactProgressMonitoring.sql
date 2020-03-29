CREATE VIEW custom."vw_schoolmint_FactProgressMonitoring" AS
/*********************************************************************
Business Summary: Returns progress monitoring data for tableau data for SM Revamp from 3/1/2020

Comments:
2020-03-05  8:00am      AGonzalez        Created
*********************************************************************/

WITH CurrProgress AS (
    SELECT
          "Schoolyear4digit"
        , "SchoolName"
        , "SystemSchoolID"
        , "LkSchoolID"
        , "GradeLevel"
        , "Is_TransitionGrade"
        , "GoalType"
        , "GoalNum"
        , "GoalDate"
        , "GoalProgress"
        , "ReportDate"
        , "DistanceFromGoal_absolute"
        , "WeeksRemainingToGoal"
        , "MonthsRemainingToGoal"
        , "DistanceToGoal_Capped"
        , "GoalMet_Boolean"
        , "PercentGoalMet"
        , "UnitsPerWeek_ToGoal"
        , "UnitsPerMonth_ToGoal"
    FROM custom."vw_schoolmint_ProgressMonitoring"
    WHERE 1 = 1
        AND "Schoolyear4digit" = 2021 -- current year
        AND "GradeLevel" <> 'Total'
)

, LastDayMonth AS (
    SELECT
          fds."SchoolYear4DigitEnd"
        , fds."SchoolID"
        , fds."GradeLevel"
        , DATE_PART('month', fds."ReportDate") AS "ReportMonth"
        , MAX(fds."ReportDate") AS "ReportDate"
    FROM custom."schoolmint_FactDailyStatus" fds
    GROUP BY
          fds."SchoolYear4DigitEnd"
        , fds."SchoolID"
        , fds."GradeLevel"
        , DATE_PART('month', fds."ReportDate")
)

, FactRecord AS (
    SELECT
          fds."School"
        , fds."SchoolID"
        , fds."SchoolYear4DigitEnd"
        , fds."GradeLevel"
        , fds."StatusName"
        , fds."CountInStatus"
        , fds."ReportDate"
        , ROW_NUMBER() OVER (PARTITION BY fds."School", fds."SchoolID", fds."GradeLevel", fds."StatusName", fds."SchoolYear4DigitEnd", DATE_PART('month', fds."ReportDate") ORDER BY fds."ReportDate" DESC) AS "LastDateinMonth"
    FROM custom."schoolmint_FactDailyStatus" fds
    INNER JOIN LastDayMonth ld
        ON fds."SchoolYear4DigitEnd" = ld."SchoolYear4DigitEnd"
        AND fds."SchoolID" = ld."SchoolID"
        AND fds."GradeLevel" = ld."GradeLevel"
        AND fds."ReportDate" = ld."ReportDate"
    WHERE 1=1
        AND CAST(fds."SchoolYear4DigitEnd" AS INT) >= 2019 --pulling in last 3 years for sql performance purposes
        AND fds."StatusName" NOT IN ('Budget_NumTargetStudents', 'Expected_NumReturnStudents')
 )

SELECT
      fds."School"
    , fds."SchoolID"
    , fds."SchoolYear4DigitEnd"
    , fds."GradeLevel"
    , fds."StatusName"
    , fds."CountInStatus"
    , fds."ReportDate"
    , p."Is_TransitionGrade"
    , p."GoalType"
    , p."GoalNum"
    , p."GoalDate"
    , p."GoalProgress"
    , p."ReportDate" AS "Goalreportdate"
    , fds."LastDateinMonth"
    , p."DistanceFromGoal_absolute"
    , p."WeeksRemainingToGoal"
    , p."MonthsRemainingToGoal"
    , p."DistanceToGoal_Capped"
    , p."GoalMet_Boolean"
    , p."PercentGoalMet"
    , p."UnitsPerWeek_ToGoal"
    , p."UnitsPerMonth_ToGoal"
FROM Factrecord fds
LEFT JOIN Currprogress p
    ON CAST(fds."SchoolYear4DigitEnd" AS INT) = p."Schoolyear4digit"
    AND CAST(fds."SchoolID" AS INT) = p."SystemSchoolID"
    AND fds."GradeLevel" = p."GradeLevel"
    AND fds."ReportDate" = p."ReportDate"
WHERE 1 = 1
  AND CAST(fds."SchoolYear4DigitEnd" AS INT) >= 2019
  AND fds."LastDateinMonth" = 1
