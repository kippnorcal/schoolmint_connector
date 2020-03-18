CREATE PROCEDURE custom.sproc_SchoolMint_Create_FactDailyStatus AS
SET NOCOUNT ON
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
FROM [custom].[SchoolMint_FactDailyStatus]
WHERE reportdate = CAST(GETDATE() AS DATE);

WITH current_schoolyear AS(
    SELECT
        MAX(SchoolYear4Digit) SchoolYear4Digit
    FROM [custom].schoolmint_ApplicationData_raw
),apps AS (
	SELECT
	    a.Schoolyear4digit
	    ,a.School_Applying_To
	    ,sch.Schoolid
	    ,sch.School AS SchoolName
        ,a.Application_Id
	    ,a.Application_Student_Id
	    ,a.Grade_Applying_To
	    ,a.Application_Status
	    ,b.Statusname
	    ,lk.Enrollment_Period_Str
	FROM [custom].schoolmint_ApplicationData_raw a
	LEFT JOIN custom.schoolmint_ApplicationStatuses b
	    ON a.Application_Status = b.Status
	LEFT JOIN [custom].SchoolMint_lk_Enrollment lk --AG: is this needed??
	    ON a.Enrollment_Period = lk.Enrollment_Period_id
	LEFT JOIN custom.SchoolMint_SchoolCodes sch
        ON a.School_Applying_to = sch.SchoolMint_SchoolID
	WHERE 1=1
	    AND a.SchoolYear4Digit=(SELECT SchoolYear4Digit FROM current_schoolyear)
	)
INSERT INTO [custom].[SchoolMint_FactDailyStatus] (
	[School]
	,[SchoolID]
	,[SchoolYear4DigitEnd]
	,[GradeLevel]
	,[StatusName]
	,[CountInStatus]
	,[ReportDate]
	)

SELECT
    School
	,Systemschoolid
	,SchoolYear4Digit
	,Grade_Level
	,'Budget_NumTargetStudents' AS STATUS
	,Goal_Num AS CountInStatus
	,CAST(GETDATE() AS DATE) AS ReportDate
FROM custom.Schoolmint_Progressmonitoring --custom.[Schoolmint_BudgetandExpect_Num]
WHERE 1=1
    AND SchoolYear4digit = (SELECT SchoolYear4Digit FROM current_schoolyear)
    AND Goal_Type = 'Budget_NumTargetStudents'

UNION

SELECT
    School
	, Systemschoolid
	, SchoolYear4Digit
	, Grade_Level
	,'Expected_NumReturnStudents' AS STATUS
	, Goal_Num AS CountInStatus
	,CAST(GETDATE() AS DATE)
FROM custom.Schoolmint_Progressmonitoring --custom.[Schoolmint_BudgetandExpect_Num]
WHERE 1=1
    AND SchoolYear4digit = (select SchoolYear4Digit from current_schoolyear)
    AND Goal_Type = 'Expected_NumReturnStudents'

UNION

SELECT
    COALESCE(a.SchoolName, a.school_applying_to)
	,COALESCE(a.schoolID, a.school_applying_to)
	,a.SchoolYear4Digit
	,a.Grade_Applying_To
	,a.statusname
	,COUNT(DISTINCT a.Application_Id) --AG: used to be -->count(1)
	,CAST(GETDATE() AS DATE)
FROM apps a
GROUP BY
    a.SchoolYear4Digit
	,coalesce(a.schoolID, a.school_applying_to)
	,coalesce(a.schoolName, a.school_applying_to)
	,a.Grade_Applying_To
	,a.statusname

UPDATE custom.SchoolMint_FactDailyStatus
SET CountInStatus = PM.Goal_num
FROM custom.SchoolMint_FactDailyStatus FDS
INNER JOIN custom.SchoolMint_ProgressMonitoring PM
    ON FDS.SchoolYear4DigitEnd = PM.Schoolyear4digit
    AND FDS.School = PM.School -- using school instead of school ID because Bridge rising/upper has the same ID
    AND FDS.GradeLevel = PM.Grade_level
    AND FDS.StatusName = PM.Goal_Type
WHERE FDS.StatusName in ('Budget_NumTargetStudents', 'Expected_NumReturnStudents')
    AND FDS.CountInStatus <> PM.Goal_num
    
SELECT @@rowcount AS rc
GO

