import { useMemo, useState } from 'react';
import { ActivityIndicator, Modal, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { cleanName, formatPrice } from '../lib/catalog';
import { colors, radii } from '../lib/theme';
import type { Product } from '../lib/types';

type Props = {
  visible: boolean;
  product: Product;
  onClose: () => void;
  onSubmit: (email: string, target: number | null) => Promise<void>;
};

export function AlertModal({ visible, product, onClose, onSubmit }: Props) {
  const [email, setEmail] = useState('');
  const [target, setTarget] = useState(() => String(Math.floor(product.sale_price * 0.85)));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const suggested = useMemo(() => Math.floor(product.sale_price * 0.85), [product.sale_price]);

  async function submit() {
    const normalizedEmail = email.trim().toLowerCase();
    const parsedTarget = target.trim() ? Number(target) : null;
    setError(null);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setError('Enter a valid email address.');
      return;
    }
    if (parsedTarget !== null && (!Number.isFinite(parsedTarget) || parsedTarget <= 0 || parsedTarget >= product.sale_price)) {
      setError(`Target must be below ${formatPrice(product.sale_price, product.symbol)}.`);
      return;
    }
    setBusy(true);
    try {
      await onSubmit(normalizedEmail, parsedTarget);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <Text style={styles.title}>Price alert</Text>
          <Text style={styles.sub}>{cleanName(product.full_name || product.model)}</Text>
          <Text style={styles.current}>Current {formatPrice(product.sale_price, product.symbol)} · suggested target {formatPrice(suggested, product.symbol)}</Text>
          <TextInput style={styles.input} value={email} onChangeText={setEmail} placeholder="you@example.com" autoCapitalize="none" keyboardType="email-address" />
          <View style={styles.priceInputRow}>
            <Text style={styles.symbol}>{product.symbol}</Text>
            <TextInput style={[styles.input, styles.priceInput]} value={target} onChangeText={setTarget} keyboardType="decimal-pad" placeholder={String(suggested)} />
          </View>
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <View style={styles.actions}>
            <Pressable style={[styles.button, styles.secondary]} onPress={onClose} disabled={busy}>
              <Text style={styles.secondaryText}>Cancel</Text>
            </Pressable>
            <Pressable style={[styles.button, styles.primary]} onPress={submit} disabled={busy}>
              {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryText}>Save alert</Text>}
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(24,23,20,0.36)',
  },
  card: {
    gap: 12,
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    backgroundColor: colors.surface,
    padding: 20,
    paddingBottom: 34,
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: '900',
  },
  sub: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: '700',
  },
  current: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: '600',
  },
  input: {
    minHeight: 48,
    borderRadius: radii.sm,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    backgroundColor: colors.bg,
    paddingHorizontal: 12,
    color: colors.ink,
    fontSize: 16,
  },
  priceInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  symbol: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: '900',
  },
  priceInput: {
    flex: 1,
  },
  error: {
    color: colors.danger,
    fontSize: 13,
    fontWeight: '700',
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
  },
  button: {
    flex: 1,
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.sm,
  },
  secondary: {
    backgroundColor: colors.surfaceAlt,
  },
  primary: {
    backgroundColor: colors.ink,
  },
  secondaryText: {
    color: colors.ink,
    fontWeight: '800',
  },
  primaryText: {
    color: '#fff',
    fontWeight: '900',
  },
});
