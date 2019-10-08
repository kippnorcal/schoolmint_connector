CREATE PROC [custom].[sproc_SchoolMint_RawIndex_PrepareTables]
AS
SET NOCOUNT ON

/***************************************************************************
Name: custom.sproc_SchoolMint_RawIndex_PrepareTables

Business Purpose: Prepare primary and backup tables for SchoolMint load.
If the primary table has data, then truncate the backup table and load it with data frim the primary table.
Otherwise, don't truncate the backup table.

Called daily by SchoolMint python code.

Comments:
2019-10-08	3:30PM		pkats		Initial sproc
***************************************************************************/
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