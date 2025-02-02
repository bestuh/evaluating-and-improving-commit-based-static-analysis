ALTER TABLE link_cve_fixing_commit ADD manual_delete INT NOT NULL DEFAULT 0;


UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2017-7484' AND link_cve_fixing_commit.com_config_code = 'postgres' 
AND link_cve_fixing_commit.com_sha = '553d2ec2710be5ae304c40134643c8f6d754af67';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2018-1052' AND link_cve_fixing_commit.com_config_code = 'postgres' 
AND link_cve_fixing_commit.com_sha = '7ac0069fb880b9b64223f104058c82773321851c';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2018-1058' AND link_cve_fixing_commit.com_config_code = 'postgres' 
AND link_cve_fixing_commit.com_sha = 'a5322ca10fa16bed01e3e3d6c49c0f49c68b5593';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2018-1058' AND link_cve_fixing_commit.com_config_code = 'postgres' 
AND link_cve_fixing_commit.com_sha = '6336b6dfc5c5f7ef746fb7b14c720ef0c2c6a1f1';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2016-5424' AND link_cve_fixing_commit.com_config_code = 'postgres' 
AND link_cve_fixing_commit.com_sha = '8b845520fb0aa50fea7aae44a45cee1b6d87845d';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2012-2655' AND link_cve_fixing_commit.com_config_code = 'postgres' 
AND link_cve_fixing_commit.com_sha = 'ad0009e7be27489f5acc0a36217d9ea8f3db2b14';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2019-1559' AND link_cve_fixing_commit.com_config_code = 'openssl' 
AND link_cve_fixing_commit.com_sha = 'f4800345d95d632d424f9b2725418c0c2ec6f029';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2017-3737' AND link_cve_fixing_commit.com_config_code = 'openssl' 
AND link_cve_fixing_commit.com_sha = '97652f0b3a557876462ef30373ac5eeeaa88b295';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2017-3733' AND link_cve_fixing_commit.com_config_code = 'openssl' 
AND link_cve_fixing_commit.com_sha = '98d132cf6a879faf0147aa83ea0c07ff326260ed';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2016-7053' AND link_cve_fixing_commit.com_config_code = 'openssl' 
AND link_cve_fixing_commit.com_sha = 'a378a46985698bf2576b2990e7faf21f62dd176a';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2016-7055' AND link_cve_fixing_commit.com_config_code = 'openssl' 
AND link_cve_fixing_commit.com_sha = 'dca2e0ee1745ed2d9cba8c29f334f881a58f85dc';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2016-6309' AND link_cve_fixing_commit.com_config_code = 'openssl' 
AND link_cve_fixing_commit.com_sha = '44f206aa9dfd4f226f17d9093732dbece5300aa6';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2016-2109' AND link_cve_fixing_commit.com_config_code = 'openssl' 
AND link_cve_fixing_commit.com_sha = '9f13d4dd5ec420fb2fa0a7b94a6d66bb2700a492';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2014-0224' AND link_cve_fixing_commit.com_config_code = 'openssl' 
AND link_cve_fixing_commit.com_sha = '657da85eea3a5825b2dd25ff25b99ec206c48136';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2015-1793' AND link_cve_fixing_commit.com_config_code = 'openssl' 
AND link_cve_fixing_commit.com_sha = '593e9c638c58e1a510c519db0d024527113330f3';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2014-0224' AND link_cve_fixing_commit.com_config_code = 'openssl' 
AND link_cve_fixing_commit.com_sha = 'fb8d9ddb9dc19d84dffa84932f75e607c8a3ffe6';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2014-0160' AND link_cve_fixing_commit.com_config_code = 'openssl' 
AND link_cve_fixing_commit.com_sha = '6af080acaf57c74e3cd96642f2900fa602407d10';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2012-3489' AND link_cve_fixing_commit.com_config_code = 'postgres' 
AND link_cve_fixing_commit.com_sha = 'adc97d03b92fef50608c21059f0509fa97d314f6';

UPDATE link_cve_fixing_commit
SET manual_delete = 1
WHERE link_cve_fixing_commit.cve_id = 'CVE-2016-2326' AND link_cve_fixing_commit.com_config_code = 'ffmpeg' 
AND link_cve_fixing_commit.com_sha = 'bfd0f42277d1fab7b354f80f5e158e15a75f34ee';





