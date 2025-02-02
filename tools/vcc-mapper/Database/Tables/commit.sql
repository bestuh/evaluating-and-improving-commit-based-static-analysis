DROP TABLE IF EXISTS commit;

CREATE TABLE commit (
com_sha VARCHAR(50) 
, com_date_commited DATETIME
, com_author VARCHAR(256)
, com_message VARCHAR(5000)
, com_config_code VARCHAR(50) 
, PRIMARY KEY(com_sha, com_config_code)
);

