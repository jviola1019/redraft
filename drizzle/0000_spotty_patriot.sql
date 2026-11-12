CREATE TABLE `daily_attempts` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`date` text NOT NULL,
	`game_id` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`date`) REFERENCES `daily_challenges`(`date`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`game_id`) REFERENCES `game_runs`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `one_attempt_per_day` ON `daily_attempts` (`owner`,`date`);--> statement-breakpoint
CREATE UNIQUE INDEX `attempt_game` ON `daily_attempts` (`game_id`);--> statement-breakpoint
CREATE TABLE `daily_challenges` (
	`date` text PRIMARY KEY NOT NULL,
	`config` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `game_runs` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`mode` text NOT NULL,
	`challenge_date` text,
	`team` text NOT NULL,
	`year` integer NOT NULL,
	`status` text NOT NULL,
	`revision` integer DEFAULT 0 NOT NULL,
	`state` text NOT NULL,
	`score` real,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL,
	FOREIGN KEY (`challenge_date`) REFERENCES `daily_challenges`(`date`) ON UPDATE no action ON DELETE no action,
	CONSTRAINT "run_mode" CHECK("game_runs"."mode" IN ('historical','daily')),
	CONSTRAINT "run_status" CHECK("game_runs"."status" IN ('drafting','ready','simulating','complete')),
	CONSTRAINT "run_revision" CHECK("game_runs"."revision" >= 0),
	CONSTRAINT "run_challenge" CHECK(("game_runs"."mode" = 'daily' AND "game_runs"."challenge_date" IS NOT NULL) OR ("game_runs"."mode" = 'historical' AND "game_runs"."challenge_date" IS NULL))
);
--> statement-breakpoint
CREATE INDEX `runs_owner_updated` ON `game_runs` (`owner`,`updated_at`);--> statement-breakpoint
CREATE TABLE `daily_leaderboard_entries` (
	`id` text PRIMARY KEY NOT NULL,
	`date` text NOT NULL,
	`owner` text NOT NULL,
	`game_id` text NOT NULL,
	`alias` text NOT NULL,
	`team` text NOT NULL,
	`score` real NOT NULL,
	`model_version` text NOT NULL,
	`dataset_version` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`date`) REFERENCES `daily_challenges`(`date`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`game_id`) REFERENCES `game_runs`(`id`) ON UPDATE no action ON DELETE no action,
	CONSTRAINT "score_bounds" CHECK("daily_leaderboard_entries"."score" BETWEEN 0 AND 100)
);
--> statement-breakpoint
CREATE UNIQUE INDEX `one_score_per_day` ON `daily_leaderboard_entries` (`owner`,`date`);--> statement-breakpoint
CREATE INDEX `leaderboard_date_score` ON `daily_leaderboard_entries` (`date`,`score`);--> statement-breakpoint
CREATE TABLE `rate_windows` (
	`id` text PRIMARY KEY NOT NULL,
	`count` integer DEFAULT 0 NOT NULL,
	`expires_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `rate_expiry` ON `rate_windows` (`expires_at`);--> statement-breakpoint
CREATE TABLE `request_receipts` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`game_id` text NOT NULL,
	`request_hash` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`game_id`) REFERENCES `game_runs`(`id`) ON UPDATE no action ON DELETE no action
);
