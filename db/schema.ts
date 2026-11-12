import { sql } from 'drizzle-orm';
import { sqliteTable, text, integer, real, index, uniqueIndex, check } from 'drizzle-orm/sqlite-core';
export const dailyChallenges = sqliteTable('daily_challenges', {
  date: text('date').primaryKey(), config: text('config').notNull(), createdAt: text('created_at').notNull(),
});
export const gameRuns = sqliteTable('game_runs', {
  id: text('id').primaryKey(), owner: text('owner').notNull(), mode: text('mode').notNull(),
  challengeDate: text('challenge_date').references(() => dailyChallenges.date),
  team: text('team').notNull(), year: integer('year').notNull(), status: text('status').notNull(),
  revision: integer('revision').notNull().default(0), state: text('state').notNull(), score: real('score'),
  createdAt: text('created_at').notNull(), updatedAt: text('updated_at').notNull(),
}, t => [index('runs_owner_updated').on(t.owner,t.updatedAt),
  check('run_mode',sql`${t.mode} IN ('historical','daily')`),
  check('run_status',sql`${t.status} IN ('drafting','ready','simulating','complete')`),
  check('run_revision',sql`${t.revision} >= 0`),
  check('run_challenge',sql`(${t.mode} = 'daily' AND ${t.challengeDate} IS NOT NULL) OR (${t.mode} = 'historical' AND ${t.challengeDate} IS NULL)`)]);
export const dailyAttempts = sqliteTable('daily_attempts', {
  id: text('id').primaryKey(), owner: text('owner').notNull(), date: text('date').notNull().references(() => dailyChallenges.date),
  gameId: text('game_id').notNull().references(() => gameRuns.id), createdAt: text('created_at').notNull(),
}, t => [uniqueIndex('one_attempt_per_day').on(t.owner,t.date),uniqueIndex('attempt_game').on(t.gameId)]);
export const leaderboard = sqliteTable('daily_leaderboard_entries', {
  id: text('id').primaryKey(), date: text('date').notNull().references(() => dailyChallenges.date),
  owner: text('owner').notNull(), gameId: text('game_id').notNull().references(() => gameRuns.id),
  alias: text('alias').notNull(), team: text('team').notNull(), score: real('score').notNull(),
  modelVersion: text('model_version').notNull(), datasetVersion: text('dataset_version').notNull(), createdAt: text('created_at').notNull(),
}, t => [uniqueIndex('one_score_per_day').on(t.owner,t.date),index('leaderboard_date_score').on(t.date,t.score),check('score_bounds',sql`${t.score} BETWEEN 0 AND 100`)]);
export const receipts = sqliteTable('request_receipts', {
  id: text('id').primaryKey(), owner: text('owner').notNull(), gameId: text('game_id').notNull().references(() => gameRuns.id),
  requestHash: text('request_hash').notNull(), createdAt: text('created_at').notNull(),
});
export const rateWindows = sqliteTable('rate_windows', {
  id: text('id').primaryKey(), count: integer('count').notNull().default(0), expiresAt: integer('expires_at').notNull(),
},t=>[index('rate_expiry').on(t.expiresAt)]);
