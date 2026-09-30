import { LinearGradient } from "expo-linear-gradient";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors } from "../../../theme/colors";

type Props = {
  label: string;
  selected: boolean;
  onPress: () => void;
  /** "radio" outlines the row (gender step); "fill" fills it gold (interested-in step). */
  variant?: "radio" | "fill";
};

export function SelectRow({ label, selected, onPress, variant = "radio" }: Props) {
  if (variant === "fill") {
    return (
      <Pressable onPress={onPress} style={({ pressed }) => [pressed && styles.pressed]}>
        {selected ? (
          <LinearGradient
            colors={[colors.secondaryBright, colors.secondaryDim]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.row}
          >
            <Text style={[styles.centered, styles.labelOnGold]}>{label}</Text>
          </LinearGradient>
        ) : (
          <View style={[styles.row, styles.rowUnselected]}>
            <Text style={[styles.centered, styles.label]}>{label}</Text>
          </View>
        )}
      </Pressable>
    );
  }

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [pressed && styles.pressed]}>
      <View style={[styles.row, styles.rowRadio, selected && styles.rowRadioSelected]}>
        <Text style={[styles.label, selected && styles.labelSelected]}>{label}</Text>
        <View style={[styles.radio, selected && styles.radioSelected]}>
          {selected && <View style={styles.radioDot} />}
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    overflow: "hidden",
  },
  rowUnselected: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
  rowRadio: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
  rowRadioSelected: { backgroundColor: colors.surfaceRaised, borderColor: colors.secondaryDim },
  centered: { flex: 1, textAlign: "center" },
  label: { color: colors.textMuted, fontSize: 16 },
  labelSelected: { color: colors.text, fontWeight: "600" },
  labelOnGold: { color: colors.onSecondary, fontSize: 16, fontWeight: "600" },
  radio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1,
    borderColor: colors.textSubtle,
    alignItems: "center",
    justifyContent: "center",
  },
  radioSelected: { borderColor: colors.secondaryDim },
  radioDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: colors.secondaryDim },
  pressed: { opacity: 0.85 },
});
