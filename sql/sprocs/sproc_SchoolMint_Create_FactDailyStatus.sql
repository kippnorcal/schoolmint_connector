SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROC [custom].[sproc_SchoolMint_Create_FactDailyStatus] 
AS
SET NOCOUNT ON

/* So That Report is Re-Runnable */
DELETE
FROM [custom].[SchoolMint_FactDailyStatus]
WHERE reportdate = CAST(GETDATE() AS DATE);
WITH a
AS (
	SELECT *
	FROM [custom].schoolmint_ApplicationData_raw a
	LEFT JOIN custom.schoolmint_ApplicationStatuses b ON a.Application_Status = b.STATUS
	LEFT JOIN [custom].SchoolMint_Enrollment_LKP lkp ON a.Enrollment_Period = lkp.Enrollment_Period_id
	)
,current_schoolyear as
(select max(SchoolYear4Digit_int) SchoolYear4Digit_int from a)
INSERT INTO [custom].[SchoolMint_FactDailyStatus] (
	[School]
	,[SchoolID]
	,[SchoolYear4DigitEnd]
	,[GradeLevel]
	,[StatusName]
	,[CountInStatus]
	,[ReportDate]
	)
SELECT School
	,SchoolID
	,SchoolYear4DigitEnd
	,GradeLevel
	,'Budget_NumTargetStudents' AS STATUS
	,Budget_NumTargetStudents AS CountInStatus
	,CAST(GETDATE() AS DATE)
FROM custom.[Schoolmint_BudgetandExpect_Num]
WHERE SchoolYear4digitEnd = (select SchoolYear4Digit_int from current_schoolyear)

UNION

SELECT School
	,SchoolID
	,SchoolYear4DigitEnd
	,GradeLevel
	,'Expected_NumReturnStudents'
	,Expected_NumReturnStudents AS CountInStatus
	,CAST(GETDATE() AS DATE)
FROM custom.[Schoolmint_BudgetandExpect_Num]
WHERE SchoolYear4digitEnd = (select SchoolYear4Digit_int from current_schoolyear)

UNION

SELECT coalesce(school, school_applying_to)
	,coalesce(schoolID, school_applying_to)
	,SchoolYear4Digit
	,Grade_Applying_To
	,statusname
	,count(1)
	,CAST(GETDATE() AS DATE)
FROM a
LEFT JOIN custom.SchoolMint_SchoolCodes b ON a.School_Applying_to = b.SchoolMint_SchoolID
GROUP BY SchoolYear4Digit
	,coalesce(schoolID, school_applying_to)
	,coalesce(school, school_applying_to)
	,Grade_Applying_To
	,statusname
ORDER BY schoolid
	,gradelevel
	,STATUS

SELECT @@rowcount AS rc
GO


