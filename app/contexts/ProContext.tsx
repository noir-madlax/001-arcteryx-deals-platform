import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, PropsWithChildren, useCallback, useContext, useEffect, useMemo, useState } from 'react';

const STORAGE_KEY = 'geardrop.pro.v1';

type ProContextValue = {
  isPro: boolean;
  setPro: (next: boolean) => Promise<void>;
};

const ProContext = createContext<ProContextValue | null>(null);

export function ProProvider({ children }: PropsWithChildren) {
  const [isPro, setIsPro] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((value) => setIsPro(value === 'true')).catch(() => setIsPro(false));
  }, []);

  const setPro = useCallback(async (next: boolean) => {
    setIsPro(next);
    await AsyncStorage.setItem(STORAGE_KEY, next ? 'true' : 'false');
  }, []);

  const value = useMemo(() => ({ isPro, setPro }), [isPro, setPro]);
  return <ProContext.Provider value={value}>{children}</ProContext.Provider>;
}

export function usePro() {
  const value = useContext(ProContext);
  if (!value) throw new Error('usePro must be used inside ProProvider');
  return value;
}
