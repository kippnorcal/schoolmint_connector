CREATE PROCEDURE custom."sproc_schoolmint_Raw_PostProcess"(integer)
LANGUAGE plpgsql
AS $$
BEGIN
/***************************************************************************
Name: custom.sproc_SchoolMint_Raw_PostProcess

Business Purpose: Populate SchoolYear4Digit in schoolmint_ApplicationData_raw
Called daily by SchoolMint python code.

Notes:
  - $1 variable is CurrentSchoolYear

Comments:
2019-10-08	3:30PM		pkats		Initial sproc
***************************************************************************/

UPDATE custom."schoolmint_ApplicationData_raw" raw1
SET "SchoolYear4Digit" = lk."SchoolYear4Digit_int"
FROM custom."schoolmint_lk_Enrollment" lk
WHERE raw1."Enrollment_Period" = CAST(lk."Enrollment_Period_id" AS VARCHAR)
    AND raw1."SchoolYear4Digit" IS NULL;


/* Get the rowcount for the current year */
DECLARE
    current_rowcount integer := (SELECT COUNT(*) FROM custom."schoolmint_ApplicationData_raw" WHERE "SchoolYear4Digit" = $1);
    BEGIN
        IF current_rowcount = 0
        THEN /* There was a problem, revert from backup */
            INSERT INTO custom."schoolmint_ApplicationData_raw"
            SELECT *
            FROM custom."schoolmint_ApplicationData_raw_backup";
        END IF;
    END;


SELECT
      COUNT(*) AS RawCT
	,(SELECT COUNT(*) FROM custom."schoolmint_ApplicationData_raw_backup") AS BackupRowCT
FROM custom."schoolmint_ApplicationData_raw"
WHERE "SchoolYear4Digit" = $1;

END;
$$;