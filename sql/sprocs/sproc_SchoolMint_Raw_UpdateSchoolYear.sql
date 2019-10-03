SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROC [custom].[sproc_SchoolMint_Raw_UpdateSchoolYear]
AS

SET NOCOUNT ON

	update raw1
	set SchoolYear4Digit = SchoolYear4Digit_int
	from custom.schoolmint_ApplicationData_raw raw1 
	join [custom].SchoolMint_Enrollment_LKP lkp ON raw1.Enrollment_Period = lkp.Enrollment_Period_id

GO


