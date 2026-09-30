import { StyleSheet, View } from "react-native";

import { colors } from "../../../theme/colors";

export function ProgressBar({ step, total }: { step: number; total: number }) {
  const pct = Math.max(0, Math.min(1, step / total));
  return (
    <View style={styles.track}>
      <View style={[styles.fill, { width: `${pct * 100}%` }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  track: { height: 4, borderRadius: 2, backgroundColor: colors.progressTrack, overflow: "hidden" },
  fill: { height: 4, borderRadius: 2, backgroundColor: colors.secondary },
});
