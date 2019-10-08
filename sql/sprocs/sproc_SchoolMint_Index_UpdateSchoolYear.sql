
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE PROC [custom].[sproc_SchoolMint_Index_UpdateSchoolYear]
AS


SET NOCOUNT ON

	UPDATE index1
	SET SchoolYear4Digit = SchoolYear4Digit_int
	FROM custom.schoolmint_ApplicationDataIndex_raw index1
	INNER JOIN custom.schoolmint_ApplicationData_raw raw1 
		ON raw1.Application_ID=index1.application_id
	INNER JOIN [custom].SchoolMint_lk_Enrollment lk 
		ON raw1.Enrollment_Period = lk.Enrollment_Period_id



GO
