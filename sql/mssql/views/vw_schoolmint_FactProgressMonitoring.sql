CREATE VIEW custom.vw_schoolmint_FactProgressMonitoring AS
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
    FROM custom.vw_schoolmint_ProgressMonitoring
    WHERE 1 = 1
        AND Schoolyear4digit = 2021 -- current year
        AND GradeLevel <> 'Total'
)

, LastDayMonth AS (
    SELECT
          fds.Schoolyear4digitend
        , fds.Schoolid
        , fds.Gradelevel
        , MONTH(fds.Reportdate) AS ReportMonth
        , MAX(fds.Reportdate) AS ReportDate
    FROM custom.schoolmint_Factdailystatus fds
    GROUP BY
          fds.Schoolyear4digitend
        , fds.Schoolid
        , fds.Gradelevel
        , MONTH(fds.Reportdate)
)

, FactRecord AS (
    SELECT
          fds.School
        , fds.Schoolid
        , fds.Schoolyear4digitend
        , fds.Gradelevel
        , fds.Statusname
        , fds.Countinstatus
        , fds.Reportdate
        , ROW_NUMBER() OVER (PARTITION BY fds.School, fds.Schoolid, fds.Gradelevel, FDS.Statusname, fds.Schoolyear4digitend, MONTH(fds.ReportDate) ORDER BY fds.ReportDate DESC) AS LastDateinMonth
    FROM custom.schoolmint_Factdailystatus fds
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
       fds.School
     , fds.Schoolid
     , fds.Schoolyear4digitend
     , fds.Gradelevel
     , fds.Statusname
     , fds.Countinstatus
     , fds.Reportdate
     , p.Is_Transitiongrade
     , p.Goaltype
     , p.Goalnum
     , p.Goaldate
     , p.Goalprogress
     , p.Reportdate AS Goalreportdate
     , fds.Lastdateinmonth
     , p.Distancefromgoal_Absolute
     , p.Weeksremainingtogoal
     , p.Monthsremainingtogoal
     , p.Distancetogoal_Capped
     , p.Goalmet_Boolean
     , p.Percentgoalmet
     , p.Unitsperweek_Togoal
     , p.Unitspermonth_Togoal
FROM Factrecord fds
LEFT JOIN Currprogress p
    ON fds.Schoolyear4digitend = p.Schoolyear4digit
    AND fds.Schoolid = p.Systemschoolid
    AND fds.Gradelevel = p.Gradelevel
    AND fds.Reportdate = p.Reportdate
WHERE 1 = 1
  AND fds.Schoolyear4digitend >= 2019
  AND fds.Lastdateinmonth = 1
