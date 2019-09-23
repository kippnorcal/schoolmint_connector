SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO




CREATE VIEW [custom].[vw_SchoolMint_AppStatusList] 
 AS 

SELECT
    School =   u.School ,
    SchoolID = u.SchoolID ,
    SchoolYear4DigitEnd = u.SchoolYear4digitEnd ,
    GradeLevel = u.[GradeLevel] ,
    StatusName =               u.StatusName ,
    CountInStatus =            u.TheCount
FROM
    custom.Schoolmint_BudgetandExpect_Num defaults unpivot ( TheCount FOR StatusName IN
                                                                                         (
                                                                                         Budget_NumTargetStudents
                                                                                         ,
                                                                                         Expected_NumReturnStudents
                                                                                         ) )u
UNION ALL
SELECT 
	 School = sch.School
	,SchoolID = sch.SchoolID
	,SchoolYear4DigitEnd  = RIGHT(app.Enrollment_Period, 4)
	,GradeLevel  = app.Grade_Applying_To
	,StatusName = sta.StatusName 
	,CountInStatus = count(*)
FROM
	custom.schoolmint_ApplicationData_raw  app
	inner join custom.schoolmint_ApplicationStatuses sta
		on app.Application_Status = sta.[Status]
	inner join (
			SELECT DISTINCT ben.School, ben.SchoolID, sc.SchoolMint_SchoolID
			FROM custom.Schoolmint_BudgetandExpect_Num ben
			INNER JOIN custom.SchoolMint_SchoolCodes sc
				ON ben.School = sc.School
		)sch
		ON (sch.School = app.School_Applying_to OR sch.SchoolMint_SchoolID = app.School_Applying_to)
GROUP BY 
sch.School,
	 sch.SchoolID
	,RIGHT(app.Enrollment_Period, 4)
	,app.Grade_Applying_To
	,sta.StatusName





GO
