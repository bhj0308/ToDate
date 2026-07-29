import type { ReactNode } from "react";
import { ScrollView, StyleSheet, View, type StyleProp, type ViewStyle } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { colors } from "../theme/colors";

type ScreenProps = {
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
  /** Renders content inside a ScrollView. Defaults to true. */
  scroll?: boolean;
};

/** Shared screen shell: safe-area + consistent padding + optional scroll. */
export function Screen({ children, style, scroll = true }: ScreenProps) {
  return (
    <SafeAreaView style={styles.safeArea} edges={["top", "bottom"]}>
      {scroll ? (
        <ScrollView style={styles.scroll} contentContainerStyle={[styles.content, style]}>
          {children}
        </ScrollView>
      ) : (
        <View style={[styles.content, styles.flex, style]}>{children}</View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scroll: {
    flex: 1,
  },
  flex: {
    flex: 1,
  },
  content: {
    padding: 16,
    gap: 12,
  },
});
