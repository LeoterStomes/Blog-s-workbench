import assert from 'node:assert/strict';
import test from 'node:test';

test('confirmation snapshot survives pending state being cleared', async () => {
  const { snapshotConfirmation } = await import(
    '../../astro-blog/src/lib/confirmationState.mjs'
  );
  let pending = {
    confirmationId: 'confirm-1',
    actions: [{ callId: 'call-1', tool: 'delete_article' }],
  };

  const snapshot = snapshotConfirmation(pending);
  pending = null;

  assert.equal(snapshot?.confirmationId, 'confirm-1');
  assert.equal(snapshot?.actions[0]?.tool, 'delete_article');
});

test('empty confirmation snapshot is null', async () => {
  const { snapshotConfirmation } = await import(
    '../../astro-blog/src/lib/confirmationState.mjs'
  );
  assert.equal(snapshotConfirmation(null), null);
});
