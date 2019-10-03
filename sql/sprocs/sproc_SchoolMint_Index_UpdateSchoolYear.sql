
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROC [custom].[sproc_SchoolMint_Index_UpdateSchoolYear]
AS

SET NOCOUNT ON

	update index1
	set SchoolYear4Digit = SchoolYear4Digit_int
	from custom.schoolmint_ApplicationDataIndex_raw index1
	join custom.schoolmint_ApplicationData_raw raw1 on raw1.Application_ID=index1.application_id
	join [custom].SchoolMint_Enrollment_LKP lkp ON raw1.Enrollment_Period = lkp.Enrollment_Period_id

GO
