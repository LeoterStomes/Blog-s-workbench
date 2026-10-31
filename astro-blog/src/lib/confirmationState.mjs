export function snapshotConfirmation(confirmation) {
  if (!confirmation?.confirmationId) return null;
  return {
    confirmationId: String(confirmation.confirmationId),
    actions: Array.isArray(confirmation.actions)
      ? confirmation.actions.map(action => ({ ...action }))
      : [],
  };
}
