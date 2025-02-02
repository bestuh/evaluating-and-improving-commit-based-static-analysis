
CREATE TABLE ref_mapping_types(
	id VARCHAR(50) PRIMARY KEY
    , description_english VARCHAR(250) NULL
);

INSERT INTO ref_mapping_types(id, description_english)
VALUES ('', 'Empty entry')
, ('TypeCommonID', 'Mapping obtained by linking a commen identifier (e.g. bug ID)')
, ('TypeCommitSha', 'Commit identifier (sha) referenced in CVE entry')
, ('TypeCVEID', 'CVE ID referenced in Commit message')