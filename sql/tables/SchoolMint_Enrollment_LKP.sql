SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [custom].[SchoolMint_Enrollment_LKP](
	[Enrollment_Period_id] [int] NULL,
	[SchoolYear4Digit_int] int NULL,
	[Enrollment_Period_str] [varchar](10) NULL
) ON [PRIMARY]
GO
