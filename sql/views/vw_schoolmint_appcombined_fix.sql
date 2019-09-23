SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE VIEW
   [custom].[vw_schoolmint_appcombined_fix] AS
   
SELECT
    stat.* ,
    bug.Budget_NumTargetStudents
FROM
    custom.vw_schoolmint_appStatusList stat
JOIN
    custom.Schoolmint_budgetandexpect_num bug
ON
    bug.schoolid = stat.schoolid
AND stat.gradelevel = bug.[GradeLevel]
AND stat.SchoolYear4DigitEnd = bug.SchoolYear4digitEnd

GO
