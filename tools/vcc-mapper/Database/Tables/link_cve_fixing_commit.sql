CREATE TABLE link_cve_fixing_commit(
cve_id VARCHAR(50)
, com_sha VARCHAR(50)
, com_config_code VARCHAR(50)
);

ALTER TABLE link_cve_fixing_commit ADD FOREIGN KEY (cve_id)
REFERENCES cve(cve_id);

ALTER TABLE link_cve_fixing_commit ADD FOREIGN KEY (com_sha)
REFERENCES commit(com_sha);

ALTER TABLE link_cve_fixing_commit ADD FOREIGN KEY (com_config_code)
REFERENCES commit(com_config_code);
