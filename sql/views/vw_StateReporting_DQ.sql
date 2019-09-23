SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW    [custom].[vw_StateReporting_DQ] AS (

/****************************************************************************************************
Business Summary: Determines which students are currently enrolled vs. enrolled on Census Day
Used in Current & Historical, Fall 1 Student DQ Reports

SELECT * FROM custom.vw_StateReporting_DQ

Comments:
2017?  CBenson Created
2019-09-19 11:00 FTandoc Updated

****************************************************************************************************/

    SELECT
            cstu.systemStudentid ,
            pstu.state_studentnumber ,
            sc.name SchoolName ,
            sc.school_number ,
            pstu.id ,
            pstu.schoolid ,
            pstu.home_phone ,
            pstu.lastfirst ,
            pstu.first_name ,
            pstu.last_name ,
            pstu.enroll_status EnrollStatus ,
            cstu.gradelevel ,
            CASE
                WHEN pstu.enroll_status = 0
                THEN 1
                ELSE 0
            END AS Ind_ActiveEnrollment
            /*     Indicates whether or not the student was enrolled on census day */
            ,
            CASE
                WHEN pstu.entrydate BETWEEN '02-Aug-2019' AND '02-OCT-2019'
                AND pstu.exitdate > '03-OCT-2019'---PS exit date is true exit date + 1
                THEN 1
                ELSE 0
            END AS Ind_CensusEnrollment ,
            CASE
                WHEN pstu.entrydate BETWEEN '02-Aug-2019' AND '02-OCT-2019'
                AND pstu.exitdate > '20-SEP-2019' ---PS exit date is true exit date + 1
                THEN 1
                ELSE 0
            END AS Ind_BudgetEnrollment
            /*     Indicates whether or not the student was exited */
            ,
            CASE
                WHEN pstu.enroll_status != 0
                AND pstu.entrydate > '01-Jul-2019'
                THEN 1
                ELSE 0
            END AS Ind_Exited
            /*,    CASE
                   WHEN pstu.exitcode = 'N470' or (pstu.exitcode = 'E450' and pstu.exitdate =
                   pstu.entrydate) then 'Exited - No-show'
                   WHEN pstu.enroll_status != 0 and pstu.exitdate > '01-Sep-2017' then 'Exited -
                   Mid-year
                   exit'
                   else 'Still Enrolled'
                   end as exitstatus*/
            ,
            CASE
                WHEN pstu.enroll_status != 0
                AND pstu.exitdate BETWEEN GETDATE() + 1 AND '20-Jun-2012'
                THEN 'Incorrect Exit'
                WHEN pstu.enroll_status != 0
                AND pstu.exitdate < pstu.entrydate
                THEN 'Incorrect Exit'
                WHEN pstu.enroll_status != 0
                AND pstu.exitdate < '01-Sep-2019'
                AND pstu.exitdate > pstu.entrydate
                THEN 'No Issue'
                    /*AWHEN pstu.enroll_status != 0
                    AND pstu.exitdate < '01-Sep-2019'
                    AND (((pstu.exitdate != '01-Aug-2019'
                    OR  pstu.entrydate != '01-AUG-2019')
                    OR  pstu.exitcode NOT IN ('N470',
                    'E450')))
                    THEN 'Incorrect Exit'*/
                ELSE 'No Issue'
            END AS Ind_InvalidExit ,
            pstu.entrydate ,
            pstu.exitdate ,
            cstu.gender ,
            cstu.dateofbirth AS DOB ,
            CASE
                WHEN cstu.birthplacecountry IS NULL
                THEN 'Not Specified'
                ELSE cstu.birthplacecountry
            END AS BirthPlace_Country ,
            CASE
                WHEN cstu.address IS NULL
                THEN 'Not Specified'
                ELSE 'Specified'
            END AS Address ,
            cstu.address as Mailing_Address,
            CASE
                WHEN cstu.city IS NULL
                THEN 'Not Specified'
                ELSE 'Specified'
            END         AS city ,
            pstu.city   AS 'city_map' ,
            cstu.[state    ] ,
            cstu.zip    AS zip_map ,
            CASE
                WHEN cstu.zip IS NULL
                THEN 'Not Specified'
                ELSE 'Specified'
            END AS zip ,
            pstu.mother,
            pstu.father,
            CASE
                WHEN pstu.mother IS NULL
                AND pstu.father IS NULL
                AND cstm.Guardian_LN IS NULL
                THEN 'No Parent/Guardian'
                ELSE ''
            END AS Parent_Guard_Flag ,
            CASE
                WHEN pstu.fedethnicity = 0
                THEN 'Not Hispanic'
                WHEN pstu.fedethnicity = 1
                THEN 'Hispanic/Latino'
                ELSE 'Not Specified'
            END AS Fed_Ethnicity
            /*     Race & Ethnicity field in the Tableau Report*/
            ,
            cstu.primaryethnicgroup ,
            CASE
                WHEN pstu.districtofresidence IS NULL
                THEN 'Not Specified'
                ELSE 'Specified'
            END AS District_of_Residence ,
            CASE
                WHEN pstu.state_studentnumber IS NULL
                THEN 'Not Specified'
                ELSE 'Specified'
            END AS SSID ,
            (
                SELECT
                    CASE
                        WHEN COUNT(sr.racecd) > 1
                        THEN 'Mixed'
                        ELSE MIN(sr.racecd)
                    END AS RaceCP
                FROM
                    Powerschool.Powerschool_StudentRace sr
                WHERE
                    sr.studentid = pstu.id)    RACE_CP ,
            cstu.primarydisability          AS SPED_Program_Code,
            CASE
                WHEN cstu.primarydisability LIKE '2%'
                THEN 'Has an IEP'
                WHEN cstu.primarydisability LIKE '3%'
                THEN 'Has an IEP'
                WHEN cstu.primarydisability LIKE '4%'
                THEN 'Has an IEP'
                WHEN cstu.primarydisability LIKE '5%'
                THEN 'Has an IEP'
                WHEN cstu.primarydisability LIKE '6%'
                THEN 'Has an IEP'
                WHEN cstu.primarydisability LIKE '0%'
                THEN 'No IEP'
                ELSE 'No IEP'
            END AS 'IEP Status' ,
            CASE
                WHEN UPPER(cstu.LunchStatus) = 'F'
                THEN 'Free'
                WHEN UPPER(cstu.LunchStatus) = 'R'
                THEN 'Reduced'
                WHEN UPPER(cstu.LunchStatus) = 'FDC'
                THEN 'Free Direct Certification'
                WHEN UPPER(cstu.LunchStatus) = 'P'
                THEN 'Paid'
                WHEN UPPER(cstu.LunchStatus) = 'T'
                THEN 'Application Missing'
                ELSE 'Not Specified'
            END AS LunchStatus ,
            pstu.exitcode
            /*
            ,CASE
             WHEN UPPER(cstu.LunchStatus) = 'F' THEN 'Free/Reduced'
             when UPPER(cstu.LunchStatus) = 'R' THEN 'Free/Reduced'
             when UPPER(cstu.LunchStatus) = 'FDC' THEN 'Free/Reduced'
             ELSE 'Paid'
             END AS 'Free/Reduced Status'
            */
            ,
            CASE
                WHEN UPPER(cstu.LunchStatus) = 'F'
                THEN 'Unduplicated'
                WHEN UPPER(cstu.LunchStatus) = 'R'
                THEN 'Unduplicated'
                WHEN UPPER(cstu.LunchStatus) = 'FDC'
                THEN 'Unduplicated'
                WHEN cstm.homeless_code IS NOT NULL
                THEN 'Unduplicated'
                WHEN cstu.languagefluency = 'EL'
                THEN 'Unduplicated'
                ELSE 'Ineligible'
            END AS 'Unduplicated Status' ,
            CASE
                WHEN cstm.homeless_code IS NOT NULL
                THEN 'Eligible'
                ELSE 'Ineligible'
            END AS 'Homeless Status'
            /*Custom CA Fields from powerschool_customfields_getcf*/
            ,
            cstm.CA_PrimaryLanguage ,
            cstm.ParentEd
            /*Whether or not First USA school date needs to be provided*/
            ,
            cstu.languagefluency ,
            CASE
                WHEN (cstu.birthplacecountry NOT IN ('US',
                                                     'PR')
                    OR  cstu.languagefluency = 'EL')
                AND cstm.FirstUSASchooling IS NULL
                THEN 'Need 1st USA School Date'
                ELSE 'Specified/Not Needed'
            END                    AS first_usa_school_test ,
            cstm.FirstUSASchooling AS FirstUSA_School ,
            cstm.BirthCountry ,
            pstu.schoolentrydate
            /*Below needs to be updated with the new exit reason*/
            ,
            CASE
                WHEN (enr.exitreason IS NULL
                    AND pstu.enroll_status !=0)
                OR  (enr.exitreason LIKE '-----'
                    AND pstu.enroll_status !=0)
                THEN
                    CASE
                        WHEN pstu.entrydate = pstu.exitdate
                        AND schoolentrydate > '1-Aug-2019'
                        THEN 'None Needed'
                        ELSE 'Missing Exit Reason'
                    END
                WHEN enr.exitreason IS NOT NULL
                AND enr.exitreason NOT LIKE '-----'
                THEN 'Has Exit Reason'
                ELSE 'None Needed'
            END AS ExitReason_flag ,
            CASE
                WHEN enr.exitreason LIKE '-----'
                THEN NULL
                ELSE enr.exitreason
            END AS exitreason ,
            pstu.exitcomment ,
            CASE
                WHEN enr.exitreason LIKE '%Other%'
                AND enr.exitreason NOT LIKE '%Another%'
                AND pstu.exitcomment IS NULL
                THEN 'Exit Comment Needed'
                WHEN enr.exitreason LIKE '%Know%'
                AND pstu.exitcomment IS NULL
                THEN 'Exit Comment Needed'
                ELSE 'No Exit Comment Needed'
            END AS ExitComment_Flag ,
            CASE
                WHEN (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '181') LIKE '181'
                THEN 'Free Eligibile'
                WHEN (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '182') LIKE '182'
                THEN 'Reduced Eligible'
                ELSE ''
            END AS FRL_Program ,
            CASE
                WHEN (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '181') LIKE '181'
                AND (UPPER(cstu.lunchstatus) = 'F'
                    OR  UPPER(cstu.lunchstatus) = 'FDC')
                THEN 'Program Match'
                WHEN (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '181') LIKE '181'
                AND (UPPER(cstu.lunchstatus) != 'F'
                    OR  UPPER(cstu.lunchstatus) != 'FDC')
                THEN 'Program Mismatch'
                WHEN (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '182') LIKE '182'
                AND UPPER(cstu.lunchstatus) = 'R'
                THEN 'Program Match'
                WHEN (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '182') LIKE '182'
                AND UPPER(cstu.lunchstatus) != 'R'
                THEN 'Program Mismatch'
                WHEN UPPER(cstu.lunchstatus) = 'P'
                THEN ''
                ELSE 'No Program Enrollment'
            END AS FRL_Program_Match ,
            CASE
                WHEN (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '144') LIKE '144'
                THEN 'SPED Program'
                ELSE ''
            END                    AS Sped_Program ,
            cstm.PrimaryDisability AS 'Primary Disability' ,
            CASE
                WHEN cstm.PrimaryDisability IS NOT NULL
                AND cstm.PrimaryDisability != 0
                AND (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '144') LIKE '144'
                THEN 'Program Match'
                WHEN cstm.PrimaryDisability IS NOT NULL
                AND cstm.PrimaryDisability != 0
                AND (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '144') IS NULL
                THEN 'Program Enrollment Needed'
                WHEN cstm.PrimaryDisability = 0
                THEN 'No IEP'
                WHEN cstm.PrimaryDisability IS NULL
                THEN 'No IEP'
                ELSE 'logic needs attention'
            END AS SpedEnrollmentFlag ,
            CASE
                WHEN (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '191') LIKE '191'
                THEN 'Homeless Program'
                ELSE ''
            END                AS Homeless_Program ,
            cstm.homeless_code AS HomelessCode ,
            CASE
                WHEN (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '191') LIKE '191'
                AND cstm.homeless_code IS NOT NULL
                THEN 'Program Match'
                WHEN cstm.homeless_code IS NULL
                THEN 'Not Eligible'
                WHEN cstm.homeless_code IS NOT NULL
                AND (
                        SELECT
                            MAX(v2.user_defined_text)
                        FROM
                            PowerSchool.PowerSchool_virtualtablesdata2 v2
                        WHERE
                            v2.foreignkey = pstu.id
                        AND v2.linkto_def_id = 1032
                        AND v2.created_on > '01-AUG-2019'
                        AND v2.user_defined_date > '01-Aug-2019'
                        AND v2.user_defined_text LIKE '191') IS NULL
                THEN 'Program Enrollment Needed'
                ELSE 'Logic Needs Attention'
            END AS Homeless_Program_Enrollment ,
            (
                SELECT
                    CONVERT(VARCHAR(9),MIN(cd.date_value), 10) AS firstday
                FROM
                    PowerSchool.PowerSchool_Schools sc1
                JOIN
                    PowerSchool.PowerSchool_Calendar_Day cd
                ON
                    sc1.school_number = cd.schoolid
                WHERE
                    cd.date_value > '01-AUG-2019'
                AND cd.membershipvalue = 1
                AND sc1.school_number = sc.school_number
                GROUP BY
                    sc1.school_number ) AS School_FirstDay ,
            (
                SELECT
                    CONVERT(VARCHAR(9),MAX(cd.date_value), 10) AS lastday
                FROM
                    PowerSchool.PowerSchool_Schools sc1
                JOIN
                    PowerSchool.PowerSchool_Calendar_Day cd
                ON
                    sc1.school_number = cd.schoolid
                WHERE
                    cd.date_value > '01-AUG-2019'
                AND cd.membershipvalue = 1
                AND sc1.school_number = sc.school_number
                GROUP BY
                    sc1.school_number ) AS School_LastDay ,
            (
                SELECT
                    COUNT(cd.DATE_VALUE) AS totaldays
                FROM
                    PowerSchool.PowerSchool_Schools sc1
                JOIN
                    PowerSchool.PowerSchool_Calendar_Day cd
                ON
                    sc1.school_number = cd.schoolid
                WHERE
                    cd.date_value > '01-AUG-2019'
                AND cd.membershipvalue = 1
                AND sc1.school_number = sc.school_number
                GROUP BY
                    sc1.school_number ) AS School_TotalDays ,
            CASE
                WHEN sc.name LIKE '%Bridge%'
                AND pstu.districtofresidence LIKE '%161259'
                THEN 'In District'
                WHEN sc.name LIKE '%Summit%'
                AND pstu.districtofresidence LIKE '%161309'
                THEN 'In District'
                WHEN sc.name LIKE '%King%'
                AND pstu.districtofresidence LIKE '%161309'
                THEN 'In District'
                WHEN sc.name LIKE '%Heartwood%'
                AND pstu.districtofresidence LIKE '4369369'
                THEN 'In District'
                WHEN sc.name LIKE '%Heritage%'
                AND pstu.districtofresidence LIKE '4369450'
                THEN 'In District'
                WHEN sc.name LIKE '%Prize%'
                AND pstu.districtofresidence LIKE '4369369'
                THEN 'In District'
                WHEN sc.name LIKE '%San Jose%'
                AND pstu.districtofresidence LIKE '4369427'
                THEN 'In District'
                WHEN sc.name LIKE '%Excelencia%'
                AND pstu.districtofresidence LIKE '4169005'
                THEN 'In District'
                WHEN sc.name LIKE '%Bay Academy%'
                AND pstu.districtofresidence LIKE '3868478'
                THEN 'In District'
                WHEN sc.name LIKE '%College Prep%'
                AND pstu.districtofresidence LIKE '3868478'
                THEN 'In District'
                WHEN sc.name LIKE '%Bayview%'
                AND pstu.districtofresidence LIKE '3868478'
                THEN 'In District'
                WHEN sc.name LIKE '%Valiant%'
                AND pstu.districtofresidence LIKE '4168999'
                THEN 'In District'
                WHEN sc.name LIKE '%Navigate%'
                AND pstu.districtofresidence LIKE '4369427'
                THEN 'In District'
                ELSE 'Out of District'
            END AS Indistrict_Indicator ,
            pstu.districtofresidence ,
            cstm.sm_hls_q1 ,
            cstm.sm_hls_q2 ,
            cstm.sm_hls_q3 ,
            cstm.sm_hls_q4 ,
            /*
            cstm.sm_hls_q1 AS 'HLS 1' ,
            cstm.sm_hls_q1 AS 'HLS 2' ,
            cstm.sm_hls_q1 AS 'HLS 3' ,
            cstm.sm_hls_q1 AS 'HLS 4' ,
            CASE
            WHEN cstm.sm_hls_q1 IS NULL
            OR  cstm.sm_hls_q2 IS NULL
            OR  cstm.sm_hls_q3 IS NULL
            THEN 'N/A'
            WHEN cstm.sm_hls_q1 = 00
            AND cstm.sm_hls_q2 = 00
            AND cstm.sm_hls_q3 = 00
            THEN 'English Only'
            ELSE 'Other'
            END AS 'HLS Analysis' ,
            */
            CASE
                WHEN pstu.log LIKE '%Schoolmint%'
                THEN substring(pstu.log, (charindex('[', pstu.log) +1) , (charindex('-', pstu.log,
                    0)-2))
                ELSE substring(pstu.log, (charindex('[', pstu.log) +1) , (charindex('-', pstu.log,
                    0)-3))
            END AS 'Date Synced' ,
            pstu.street
        FROM
            dw.DW_dimStudent cstu
        RIGHT JOIN
            PowerSchool.Powerschool_students pstu
        ON
            cstu.SystemStudentID = CONVERT(VARCHAR(50), CONVERT(bigint,pstu.student_number))
        RIGHT JOIN
            PowerSchool.Powerschool_schools sc
        ON
            pstu.schoolid = sc.school_number
        RIGHT JOIN
            dw.DW_dimEnrollment enr
        ON
            cstu.SystemStudentID = enr.SystemStudentID
        RIGHT JOIN
            Custom.CustomFields_getcf_Students_Pivot cstm
        ON
            cstu.SystemStudentID = cstm.student_number
        WHERE
            sc.name NOT LIKE '%Graduated%'
        AND sc.name NOT LIKE '%Wait%'
        AND enr.entrydate BETWEEN '1-Jul-2019' AND '01-Jun-2020'
    )
GO
