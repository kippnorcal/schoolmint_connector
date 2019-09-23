SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE VIEW [custom].[vw_Schoolmint_FactDailyStatus] AS

select 
        fds.*
        ,CASE
                WHEN eomonth(fds.reportdate) = fds.reportdate THEN 1
                ELSE 0
         END AS lastday_month_boolean
         ,bug.Budget_NumTargetStudents

from custom.schoolmint_factdailystatus fds
JOIN CUSTOM.Schoolmint_budgetandExpect_Num as bug on (bug.schoolid = fds.schoolid AND bug.gradelevel = fds.gradelevel
and bug.SchoolYear4digitEnd = fds.SchoolYear4DigitEnd)

GO
