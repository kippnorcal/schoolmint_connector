CREATE VIEW [custom].[vw_SchoolMint_ProgressMonitoring] AS
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
        num.SchoolYear4Digit
        , num.School AS SchoolName
        , num.SystemSchoolID
        , num.LkSchoolID
        , num.Grade_Level AS GradeLevel
        , num.Goal_Type AS GoalType
        , num.Goal_Num AS GoalNum
        , num.Goal_Date AS GoalDate
        , app.CountInStatus AS GoalProgress
        , app.reportDate AS ReportDate
        , num.Goal_Num - app.CountInStatus AS DistanceFromGoal_absolute
        , Row_Number() OVER (PARTITION BY num.SchoolYear4Digit, num.School, num.Grade_Level, num.Goal_Type, num.Goal_Date
                            ORDER BY app.reportdate desc) AS RowNum
    FROM custom.Schoolmint_ProgressMonitoring num
    INNER JOIN custom.Vw_Schoolmint_Factdailystatus_Interimtargets app
        ON ((num.School = app.School OR num.SystemSchoolID = app.SchoolID)
        AND num.Schoolyear4digit = app.SchoolYear4DigitEnd
        AND num.Grade_Level = app.GradeLevel
        AND num.Goal_Date >= app.ReportDate
        AND num.Goal_Type LIKE 'app%'
        AND app.Statusname = 'Application'
    )
), RegistrationData AS (
    SELECT
          num.SchoolYear4Digit
        , num.School AS SchoolName
        , num.SystemSchoolID
        , num.LkSchoolID
        , num.Grade_Level AS GradeLevel
        , num.Goal_Type AS GoalType
        , num.Goal_Num AS GoalNum
        , num.Goal_Date AS GoalDate
        , app.CountInStatus AS GoalProgress
        , app.reportDate AS ReportDate
        , num.Goal_Num - app.CountInStatus AS DistanceFromGoal_absolute
        , Row_Number() OVER (PARTITION BY num.SchoolYear4Digit, num.School, num.Grade_Level, num.Goal_Type, num.Goal_Date
                            ORDER BY app.reportdate desc) AS RowNum
    FROM custom.Schoolmint_ProgressMonitoring num
    INNER JOIN custom.Vw_Schoolmint_Factdailystatus_Interimtargets app
        ON (
            (num.School = app.School OR num.SystemSchoolID = app.SchoolID)
            AND num.Schoolyear4digit = app.SchoolYear4DigitEnd
            AND num.Grade_Level = app.GradeLevel
            AND num.Goal_Date >= app.ReportDate
            AND num.Goal_Type LIKE 'reg%'
            AND app.Statusname = 'Registration'
        )
), PSEnerollmentData AS (
    SELECT
         num.SchoolYear4Digit
        , num.School AS SchoolName
        , num.SystemSchoolID
        , num.LkSchoolID
        , num.Grade_Level AS GradeLevel
        , num.Goal_Type AS GoalType
        , num.Goal_Num AS GoalNum
        , num.Goal_Date AS GoalDate
        , app.CountInStatus AS GoalProgress
        , app.reportDate AS ReportDate
        , num.Goal_Num - app.CountInStatus AS DistanceFromGoal_absolute
        , Row_Number() OVER (PARTITION BY num.SchoolYear4Digit, num.School, num.Grade_Level, num.Goal_Type, num.Goal_Date
                            ORDER BY app.reportdate desc) AS RowNum
    FROM custom.Schoolmint_ProgressMonitoring num
    INNER JOIN custom.vw_SchoolMint_FactDailyStatus app
        ON ((num.School = app.School OR num.SystemSchoolID = app.SchoolID)
        AND num.Schoolyear4digit = app.SchoolYear4DigitEnd
        AND num.Grade_Level = app.GradeLevel
        AND num.Goal_Date >= app.ReportDate
        AND num.Goal_Type IN ('Budget_NumTargetStudents', 'PS Prelim Enroll')
        )
), CombinedGoals AS (
    SELECT app.SchoolYear4Digit
         , app.SchoolName
         , app.SystemSchoolID
         , app.LkSchoolID
         , app.GradeLevel
         , app.GoalType
         , app.GoalNum
         , app.GoalDate
         , app.GoalProgress
         , app.ReportDate
         , app.DistanceFromGoal_Absolute
    FROM ApplicationData app
    WHERE 1 = 1
      AND RowNum = 1

    UNION ALL

    SELECT
           reg.SchoolYear4Digit
         , reg.SchoolName
         , reg.SystemSchoolID
         , reg.LkSchoolID
         , reg.GradeLevel
         , reg.GoalType
         , reg.GoalNum
         , reg.GoalDate
         , reg.GoalProgress
         , reg.ReportDate
         , reg.DistanceFromGoal_absolute

    FROM RegistrationData reg
    WHERE 1 = 1
      AND RowNum = 1

    UNION ALL

    SELECT
           ps.SchoolYear4Digit
         , ps.SchoolName
         , ps.SystemSchoolID
         , ps.LkSchoolID
         , ps.GradeLevel
         , ps.GoalType
         , ps.GoalNum
         , ps.GoalDate
         , ps.GoalProgress
         , ps.ReportDate
         , ps.DistanceFromGoal_absolute

    FROM PSEnerollmentData ps
    WHERE 1 = 1
      AND RowNum = 1
)
   SELECT
        SchoolYear4Digit
        , SchoolName
        , SystemSchoolID
        , LkSchoolID
        , GradeLevel
        , IIF(GradeLevel IN ('TK', 'K', '6', '9'), 'Transition Grade', 'Non-Transition Grade') Is_TransitionGrade
        , GoalType
        , GoalNum
        , GoalDate
        , GoalProgress
        , ReportDate
        , DistanceFromGoal_absolute
        , DATEDIFF(WEEK, GETDATE(), GoalDate) AS WeeksRemainingToGoal
        , DATEDIFF(MONTH, GETDATE(), GoalDate) AS MonthsRemainingToGoal
        , IIF(DistanceFromGoal_absolute <= 0, 0, DistanceFromGoal_absolute) AS DistanceToGoal_Capped
        , IIF(DistanceFromGoal_absolute <= 0, 1, 0) GoalMet_Boolean
        , IIF(GoalNum <> 0, GoalProgress / GoalNum, NULL) AS PercentGoalMet
        , IIF(DistanceFromGoal_absolute <= 0, 0,
            IIF(DistanceFromGoal_absolute/ DATEDIFF(WEEK, GETDATE(), GoalDate) = 0, 1,DistanceFromGoal_absolute/ DATEDIFF(WEEK, GETDATE(), GoalDate))) AS UnitsPerWeek_ToGoal
        , IIF(DistanceFromGoal_absolute <= 0, 0,
            IIF(DistanceFromGoal_absolute / DATEDIFF(MONTH, GETDATE(), GoalDate)=0, 1,DistanceFromGoal_absolute / DATEDIFF(MONTH, GETDATE(), GoalDate)) ) AS UnitsPerMonth_ToGoal

FROM CombinedGoals

