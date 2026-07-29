import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";

import { colors } from "../theme/colors";

type PrimaryButtonProps = {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: "primary" | "secondary";
};

export function PrimaryButton({
  title,
  onPress,
  disabled,
  loading,
  variant = "primary",
}: PrimaryButtonProps) {
  const isDisabled = disabled || loading;
  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.base,
        variant === "secondary" ? styles.secondary : styles.primary,
        isDisabled && styles.disabled,
        pressed && !isDisabled && styles.pressed,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={variant === "secondary" ? colors.primary : "#fff"} />
      ) : (
        <Text style={variant === "secondary" ? styles.secondaryText : styles.primaryText}>
          {title}
        </Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  primary: {
    backgroundColor: colors.primary,
  },
  secondary: {
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: colors.primary,
  },
  disabled: {
    opacity: 0.5,
  },
  pressed: {
    opacity: 0.85,
  },
  primaryText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 16,
  },
  secondaryText: {
    color: colors.primary,
    fontWeight: "600",
    fontSize: 16,
  },
});
