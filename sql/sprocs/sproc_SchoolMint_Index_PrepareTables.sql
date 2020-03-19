CREATE PROC [custom].[sproc_SchoolMint_Index_PrepareTables] (@CurrentSchoolYear INT)
AS

SET NOCOUNT ON
/***************************************************************************
Name: custom.sproc_SchoolMint_Index_PrepareTables

Business Purpose: Prepare primary and backup tables for SchoolMint load.
If the primary table has data, then truncate the backup table and load it with data frim the primary table.
Otherwise, don't truncate the backup table.

Called daily by SchoolMint python code.

Comments:
2019-10-08	3:30PM		pkats		Initial sproc
***************************************************************************/


--If Index Table has data for the current year, then truncate backup table and load backup table from Raw. Otherwise, dont truncate Backup Table
IF (
		SELECT count(1)
		FROM custom.schoolmint_ApplicationDataIndex_raw
		WHERE SchoolYear4Digit=@CurrentSchoolYear 
		) > 0
BEGIN
	TRUNCATE TABLE custom.schoolmint_ApplicationDataIndex_raw_backup;

	INSERT INTO custom.schoolmint_ApplicationDataIndex_raw_backup
	SELECT *
	FROM custom.schoolmint_ApplicationDataIndex_raw
	WHERE SchoolYear4Digit=@CurrentSchoolYear;

	DELETE FROM custom.schoolmint_ApplicationDataIndex_raw WHERE SchoolYear4Digit=@CurrentSchoolYear;
END



SELECT count(1) ct
FROM custom.schoolmint_ApplicationDataIndex_raw WHERE SchoolYear4Digit=@CurrentSchoolYear;

go