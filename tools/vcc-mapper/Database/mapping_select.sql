SELECT DISTINCT cve_id, com_sha
FROM cve
INNER JOIN cve_config_code ON cve_config_code.cve_id = cve.cve_id
INNER JOIN link_cve_fixing_commit ON link_cve_fixing_commit.cve_id =  cve.cve_id and link_cve_fixing_commit.com_config_code = cve_config_code.config_code
INNER JOIN commit ON commit.com_sha = link_cve_fixing_commit.com_sha AND commit.com_config_code = link_cve_fixing_commit.com_config_code
WHERE cve_config_code.config_code = 'firefox'
ORDER BY cve_date_created DESC;
