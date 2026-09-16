import { useSyncExternalStore } from "react";

import { upgradeRequiredStore } from "../../api/client";

export function useUpgradeRequired(): boolean {
  return useSyncExternalStore(upgradeRequiredStore.subscribe, upgradeRequiredStore.get);
}
