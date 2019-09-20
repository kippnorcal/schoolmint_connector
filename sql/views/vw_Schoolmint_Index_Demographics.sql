SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO



CREATE VIEW [custom].[vw_Schoolmint_Index_Demographics] AS
    
SELECT
    ind.* ,
    sel.enrollment_period ,
    sel.last_update_date ,
    sel.last_status_change ,
    sel.studentaddress_coordinates ,
    sel.how_did_you_hear_about_us ,
    sel.free_reduced_lunch ,
    sel.priorities AS priorities_custom
        ,Stat.statusname
        ,stat.statusDescription
        ,stat.statusgroupname
	,SchoolName_normalized = sch.School
	,SchoolID_normalized = sch.SchoolID

FROM CUSTOM.schoolmint_applicationDataIndex_raw ind
INNER JOIN CUSTOM.schoolmint_ApplicationData_raw sel 
        ON ind.applicantion_id = sel.application_id AND ind.student_id = SEL.SM_Student_ID
JOIN CUSTOM.schoolmint_ApplicationStatuses stat on stat.status = ind.status
INNER JOIN custom.SchoolMint_SchoolCodes sch
				ON (ind.school_name = sch.School OR sch.SchoolMint_SchoolID = ind.school_name)
		


GO
