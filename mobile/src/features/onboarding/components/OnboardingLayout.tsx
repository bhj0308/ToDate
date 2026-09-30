import { LinearGradient } from "expo-linear-gradient";
import type { ReactNode } from "react";
import { Platform, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { colors } from "../../../theme/colors";
import { ProgressBar } from "./ProgressBar";

/**
 * The shell every application step shares: warm gradient, back control, eyebrow,
 * serif heading, body copy, scrollable content, progress and a pinned CTA.
 *
 * NOTE: the heading font is the platform serif as a stand-in. The Figma uses a
 * specific display serif that hasn't been handed over yet — see design/tokens.md.
 */
export const headingFont = Platform.select({ ios: "Georgia", default: "serif" });

type Props = {
  eyebrow: string;
  title: string;
  subtitle?: string;
  step: number;
  totalSteps: number;
  ctaLabel?: string;
  ctaDisabled?: boolean;
  ctaLoading?: boolean;
  onCta: () => void;
  onBack?: () => void;
  /** Set false while a child is handling its own vertical gesture (drag to reorder). */
  scrollEnabled?: boolean;
  children: ReactNode;
};

export function OnboardingLayout({
  eyebrow,
  title,
  subtitle,
  step,
  totalSteps,
  ctaLabel = "Continue",
  ctaDisabled,
  ctaLoading,
  onCta,
  onBack,
  scrollEnabled = true,
  children,
}: Props) {
  return (
    <LinearGradient
      colors={[colors.backgroundTop, colors.backgroundBottom]}
      style={styles.flex}
    >
      <SafeAreaView style={styles.flex} edges={["top", "bottom"]}>
        <View style={styles.header}>
          {onBack && (
            <Pressable onPress={onBack} style={styles.back} hitSlop={12}>
              <Text style={styles.backGlyph}>‹</Text>
            </Pressable>
          )}
        </View>

        <ScrollView
          style={styles.flex}
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          scrollEnabled={scrollEnabled}
        >
          <Text style={styles.eyebrow}>{eyebrow}</Text>
          <Text style={styles.title}>{title}</Text>
          {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
          <View style={styles.body}>{children}</View>
        </ScrollView>

        <View style={styles.footer}>
          <ProgressBar step={step} total={totalSteps} />
          <View style={{ height: 16 }} />
          <PrimaryButton
            title={ctaLabel}
            onPress={onCta}
            disabled={ctaDisabled}
            loading={ctaLoading}
          />
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  header: { paddingHorizontal: 24, paddingTop: 8, height: 52, justifyContent: "center" },
  back: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
  backGlyph: { color: colors.text, fontSize: 24, lineHeight: 26, marginTop: -2 },
  content: { paddingHorizontal: 24, paddingBottom: 24 },
  eyebrow: {
    color: colors.textSubtle,
    fontSize: 12,
    letterSpacing: 3,
    textTransform: "uppercase",
    marginBottom: 12,
  },
  title: { color: colors.text, fontSize: 30, lineHeight: 38, fontFamily: headingFont },
  subtitle: { color: colors.textMuted, fontSize: 16, lineHeight: 23, marginTop: 10 },
  body: { marginTop: 24 },
  footer: { paddingHorizontal: 24, paddingBottom: 12, paddingTop: 8 },
});
