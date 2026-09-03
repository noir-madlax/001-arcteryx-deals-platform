import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, PropsWithChildren, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { DEFAULT_REGION, normalizeRegion } from '../lib/catalog';

const STORAGE_KEY = 'geardrop.region.v1';

type RegionContextValue = {
  region: string;
  setRegion: (next: string) => Promise<void>;
};

const RegionContext = createContext<RegionContextValue | null>(null);

export function RegionProvider({ children }: PropsWithChildren) {
  const [region, setRegionState] = useState(DEFAULT_REGION);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((value) => setRegionState(normalizeRegion(value)))
      .catch(() => setRegionState(DEFAULT_REGION));
  }, []);

  const setRegion = useCallback(async (next: string) => {
    const normalized = normalizeRegion(next);
    setRegionState(normalized);
    await AsyncStorage.setItem(STORAGE_KEY, normalized);
  }, []);

  const value = useMemo(() => ({ region, setRegion }), [region, setRegion]);
  return <RegionContext.Provider value={value}>{children}</RegionContext.Provider>;
}

export function useRegion() {
  const value = useContext(RegionContext);
  if (!value) throw new Error('useRegion must be used inside RegionProvider');
  return value;
}
