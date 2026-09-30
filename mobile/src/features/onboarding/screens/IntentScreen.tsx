import { StyleSheet, Text, View } from "react-native";

import { INTENTS, INTENT_WARNING, LOW_INTENT_OPTIONS } from "../content";
import { Chip } from "../components/Chip";
import { OnboardingLayout } from "../components/OnboardingLayout";
import { useOnboarding } from "../OnboardingContext";
import { useStep } from "../useStep";
import { colors } from "../../../theme/colors";
import type { OnboardingScreenProps } from "../../../navigation/types";

export function IntentScreen({ navigation }: OnboardingScreenProps<"Intent">) {
  const { answers, setAnswer } = useOnboarding();
  const step = useStep("Intent");
  const selected = answers.intents;

  const toggle = (intent: string) =>
    setAnswer(
      "intents",
      selected.includes(intent) ? selected.filter((i) => i !== intent) : [...selected, intent],
    );

  // Designer's rule: picking either of the last two shows the community warning.
  // It's a warning, not a block — Continue stays enabled.
  const showWarning = selected.some((i) => LOW_INTENT_OPTIONS.includes(i as never));

  return (
    <OnboardingLayout
      eyebrow="Application"
      title="Which best describes you?"
      subtitle="We're building a community of people who are here for the right reasons. Choose the option(s) that resonate with you."
      {...step}
      ctaDisabled={selected.length === 0}
      onCta={() => navigation.navigate("Gender")}
      onBack={navigation.goBack}
    >
      <View style={styles.list}>
        {INTENTS.map((intent) => (
          <Chip
            key={intent}
            label={intent}
            selected={selected.includes(intent)}
            onPress={() => toggle(intent)}
          />
        ))}
      </View>
      {showWarning && (
        <View style={styles.warning}>
          <Text style={styles.warningText}>{INTENT_WARNING}</Text>
        </View>
      )}
    </OnboardingLayout>
  );
}

const styles = StyleSheet.create({
  list: { alignItems: "flex-start", gap: 12 },
  warning: {
    marginTop: 20,
    borderWidth: 1,
    borderColor: colors.danger,
    borderRadius: 8,
    padding: 14,
  },
  warningText: { color: colors.textMuted, fontSize: 14, lineHeight: 21 },
});
