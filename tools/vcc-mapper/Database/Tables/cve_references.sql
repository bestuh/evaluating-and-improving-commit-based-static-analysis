CREATE TABLE cve_references (
cve_id VARCHAR(50)
, reference VARCHAR(256)
);

ALTER TABLE cve_references ADD FOREIGN KEY (cve_id)
REFERENCES cve(cve_id);

ALTER TABLE cve_references MODIFY reference VARCHAR(512);