CREATE PROC [custom].[sproc_SchoolMint_RawIndex_PrepareTables]
AS
SET NOCOUNT ON

--If RawIndex Table has data, then truncate backup table and load backup table from RawIndex. Otherwise, dont truncate Backup Table
IF (
		SELECT count(1)
		FROM custom.schoolmint_ApplicationDataIndex_raw
		) > 0
BEGIN
	TRUNCATE TABLE custom.schoolmint_ApplicationDataIndex_raw_backup;

	INSERT INTO custom.schoolmint_ApplicationDataIndex_raw_backup
	SELECT *
	FROM custom.schoolmint_ApplicationDataIndex_raw;

	TRUNCATE TABLE custom.schoolmint_ApplicationDataIndex_raw;
END

SELECT count(1) ct
FROM custom.schoolmint_ApplicationDataIndex_raw;
