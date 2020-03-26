CREATE TABLE [custom].[schoolmint_FactDailyStatus](
	[ID] [int] IDENTITY(5749839,1) NOT NULL,
	[School] [varchar](500) NULL,
	[SchoolID] [varchar](50) NULL,
	[SchoolYear4DigitEnd] [varchar](4) NULL,
	[GradeLevel] [varchar](500) NULL,
	[StatusName] [varchar](128) NULL,
	[CountInStatus] [int] NULL,
	[ReportDate] [date] NOT NULL,
	[Month_Boolean]  AS (case when datepart(day,[ReportDate])=(1) then (1) else (0) end),
	[Sunday_Boolean]  AS (case when datepart(weekday,[ReportDate])=(1) then (1) else (0) end)
) ON [PRIMARY]
