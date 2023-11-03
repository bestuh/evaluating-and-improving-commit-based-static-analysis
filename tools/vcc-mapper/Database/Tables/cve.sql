CREATE TABLE cve (
cve_id VARCHAR(50) PRIMARY KEY
, cve_date_created DATETIME
, cve_date_last_modified DATETIME
, cve_cwe_id VARCHAR(50)
, cve_cvss_score VARCHAR(10)
, cve_cvss_time DATETIME
, cve_cvss_vector VARCHAR(100)
);

ALTER TABLE cve ADD cve_summary VARCHAR(5000);