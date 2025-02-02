CREATE TABLE `cve` (
  `cve_id` varchar(50) NOT NULL,
  `cve_date_created` datetime DEFAULT NULL,
  `cve_date_last_modified` datetime DEFAULT NULL,
  `cve_cwe_id` varchar(50) DEFAULT NULL,
  `cve_cvss_score` varchar(10) DEFAULT NULL,
  `cve_cvss_time` datetime DEFAULT NULL,
  `cve_cvss_vector` varchar(100) DEFAULT NULL,
  `cve_summary` varchar(5000) DEFAULT NULL,
  PRIMARY KEY (`cve_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `commit` (
  `com_sha` varchar(50) NOT NULL,
  `com_date_commited` datetime DEFAULT NULL,
  `com_author` varchar(256) DEFAULT NULL,
  `com_message` varchar(5000) DEFAULT NULL,
  `com_config_code` varchar(50) NOT NULL,
  PRIMARY KEY (`com_sha`,`com_config_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `cve_config_code` (
  `cve_id` varchar(50) DEFAULT NULL,
  `config_code` varchar(256) DEFAULT NULL,
  KEY `cve_id` (`cve_id`),
  CONSTRAINT `cve_config_code_ibfk_1` FOREIGN KEY (`cve_id`) REFERENCES `cve` (`cve_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `cve_product` (
  `cve_id` varchar(50) DEFAULT NULL,
  `product` varchar(256) DEFAULT NULL,
  KEY `cve_id` (`cve_id`),
  CONSTRAINT `cve_product_ibfk_1` FOREIGN KEY (`cve_id`) REFERENCES `cve` (`cve_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `cve_references` (
  `cve_id` varchar(50) DEFAULT NULL,
  `reference` varchar(512) DEFAULT NULL,
  KEY `cve_id` (`cve_id`),
  CONSTRAINT `cve_references_ibfk_1` FOREIGN KEY (`cve_id`) REFERENCES `cve` (`cve_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `cve_vulnerable` (
  `cve_id` varchar(50) DEFAULT NULL,
  `version` varchar(256) DEFAULT NULL,
  KEY `cve_id` (`cve_id`),
  CONSTRAINT `cve_vulnerable_ibfk_1` FOREIGN KEY (`cve_id`) REFERENCES `cve` (`cve_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `link_cve_fixing_commit` (
  `cve_id` varchar(50) DEFAULT NULL,
  `com_sha` varchar(50) DEFAULT NULL,
  `com_config_code` varchar(50) DEFAULT NULL,
  `mapping_type` varchar(50) NOT NULL,
  `manual_delete` int(11) NOT NULL DEFAULT '0',
  KEY `cve_id` (`cve_id`),
  KEY `com_sha` (`com_sha`),
  KEY `FK_link_cve_fixing_commit_ref_mapping_types_mapping_type` (`mapping_type`),
  CONSTRAINT `FK_link_cve_fixing_commit_ref_mapping_types_mapping_type` FOREIGN KEY (`mapping_type`) REFERENCES `ref_mapping_types` (`id`),
  CONSTRAINT `link_cve_fixing_commit_ibfk_1` FOREIGN KEY (`cve_id`) REFERENCES `cve` (`cve_id`),
  CONSTRAINT `link_cve_fixing_commit_ibfk_2` FOREIGN KEY (`com_sha`) REFERENCES `commit` (`com_sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `ref_mapping_types` (
  `id` varchar(50) NOT NULL,
  `description_english` varchar(250) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO ref_mapping_types(id, description_english)
VALUES ('', 'Empty entry')
, ('TypeCommonID', 'Mapping obtained by linking a commen identifier (e.g. bug ID)')
, ('TypeCommitSha', 'Commit identifier (sha) referenced in CVE entry')
, ('TypeCVEID', 'CVE ID referenced in Commit message');