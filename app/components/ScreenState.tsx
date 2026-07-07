import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { colors } from '../lib/theme';

type Props = {
  title?: string;
  body?: string;
  loading?: boolean;
};

export function ScreenState({ title = 'Loading', body, loading = false }: Props) {
  return (
    <View style={styles.wrap}>
      {loading ? <ActivityIndicator color={colors.accent} /> : null}
      <Text style={styles.title}>{title}</Text>
      {body ? <Text style={styles.body}>{body}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    padding: 28,
    backgroundColor: colors.bg,
  },
  title: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: '700',
    textAlign: 'center',
  },
  body: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
});
