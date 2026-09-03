import { Image, ImageStyle, StyleProp, StyleSheet } from 'react-native';

const LOCKUP = require('../assets/brand/geardrop-logo.png');
const MARK = require('../assets/brand/geardrop-mark.png');

export function BrandLogo({ markOnly = false, style }: { markOnly?: boolean; style?: StyleProp<ImageStyle> }) {
  return (
    <Image
      accessibilityLabel="GearDrop"
      accessible
      resizeMode="contain"
      source={markOnly ? MARK : LOCKUP}
      style={[markOnly ? styles.mark : styles.lockup, style]}
    />
  );
}

const styles = StyleSheet.create({
  lockup: {
    width: 160,
    height: 46,
  },
  mark: {
    width: 30,
    height: 30,
  },
});
