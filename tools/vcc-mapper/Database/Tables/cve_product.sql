CREATE TABLE cve_product (
cve_id VARCHAR(50)
, product VARCHAR(256)
);

ALTER TABLE cve_product ADD FOREIGN KEY (cve_id)
REFERENCES cve(cve_id);