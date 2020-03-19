SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [custom].[schoolmint_ApplicationData_changehistory](
	[Application_ID] [varchar](500) NULL,
	[SM_Student_ID] [varchar](500) NULL,
	[Application_Student_Id] [varchar](500) NULL,
	[SIS_Student_Id] [varchar](500) NULL,
	[Application_Status] [varchar](500) NULL,
	[Application_Type] [varchar](500) NULL,
	[Account_ID] [varchar](500) NULL,
	[Enrollment_Period] [varchar](500) NULL,
	[Submission_Date] [varchar](500) NULL,
	[Submitted_By] [varchar](500) NULL,
	[Offered_Date] [varchar](500) NULL,
	[Accepted_Date] [varchar](500) NULL,
	[Registration_Completed_Date] [varchar](500) NULL,
	[Last_Update_Date] [varchar](500) NULL,
	[Student_ID] [varchar](500) NULL,
	[Last_Status_Change] [varchar](500) NULL,
	[District] [varchar](500) NULL,
	[Application_Status_Previous] [varchar](500) NULL,
	[Last_Update_Date_Previous] [varchar](500) NULL,
	[Last_Status_Change_Previous] [varchar](500) NULL,
	[ChangeTracking] [varchar](500) NULL,
	[ChangeTrackingDate] [datetime] NOT NULL CONSTRAINT [DF_schoolmint_ApplicationData__changehistory_ChangeTrackingDate]  DEFAULT (getdate()),
	[SchoolYear4Digit] [int] NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
