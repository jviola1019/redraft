import test from 'node:test';
import assert from 'node:assert/strict';
import { HttpError, MAX_JSON_BODY_BYTES, readJsonBody } from '../lib/request-body';
const request = (body: BodyInit | null, headers: Record<string, string> = {}) => new Request('https://redraft.example/api/game', {
  method: 'POST', body, headers: { 'content-type': 'application/json', ...headers },
});
const status = (expected: number) => (error: unknown) => error instanceof HttpError && error.status === expected;

test('JSON contract accepts same-origin JSON and media-type parameters', async () => {
  assert.deepEqual(await readJsonBody(request('{"action":"save"}', {
    origin: 'https://redraft.example', 'content-type': 'Application/JSON; charset=utf-8',
  })), { action: 'save' });
});
test('JSON contract rejects unsupported media types and malformed documents', async () => {
  await assert.rejects(readJsonBody(request('{}', { 'content-type': 'application/jsonx' })), status(415));
  await assert.rejects(readJsonBody(request('{')), status(400));
  await assert.rejects(readJsonBody(request(new Uint8Array([123, 34, 120, 34, 58, 34, 255, 34, 125]))), status(400));
  await assert.rejects(readJsonBody(request(null)), status(400));
});
test('JSON contract preserves cross-origin checks', async () => {
  await assert.rejects(readJsonBody(request('{}', { origin: 'https://other.example' })), status(403));
  await assert.rejects(readJsonBody(request('{}', { 'sec-fetch-site': 'cross-site' })), status(403));
});
test('JSON byte budget enforces actual bytes independently of declared size', async () => {
  const exact = JSON.stringify('x'.repeat(MAX_JSON_BODY_BYTES - 2));
  assert.equal((await readJsonBody(request(exact)) as string).length, MAX_JSON_BODY_BYTES - 2);
  await assert.rejects(readJsonBody(request(exact + ' ')), status(413));
  await assert.rejects(readJsonBody(request('{}', { 'content-length': String(MAX_JSON_BODY_BYTES + 1) })), status(413));
  await assert.rejects(readJsonBody(request(JSON.stringify('é'.repeat(MAX_JSON_BODY_BYTES / 2)))), status(413));
});
