import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { colors } from "../theme/colors";

type StatusMessageProps = {
  variant: "loading" | "error" | "empty";
  message?: string;
};

const DEFAULT_MESSAGE: Record<StatusMessageProps["variant"], string> = {
  loading: "Loading…",
  error: "Something went wrong.",
  empty: "Nothing here yet.",
};

export function StatusMessage({ variant, message }: StatusMessageProps) {
  return (
    <View style={styles.container}>
      {variant === "loading" && <ActivityIndicator color={colors.primary} />}
      <Text style={variant === "error" ? styles.errorText : styles.text}>
        {message ?? DEFAULT_MESSAGE[variant]}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 24,
    alignItems: "center",
    gap: 8,
  },
  text: {
    color: colors.textMuted,
    fontSize: 14,
    textAlign: "center",
  },
  errorText: {
    color: colors.danger,
    fontSize: 14,
    textAlign: "center",
  },
});
