CREATE PROCEDURE custom."sproc_schoolmint_Index_PostProcess" (INT)
LANGUAGE plpgsql
AS $$
BEGIN
/***************************************************************************
Name: custom.sproc_SchoolMint_Index_PostProcess

Business Purpose: Populate SchoolYear4Digit in schoolmint_ApplicationDataIndex_raw
Called daily by SchoolMint python code.

Notes:
  - $1 variable is the SchoolYear4Digit

Comments:
2019-10-08	3:30PM		pkats		Initial sproc
***************************************************************************/


UPDATE custom."schoolmint_ApplicationDataIndex_raw" index1
SET "SchoolYear4Digit" = "SchoolYear4Digit_int"
FROM custom."schoolmint_ApplicationDataIndex_raw" index2
INNER JOIN custom."schoolmint_ApplicationData_raw" raw1
	ON raw1."Application_ID" = index2."application_id"
INNER JOIN custom."schoolmint_lk_Enrollment" lk
	ON raw1."Enrollment_Period" = lk."Enrollment_Period_id"
WHERE index2."SchoolYear4Digit" IS NULL;

/* Get the rowcount for the current year */
DECLARE
    CurrentRowCount integer := (SELECT COUNT(*) FROM custom."schoolmint_ApplicationDataIndex_raw" WHERE "SchoolYear4Digit" = $1);
BEGIN
    IF CurrentRowCount = 0 THEN
        /* There was a problem, revert from backup */
        INSERT INTO custom."schoolmint_ApplicationDataIndex_raw"
        SELECT *
        FROM custom."schoolmint_ApplicationDataIndex_raw_backup";
    END IF;
END;


SELECT COUNT(*) AS "IndexCT"
	,(
		SELECT COUNT(*)
		FROM custom."schoolmint_ApplicationDataIndex_raw_backup"
		) AS "BackupRowCT"
FROM custom."schoolmint_ApplicationDataIndex_raw"
WHERE "SchoolYear4Digit" = $1;

END;
$$;