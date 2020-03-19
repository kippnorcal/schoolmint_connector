CREATE VIEW custom.vw_Schoolmint_FactProgressMonitoring AS
/*********************************************************************
Business Summary: Returns progress monitoring data for tableau data for SM Revamp from 3/1/2020

Comments:
2020-03-05  8:00am      AGonzalez        Created
*********************************************************************/

WITH CurrProgress AS (
        SELECT
        Schoolyear4digit
        , Schoolname
        , Systemschoolid
        , Lkschoolid
        , Gradelevel
        , Is_Transitiongrade
        , Goaltype
        , Goalnum
        , Goaldate
        , Goalprogress
        , Reportdate
        , Distancefromgoal_Absolute
        , Weeksremainingtogoal
        , Monthsremainingtogoal
        , Distancetogoal_Capped
        , Goalmet_Boolean
        , Percentgoalmet
        , Unitsperweek_Togoal
        , Unitspermonth_Togoal

        FROM Custom.vw_Schoolmint_ProgressMonitoring Pm
        WHERE 1 = 1
        AND Pm.Schoolyear4digit = 2021 -- current year
        AND pm.GradeLevel <> 'Total'

), LastDayMonth AS (
    SELECT
        fds.Schoolyear4digitend
        ,fds.Schoolid
        ,fds.Gradelevel
        ,MONTH(fds.Reportdate) AS ReportMonth
        ,max(fds.Reportdate) AS ReportDate
    FROM custom.Schoolmint_Factdailystatus fds
    GROUP BY
        fds.Schoolyear4digitend
        ,fds.Schoolid
        ,fds.Gradelevel
        , MONTH(fds.Reportdate)

), FactRecord AS (
        SELECT
        fds.School
        , fds.Schoolid
        , fds.Schoolyear4digitend
        , fds.Gradelevel
        , fds.Statusname
        , fds.Countinstatus
        , fds.Reportdate
        , ROW_NUMBER() OVER (PARTITION BY fds.School, fds.Schoolid, fds.Gradelevel, FDS.Statusname
                    ,fds.Schoolyear4digitend, MONTH (fds.ReportDate)
                    ORDER BY fds.ReportDate DESC) AS LastDateinMonth
        FROM custom.Schoolmint_Factdailystatus fds
        INNER JOIN LastDayMonth ld
            ON fds.Schoolyear4digitend = ld.Schoolyear4digitend
            AND fds.Schoolid = ld.Schoolid
            AND fds.Gradelevel = ld.Gradelevel
            AND fds.Reportdate = ld.ReportDate
        WHERE 1=1
        AND fds.Schoolyear4digitend >= 2019 --pulling in last 3 years for sql performance purposes
        AND fds.Statusname NOT IN ('Budget_NumTargetStudents', 'Expected_NumReturnStudents')
 )

SELECT
       Fds.School
     , Fds.Schoolid
     , Fds.Schoolyear4digitend
     , Fds.Gradelevel
     , Fds.Statusname
     , Fds.Countinstatus
     , Fds.Reportdate
     , P.Is_Transitiongrade
     , P.Goaltype
     , P.Goalnum
     , P.Goaldate
     , P.Goalprogress
     , P.Reportdate AS Goalreportdate
     , fds.Lastdateinmonth
     , P.Distancefromgoal_Absolute
     , P.Weeksremainingtogoal
     , P.Monthsremainingtogoal
     , P.Distancetogoal_Capped
     , P.Goalmet_Boolean
     , P.Percentgoalmet
     , P.Unitsperweek_Togoal
     , P.Unitspermonth_Togoal
FROM Factrecord Fds
LEFT JOIN Currprogress P
    ON Fds.Schoolyear4digitend = P.Schoolyear4digit
    AND Fds.Schoolid = P.Systemschoolid
    AND Fds.Gradelevel = P.Gradelevel
    AND Fds.Reportdate = P.Reportdate

WHERE 1 = 1
  AND Fds.Schoolyear4digitend >= 2019
  AND Fds.Lastdateinmonth = 1
go

