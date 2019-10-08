CREATE PROC [custom].[sproc_SchoolMint_Create_FactDailyStatus]
AS
SET NOCOUNT ON

/***************************************************************************
Name: custom.sproc_SchoolMint_Create_FactDailyStatus

Business Purpose: Generate fact daily status table.
Called daily by SchoolMint python code.
Used by student recruitment reports.

Comments:
2019-10-08	3:30PM		pkats		Initial sproc
***************************************************************************/
/* So That Report is Re-Runnable */
DELETE
FROM [custom].[SchoolMint_FactDailyStatus]
WHERE reportdate = CAST(GETDATE() AS DATE);

WITH a
AS (
	SELECT *
	FROM [custom].schoolmint_ApplicationData_raw a
	LEFT JOIN custom.schoolmint_ApplicationStatuses b
		ON a.Application_Status = b.STATUS
	LEFT JOIN [custom].SchoolMint_lk_Enrollment lk
		ON a.Enrollment_Period = lk.Enrollment_Period_id
	)
	, current_schoolyear
AS (
	SELECT max(SchoolYear4Digit_int) SchoolYear4Digit_int
	FROM a
	)
INSERT INTO [custom].[SchoolMint_FactDailyStatus] (
	[School]
	, [SchoolID]
	, [SchoolYear4DigitEnd]
	, [GradeLevel]
	, [StatusName]
	, [CountInStatus]
	, [ReportDate]
	)
SELECT School
	, SchoolID
	, SchoolYear4DigitEnd
	, GradeLevel
	, '' Budget_NumTargetStudents '' AS STATUS
	, Budget_NumTargetStudents AS CountInStatus
	, CAST(GETDATE() AS DATE)
FROM custom.[Schoolmint_BudgetandExpect_Num]
WHERE SchoolYear4digitEnd = (
		SELECT SchoolYear4Digit_int
		FROM current_schoolyear
		)

UNION

SELECT School
	, SchoolID
	, SchoolYear4DigitEnd
	, GradeLevel
	, '' Expected_NumReturnStudents ''
	, Expected_NumReturnStudents AS CountInStatus
	, CAST(GETDATE() AS DATE)
FROM custom.[Schoolmint_BudgetandExpect_Num]
WHERE SchoolYear4digitEnd = (
		SELECT SchoolYear4Digit_int
		FROM current_schoolyear
		)

UNION

SELECT coalesce(school, school_applying_to)
	, coalesce(schoolID, school_applying_to)
	, SchoolYear4Digit
	, Grade_Applying_To
	, statusname
	, count(1)
	, CAST(GETDATE() AS DATE)
FROM a
LEFT JOIN custom.SchoolMint_SchoolCodes b
	ON a.School_Applying_to = b.SchoolMint_SchoolID
GROUP BY SchoolYear4Digit
	, coalesce(schoolID, school_applying_to)
	, coalesce(school, school_applying_to)
	, Grade_Applying_To
	, statusname
ORDER BY schoolid
	, gradelevel
	, STATUS

SELECT @@rowcount AS rc