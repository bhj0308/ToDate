import { StyleSheet, View } from "react-native";

import { DATING_GOALS } from "../content";
import { Chip } from "../components/Chip";
import { OnboardingLayout } from "../components/OnboardingLayout";
import { useOnboarding } from "../OnboardingContext";
import { useStep } from "../useStep";
import type { OnboardingScreenProps } from "../../../navigation/types";

export function DatingGoalsScreen({ navigation }: OnboardingScreenProps<"DatingGoals">) {
  const { answers, setAnswer } = useOnboarding();
  const step = useStep("DatingGoals");
  const selected = answers.datingGoals;

  const toggle = (goal: string) =>
    setAnswer(
      "datingGoals",
      selected.includes(goal) ? selected.filter((g) => g !== goal) : [...selected, goal],
    );

  return (
    <OnboardingLayout
      eyebrow="Application"
      title="What brings you to ToDate?"
      subtitle="Choose the option(s) that best describes what you're genuinely hoping to find."
      {...step}
      ctaDisabled={selected.length === 0}
      onCta={() => navigation.navigate("Intent")}
      onBack={navigation.goBack}
    >
      <View style={styles.wrap}>
        {DATING_GOALS.map((goal) => (
          <Chip
            key={goal}
            label={goal}
            selected={selected.includes(goal)}
            onPress={() => toggle(goal)}
          />
        ))}
      </View>
    </OnboardingLayout>
  );
}

const styles = StyleSheet.create({
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
});
