CREATE TABLE custom.schoolmint_FactDailyStatus(
	ID serial NOT NULL,
	School varchar(500) NULL,
	SchoolID varchar(50) NULL,
	SchoolYear4DigitEnd varchar(4) NULL,
	GradeLevel varchar(500) NULL,
	StatusName varchar(128) NULL,
	CountInStatus int NULL,
	ReportDate date NOT NULL,
	Month_Boolean  boolean NOT NULL DEFAULT (false),
	Sunday_Boolean  boolean NOT NULL DEFAULT (false)
)
