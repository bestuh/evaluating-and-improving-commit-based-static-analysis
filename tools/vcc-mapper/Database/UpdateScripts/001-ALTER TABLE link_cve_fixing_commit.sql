ALTER TABLE link_cve_fixing_commit ADD COLUMN mapping_type VARCHAR(50) NOT NULL;

ALTER TABLE link_cve_fixing_commit ADD CONSTRAINT FK_link_cve_fixing_commit_ref_mapping_types_mapping_type FOREIGN KEY (mapping_type)
REFERENCES ref_mapping_types(id)