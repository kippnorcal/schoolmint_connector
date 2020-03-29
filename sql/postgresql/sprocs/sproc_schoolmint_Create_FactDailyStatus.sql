CREATE PROCEDURE custom."sproc_schoolmint_Create_FactDailyStatus"()
LANGUAGE plpgsql
AS $$
BEGIN

/***************************************************************************
Name: custom.sproc_SchoolMint_Create_FactDailyStatus

Business Purpose: Generate fact daily status table.
Called daily by SchoolMint python code.
Used by student recruitment reports.

Comments:
2019-10-08	3:30PM		pkats		Initial sproc
2020-03-11  12:00PM     agonz       Refactor
2020-03-11  12:00PM     sxiong      Add update statement to retroactively update historical budget/enrollment goals.
***************************************************************************/

/* So That Report is Re-Runnable */
DELETE
FROM custom."schoolmint_FactDailyStatus"
WHERE "ReportDate" = CAST(NOW() AS DATE);

WITH current_schoolyear AS(
    SELECT
        MAX("SchoolYear4Digit") AS "SchoolYear4Digit"
    FROM custom."schoolmint_ApplicationData_raw"
)

,apps AS (
	SELECT
	      a."SchoolYear4Digit"
	    , a."School_Applying_to"
	    , sch."SchoolID"
	    , sch."School" AS "SchoolName"
        , a."Application_ID"
	    , a."Application_Student_Id"
	    , a."Grade_Applying_To"
	    , a."Application_Status"
	    , b."StatusName"
	    , lk."Enrollment_Period_str"
	FROM custom."schoolmint_ApplicationData_raw" a
	LEFT JOIN custom."schoolmint_ApplicationStatuses" b
	    ON a."Application_Status" = b."Status"
	LEFT JOIN custom."schoolmint_lk_Enrollment" lk --AG: is this needed??
	    ON a."Enrollment_Period" = lk."Enrollment_Period_id"
	LEFT JOIN custom."schoolmint_SchoolCodes" sch
        ON a."School_Applying_to" = sch."SchoolMint_SchoolID"
	WHERE 1=1
	    AND a."SchoolYear4Digit" = (SELECT SchoolYear4Digit FROM current_schoolyear)
	)

INSERT INTO custom."schoolmint_FactDailyStatus" (
	  "School"
	, "SchoolID"
	, "SchoolYear4DigitEnd"
	, "GradeLevel"
	, "StatusName"
	, "CountInStatus"
	, "ReportDate"
	, "Month_Boolean"
	, "Sunday_Boolean"
)

SELECT
      "School"
	, "SystemSchoolID"
	, "Schoolyear4digit"
	, "Grade_level"
	, 'Budget_NumTargetStudents' AS "STATUS"
	, "Goal_num" AS "CountInStatus"
	, CAST(NOW() AS DATE) AS "ReportDate"
    -- These CASE were added here because the Table def can't include calculated columns in Postgres
    , CASE
        WHEN DATE_PART('day', CAST(NOW() AS DATE)) = 1 THEN 1
        ELSE 0
        END AS "Month_Boolean"
    , CASE
        WHEN DATE_PART('weekday', CAST(NOW() AS DATE)) = 1 THEN 1
        ELSE 0
        END AS "Sunday_Boolean"
FROM custom."schoolmint_ProgressMonitoring"
WHERE 1=1
    AND "Schoolyear4digit" = (SELECT "SchoolYear4Digit" FROM current_schoolyear)
    AND "Goal_type" = 'Budget_NumTargetStudents'

UNION

SELECT
      "School"
	, "SystemSchoolID"
	, "Schoolyear4digit"
	, "Grade_level"
	, 'Expected_NumReturnStudents' AS "STATUS"
	, "Goal_num" AS "CountInStatus"
	, CAST(NOW() AS DATE)
    , CASE
        WHEN DATE_PART('day', CAST(NOW() AS DATE)) = 1 THEN 1
        ELSE 0
        END AS "Month_Boolean"
    , CASE
        WHEN DATE_PART('weekday', CAST(NOW() AS DATE)) = 1 THEN 1
        ELSE 0
        END AS "Sunday_Boolean"
FROM custom."schoolmint_ProgressMonitoring"
WHERE 1=1
    AND "Schoolyear4digit" = (SELECT "SchoolYear4Digit" FROM current_schoolyear)
    AND "Goal_type" = 'Expected_NumReturnStudents'

UNION

SELECT
      COALESCE(a."SchoolName", a."School_Applying_to")
	, COALESCE(a."SchoolID", a."School_Applying_to")
	, a."SchoolYear4Digit"
	, a."Grade_Applying_To"
	, a."StatusName"
	, COUNT(DISTINCT a."Application_ID") --AG: used to be -->count(1)
	, CAST(NOW() AS DATE)
    , CASE
        WHEN DATE_PART('day', CAST(NOW() AS DATE)) = 1 THEN 1
        ELSE 0
        END AS "Month_Boolean"
    , CASE
        WHEN DATE_PART('weekday', CAST(NOW() AS DATE)) = 1 THEN 1
        ELSE 0
        END AS "Sunday_Boolean"
FROM apps a
GROUP BY
      a."SchoolYear4Digit"
	, COALESCE(a."SchoolName", a."School_Applying_to")
	, COALESCE(a."SchoolID", a."School_Applying_to")
	, a."Grade_Applying_To"
	, a."StatusName";


UPDATE custom."schoolmint_FactDailyStatus"
SET "CountInStatus" = pm."Goal_num"
FROM custom."schoolmint_FactDailyStatus" fds
INNER JOIN custom."schoolmint_ProgressMonitoring" pm
    ON fds."SchoolYear4DigitEnd" = pm."Schoolyear4digit"
    AND fds."School" = pm."School" -- using school instead of school ID because Bridge rising/upper has the same ID
    AND fds."GradeLevel" = pm."Grade_level"
    AND fds."StatusName" = pm."Goal_type"
WHERE fds."StatusName" IN ('Budget_NumTargetStudents', 'Expected_NumReturnStudents')
    AND fds."CountInStatus" <> pm."Goal_num";

END;
$$;
