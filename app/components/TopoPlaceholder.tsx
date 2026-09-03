import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';

import { colors, radii } from '../lib/theme';

type Props = {
  label?: string;
  showLabel?: boolean;
};

export function TopoPlaceholder({ label = 'Gear', showLabel = true }: Props) {
  return (
    <View style={styles.wrap}>
      <Svg style={StyleSheet.absoluteFill} viewBox="0 0 120 120" preserveAspectRatio="none">
        {[18, 32, 46, 60, 74, 88].map((radius) => (
          <Circle key={radius} cx="74" cy="44" r={radius} fill="none" stroke={colors.photoTopo} strokeWidth={1.5} />
        ))}
      </Svg>
      {showLabel && label ? (
        <View style={styles.tag}>
          <Text style={styles.tagText} numberOfLines={1}>
            {label}
          </Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flex: 1,
    overflow: 'hidden',
    borderRadius: radii.lg,
    backgroundColor: colors.photo,
  },
  tag: {
    position: 'absolute',
    left: 7,
    bottom: 6,
    maxWidth: '78%',
  },
  tagText: {
    color: colors.photoCat,
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.7,
    textTransform: 'uppercase',
  },
});
