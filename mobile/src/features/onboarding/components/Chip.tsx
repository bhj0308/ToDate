import { LinearGradient } from "expo-linear-gradient";
import { Pressable, StyleSheet, Text } from "react-native";

import { colors } from "../../../theme/colors";

/** Wrapping pill used by the goals and intent steps. Gold gradient when selected. */
export function Chip({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
}) {
  const content = (
    <Text style={[styles.label, selected && styles.labelSelected]}>{label}</Text>
  );

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [pressed && styles.pressed]}>
      {selected ? (
        <LinearGradient
          colors={[colors.secondaryBright, colors.secondaryDim]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[styles.chip, styles.chipSelected]}
        >
          {content}
        </LinearGradient>
      ) : (
        <Text style={[styles.chip, styles.label]}>{label}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 11,
    borderRadius: 8,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
  },
  chipSelected: { borderColor: "transparent" },
  label: { color: colors.textMuted, fontSize: 15 },
  // Same weight as unselected on purpose: bolding changes the chip's width and
  // reflows the whole wrapping row under the user's finger.
  labelSelected: { color: colors.onSecondary },
  pressed: { opacity: 0.85 },
});
