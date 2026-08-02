CREATE DATABASE IF NOT EXISTS code_reviewer
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'code_reviewer'@'localhost'
  IDENTIFIED BY 'code_reviewer_password';

CREATE USER IF NOT EXISTS 'code_reviewer'@'127.0.0.1'
  IDENTIFIED BY 'code_reviewer_password';

ALTER USER 'code_reviewer'@'localhost'
  IDENTIFIED BY 'code_reviewer_password';

ALTER USER 'code_reviewer'@'127.0.0.1'
  IDENTIFIED BY 'code_reviewer_password';

GRANT ALL PRIVILEGES ON code_reviewer.* TO 'code_reviewer'@'localhost';
GRANT ALL PRIVILEGES ON code_reviewer.* TO 'code_reviewer'@'127.0.0.1';

FLUSH PRIVILEGES;

USE code_reviewer;

ALTER TABLE submission_files MODIFY filename VARCHAR(1024) NOT NULL;
ALTER TABLE ast_nodes MODIFY file_path VARCHAR(1024) NOT NULL;
ALTER TABLE static_findings MODIFY file_path VARCHAR(1024) NOT NULL;
ALTER TABLE security_findings MODIFY file_path VARCHAR(1024) NOT NULL;
ALTER TABLE complexity_metrics MODIFY file_path VARCHAR(1024) NOT NULL;
ALTER TABLE feedback MODIFY file_path VARCHAR(1024) NULL;
