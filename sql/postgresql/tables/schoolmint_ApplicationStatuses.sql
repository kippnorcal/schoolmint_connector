CREATE TABLE custom.schoolmint_ApplicationStatuses(
	StatusID int NOT NULL,
	Status varchar(2) NOT NULL,
	StatusName varchar(100) NOT NULL,
	StatusDescription varchar(255) NOT NULL,
	StatusGroupName varchar(100) NOT NULL,
	Application boolean NULL,
	Registration boolean NULL,
	Rank int NULL
)
