CREATE PROC [custom].[sproc_SchoolMint_Raw_PrepareTables]
AS

SET NOCOUNT ON



--If Raw Table has data, then truncate backup table and load backup table from Raw. Otherwise, dont truncate Backup Table
IF (
		SELECT count(1)
		FROM custom.schoolmint_ApplicationData_raw
		) > 0
BEGIN
	TRUNCATE TABLE custom.schoolmint_ApplicationData_raw_backup;

	INSERT INTO custom.schoolmint_ApplicationData_raw_backup
	SELECT *
	FROM custom.schoolmint_ApplicationData_raw;

	TRUNCATE TABLE custom.schoolmint_ApplicationData_raw;
END



SELECT count(1) ct
FROM custom.schoolmint_ApplicationData_raw;
