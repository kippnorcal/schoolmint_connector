SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE PROC [custom].[sproc_SchoolMint_Raw_UpdateSchoolYear]
AS
/***************************************************************************
Name: custom.sproc_SchoolMint_Raw_UpdateSchoolYear

Business Purpose: Populate SchoolYear4Digit in schoolmint_ApplicationData_raw
Called daily by SchoolMint python code.

Comments:
2019-10-08	3:30PM		pkats		Initial sproc
***************************************************************************/
SET NOCOUNT ON

UPDATE raw1
SET SchoolYear4Digit = SchoolYear4Digit_int
FROM custom.schoolmint_ApplicationData_raw raw1
INNER JOIN [custom].SchoolMint_lk_Enrollment lk
	ON raw1.Enrollment_Period = lk.Enrollment_Period_id
GO

