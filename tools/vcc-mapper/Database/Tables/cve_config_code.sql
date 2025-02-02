DROP TABLE IF EXISTS cve_config_code;

CREATE TABLE cve_config_code (
cve_id VARCHAR(50)
, config_code VARCHAR(256)
);

ALTER TABLE cve_config_code ADD FOREIGN KEY (cve_id)
REFERENCES cve(cve_id);