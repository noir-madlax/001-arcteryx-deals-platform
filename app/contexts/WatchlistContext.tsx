import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, PropsWithChildren, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { usePro } from './ProContext';
import { softImpact } from '../lib/actions';
import type { Product, WatchEntry } from '../lib/types';
import { FREE_WATCHLIST_LIMIT, parseWatchEntries, setWatchAlertTarget, toggleWatchEntry, WATCHLIST_STORAGE_KEY } from '../lib/watchlist';

type WatchlistContextValue = {
  entries: WatchEntry[];
  freeLimit: number;
  isSaved: (skuId?: string | null) => boolean;
  getEntry: (skuId?: string | null) => WatchEntry | undefined;
  toggle: (product: Product) => Promise<boolean>;
  setAlertTarget: (product: Product, target: number | null) => Promise<void>;
  remove: (skuId: string) => Promise<void>;
};

const WatchlistContext = createContext<WatchlistContextValue | null>(null);

export function WatchlistProvider({ children }: PropsWithChildren) {
  const { isPro } = usePro();
  const [entries, setEntries] = useState<WatchEntry[]>([]);

  useEffect(() => {
    AsyncStorage.getItem(WATCHLIST_STORAGE_KEY).then((raw) => setEntries(parseWatchEntries(raw))).catch(() => setEntries([]));
  }, []);

  const persist = useCallback(async (next: WatchEntry[]) => {
    setEntries(next);
    await AsyncStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(next));
  }, []);

  const isSaved = useCallback((skuId?: string | null) => Boolean(skuId && entries.some((entry) => entry.skuId === skuId)), [entries]);
  const getEntry = useCallback((skuId?: string | null) => (skuId ? entries.find((entry) => entry.skuId === skuId) : undefined), [entries]);

  const toggle = useCallback(
    async (product: Product) => {
      await softImpact();
      const result = toggleWatchEntry(entries, product, isPro);
      if (!result.accepted) return false;
      await persist(result.entries);
      return true;
    },
    [entries, isPro, persist],
  );

  const setAlertTarget = useCallback(
    async (product: Product, target: number | null) => {
      await persist(setWatchAlertTarget(entries, product, target));
    },
    [entries, persist],
  );

  const remove = useCallback(async (skuId: string) => {
    await persist(entries.filter((entry) => entry.skuId !== skuId));
  }, [entries, persist]);

  const value = useMemo(
    () => ({ entries, freeLimit: FREE_WATCHLIST_LIMIT, isSaved, getEntry, toggle, setAlertTarget, remove }),
    [entries, getEntry, isSaved, remove, setAlertTarget, toggle],
  );

  return <WatchlistContext.Provider value={value}>{children}</WatchlistContext.Provider>;
}

export function useWatchlist() {
  const value = useContext(WatchlistContext);
  if (!value) throw new Error('useWatchlist must be used inside WatchlistProvider');
  return value;
}
