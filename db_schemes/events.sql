CREATE TABLE `events` (
	`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
	`event_id` CHAR(66) NOT NULL COLLATE 'utf8mb4_0900_ai_ci',
	`kind` INT(10) NOT NULL,
	`addr` CHAR(42) NOT NULL COLLATE 'utf8mb4_0900_ai_ci',
	`data` TEXT NOT NULL COLLATE 'utf8mb4_0900_ai_ci',
	`timestamp` INT(10) NOT NULL,
	PRIMARY KEY (`id`) USING BTREE,
	UNIQUE INDEX `event_id` (`event_id`) USING BTREE,
	INDEX `addr` (`addr`) USING BTREE,
	INDEX `kind` (`kind`) USING BTREE
)
COLLATE='utf8mb4_0900_ai_ci'
ENGINE=InnoDB
;
