CREATE VIEW custom."vw_schoolmint_ProgressMonitoring" AS
/****************************************************************************************************
Business Summary: Supports progress monitoring against interim goals for Student Recruitment by comparing
aggregated actuals to goal.

  SELECT * FROM custom.vw_Schoolmint_ProgressMonitoring

NOTES: Need to update this when we want to incorporate PS Enrollment Goals into this

Comments:
2017-09-01	    9:30AM		Matt            Created
2020-01-22      9:30AM      AGonzalez       Modified to join off of new infra. table that holds historical
                                            and current goal data (custom.vw_Schoolmint_ProgressMonitoring_Combined)
2020-01-28      12:23PM     AGonzalez       Modify to bring in new enrollment targets; added in lkSchoolId
2020-03-02      3:27PM      AGonzalez       Update view to point to vw_Schoolmint_FactDailyStatus_Registration for
                                            registration data
2020-03-10      2:45PM      AGonzalez       Refactor to point at vw_Schoolmint_FactDailyStatus_InterimTargets
****************************************************************************************************/

WITH ApplicationData AS (
    SELECT
          num."Schoolyear4digit"
        , num."School" AS "SchoolName"
        , num."SystemSchoolID"
        , num."LkSchoolID"
        , num."Grade_level" AS "GradeLevel"
        , num."Goal_type" AS "GoalType"
        , num."Goal_num" AS "GoalNum"
        , num."Goal_date" AS "GoalDate"
        , app."CountInStatus" AS "GoalProgress"
        , app."ReportDate" AS "ReportDate"
        , CAST(num."Goal_num" AS INT) - app."CountInStatus" AS "DistanceFromGoal_absolute"
        , ROW_NUMBER() OVER (PARTITION BY num."Schoolyear4digit", num."School", num."Grade_level", num."Goal_type", num."Goal_date" ORDER BY app."ReportDate" DESC) AS "RowNum"
    FROM custom."schoolmint_ProgressMonitoring" num
    INNER JOIN custom."vw_schoolmint_FactDailyStatus_InterimTargets" app
        ON (
              (num."School" = app."School" OR CAST(num."SystemSchoolID" AS VARCHAR) = app."SchoolID")
          AND num."Schoolyear4digit" = CAST(app."SchoolYear4DigitEnd" AS INT)
          AND num."Grade_level" = app."GradeLevel"
          AND num."Goal_date" >= app."ReportDate"
          AND num."Goal_type" LIKE 'app%'
          AND app."StatusName" = 'Application'
        )
)

, RegistrationData AS (
    SELECT
          num."Schoolyear4digit"
        , num."School" AS "SchoolName"
        , num."SystemSchoolID"
        , num."LkSchoolID"
        , num."Grade_level" AS "GradeLevel"
        , num."Goal_type" AS "GoalType"
        , num."Goal_num" AS "GoalNum"
        , num."Goal_date" AS "GoalDate"
        , app."CountInStatus" AS "GoalProgress"
        , app."ReportDate" AS "ReportDate"
        , CAST(num."Goal_num" AS INT) - app."CountInStatus" AS "DistanceFromGoal_absolute"
        , ROW_NUMBER() OVER (PARTITION BY num."Schoolyear4digit", num."School", num."Grade_level", num."Goal_type", num."Goal_date" ORDER BY app."ReportDate" DESC) AS "RowNum"
    FROM custom."schoolmint_ProgressMonitoring" num
    INNER JOIN custom."vw_schoolmint_FactDailyStatus_InterimTargets" app
        ON (
                (num."School" = app."School" OR CAST(num."SystemSchoolID" AS VARCHAR) = app."SchoolID")
            AND num."Schoolyear4digit" = CAST(app."SchoolYear4DigitEnd" AS INT)
            AND num."Grade_level" = app."GradeLevel"
            AND num."Goal_date" >= app."ReportDate"
            AND num."Goal_type" LIKE 'reg%'
            AND app."StatusName" = 'Registration'
        )
)

, PSEnerollmentData AS (
    SELECT
          num."Schoolyear4digit"
        , num."School" AS "SchoolName"
        , num."SystemSchoolID"
        , num."LkSchoolID"
        , num."Grade_level" AS "GradeLevel"
        , num."Goal_type" AS "GoalType"
        , num."Goal_num" AS "GoalNum"
        , num."Goal_date" AS "GoalDate"
        , app."CountInStatus" AS "GoalProgress"
        , app."ReportDate" AS "ReportDate"
        , CAST(num."Goal_num" AS INT) - app."CountInStatus" AS "DistanceFromGoal_absolute"
        , ROW_NUMBER() OVER (PARTITION BY num."Schoolyear4digit", num."School", num."Grade_level", num."Goal_type", num."Goal_date" ORDER BY app."ReportDate" DESC) AS "RowNum"
    FROM custom."schoolmint_ProgressMonitoring" num
    INNER JOIN custom."vw_schoolmint_FactDailyStatus" app
        ON (
              (num."School" = app."School" OR CAST(num."SystemSchoolID" AS VARCHAR) = app."SchoolID")
          AND num."Schoolyear4digit" = CAST(app."SchoolYear4DigitEnd" AS INT)
          AND num."Grade_level" = app."GradeLevel"
          AND num."Goal_date" >= app."ReportDate"
          AND num."Goal_type" IN ('Budget_NumTargetStudents', 'PS Prelim Enroll')
        )
)

, CombinedGoals AS (
    SELECT 
        app."Schoolyear4digit"
      , app."SchoolName"
      , app."SystemSchoolID"
      , app."LkSchoolID"
      , app."GradeLevel"
      , app."GoalType"
      , app."GoalNum"
      , app."GoalDate"
      , app."GoalProgress"
      , app."ReportDate"
      , app."DistanceFromGoal_absolute"
    FROM ApplicationData app
    WHERE "RowNum" = 1

    UNION ALL

    SELECT
        reg."Schoolyear4digit"
      , reg."SchoolName"
      , reg."SystemSchoolID"
      , reg."LkSchoolID"
      , reg."GradeLevel"
      , reg."GoalType"
      , reg."GoalNum"
      , reg."GoalDate"
      , reg."GoalProgress"
      , reg."ReportDate"
      , reg."DistanceFromGoal_absolute"
    FROM RegistrationData reg
    WHERE "RowNum" = 1

    UNION ALL

    SELECT
        ps."Schoolyear4digit"
      , ps."SchoolName"
      , ps."SystemSchoolID"
      , ps."LkSchoolID"
      , ps."GradeLevel"
      , ps."GoalType"
      , ps."GoalNum"
      , ps."GoalDate"
      , ps."GoalProgress"
      , ps."ReportDate"
      , ps."DistanceFromGoal_absolute"
    FROM PSEnerollmentData ps
    WHERE "RowNum" = 1
)

SELECT
      "Schoolyear4digit"
    , "SchoolName"
    , "SystemSchoolID"
    , "LkSchoolID"
    , "GradeLevel"
    , CASE
        WHEN "GradeLevel" IN ('TK', 'K', '6', '9') THEN 'Transition Grade'
        ELSE 'Non-Transition Grade'
        END AS "Is_TransitionGrade"
    , "GoalType"
    , "GoalNum"
    , "GoalDate"
    , "GoalProgress"
    , "ReportDate"
    , "DistanceFromGoal_absolute"
    , TRUNC(DATE_PART('day', "GoalDate" - NOW())/7) AS "WeeksRemainingToGoal"
    , (DATE_PART('year', "GoalDate") - DATE_PART('year', NOW())) * 12 + (DATE_PART('month', "GoalDate") - DATE_PART('month', NOW())) AS "MonthsRemainingToGoal"
    , CASE
        WHEN "DistanceFromGoal_absolute" <= 0 THEN 0
        ELSE "DistanceFromGoal_absolute"
        END AS "DistanceToGoal_Capped"
    , CASE
        WHEN "DistanceFromGoal_absolute" <= 0 THEN 1
        ELSE 0
        END AS "GoalMet_Boolean"
    , CASE
        WHEN CAST("GoalNum" AS INT) <> 0 THEN "GoalProgress" / CAST("GoalNum" AS INT)
        ELSE NULL
        END AS "PercentGoalMet"
    , CASE
        WHEN "DistanceFromGoal_absolute" <= 0 THEN 0
        ELSE CASE
            WHEN "DistanceFromGoal_absolute" / TRUNC(DATE_PART('day', "GoalDate" - NOW())/7) = 0 THEN 1
            ELSE "DistanceFromGoal_absolute" / TRUNC(DATE_PART('day', "GoalDate" - NOW())/7)
            END
        END AS "UnitsPerWeek_ToGoal"
    , CASE
        WHEN "DistanceFromGoal_absolute" <= 0 THEN 0
        ELSE CASE
            WHEN "DistanceFromGoal_absolute" / ((DATE_PART('year', "GoalDate") - DATE_PART('year', NOW())) * 12 + (DATE_PART('month', "GoalDate") - DATE_PART('month', NOW()))) = 0 THEN 1
            ELSE "DistanceFromGoal_absolute" / ((DATE_PART('year', "GoalDate") - DATE_PART('year', NOW())) * 12 + (DATE_PART('month', "GoalDate") - DATE_PART('month', NOW())))
            END
        END AS "UnitsPerMonth_ToGoal"
FROM CombinedGoals
