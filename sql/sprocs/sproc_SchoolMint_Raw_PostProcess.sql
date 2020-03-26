
CREATE PROCEDURE [custom].[sproc_schoolmint_Raw_PostProcess] (@CurrentSchoolYear INT) AS
SET NOCOUNT ON
/***************************************************************************
Name: custom.sproc_SchoolMint_Raw_PostProcess

Business Purpose: Populate SchoolYear4Digit in schoolmint_ApplicationData_raw
Called daily by SchoolMint python code.

Comments:
2019-10-08	3:30PM		pkats		Initial sproc
***************************************************************************/

DECLARE @CurrentRowCount int

UPDATE raw1
SET SchoolYear4Digit = SchoolYear4Digit_int
FROM custom.schoolmint_ApplicationData_raw raw1
INNER JOIN custom.schoolmint_lk_Enrollment lk
	ON raw1.Enrollment_Period = lk.Enrollment_Period_id
WHERE SchoolYear4Digit IS NULL

/* Get the rowcount for the current year */
SELECT @CurrentRowCount = COUNT(*)
FROM custom.schoolmint_ApplicationData_raw
WHERE SchoolYear4Digit = @CurrentSchoolYear

IF @CurrentRowCount = 0
BEGIN /* There was a problem, revert from backup */
	INSERT INTO custom.schoolmint_ApplicationData_raw
	SELECT *
	FROM custom.schoolmint_ApplicationData_raw_backup;
END

SELECT COUNT(*) AS RawCT
	,(
		SELECT COUNT(*)
		FROM custom.schoolmint_ApplicationData_raw_backup
	) AS BackupRowCT
FROM custom.schoolmint_ApplicationData_raw
WHERE SchoolYear4Digit = @CurrentSchoolYear;
