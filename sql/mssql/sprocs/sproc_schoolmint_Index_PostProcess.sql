CREATE PROCEDURE [custom].[sproc_schoolmint_Index_PostProcess] (@CurrentSchoolYear INT)
AS
SET NOCOUNT ON
/***************************************************************************
Name: custom.sproc_SchoolMint_Index_PostProcess

Business Purpose: Populate SchoolYear4Digit in schoolmint_ApplicationDataIndex_raw
Called daily by SchoolMint python code.

Comments:
2019-10-08	3:30PM		pkats		Initial sproc
***************************************************************************/

DECLARE @CurrentRowCount INT

UPDATE index1
SET SchoolYear4Digit = SchoolYear4Digit_int
FROM custom.schoolmint_ApplicationDataIndex_raw index1
INNER JOIN custom.schoolmint_ApplicationData_raw raw1 
	ON raw1.Application_ID = index1.application_id
INNER JOIN custom.schoolmint_lk_Enrollment lk 
	ON raw1.Enrollment_Period = lk.Enrollment_Period_id
WHERE index1.SchoolYear4Digit IS NULL

/* Get the rowcount for the current year */
SELECT @CurrentRowCount = COUNT(*)
FROM custom.schoolmint_ApplicationDataIndex_raw
WHERE SchoolYear4Digit = @CurrentSchoolYear

IF @CurrentRowCount = 0
BEGIN /* There was a problem, revert from backup */
	INSERT INTO custom.schoolmint_ApplicationDataIndex_raw
	SELECT *
	FROM custom.schoolmint_ApplicationDataIndex_raw_backup;
END

SELECT COUNT(*) IndexCT
	,(
		SELECT COUNT(*)
		FROM custom.schoolmint_ApplicationDataIndex_raw_backup
		) BackupRowCT
FROM custom.schoolmint_ApplicationDataIndex_raw
WHERE SchoolYear4Digit = @CurrentSchoolYear;
