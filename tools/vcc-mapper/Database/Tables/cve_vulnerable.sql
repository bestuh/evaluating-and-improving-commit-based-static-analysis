CREATE TABLE cve_vulnerable (
cve_id VARCHAR(50)
, version VARCHAR(256)
);

ALTER TABLE cve_vulnerable ADD FOREIGN KEY (cve_id)
REFERENCES cve(cve_id);