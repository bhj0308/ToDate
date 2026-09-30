import { StyleSheet, View } from "react-native";

import { INTERESTED_IN } from "../content";
import { OnboardingLayout } from "../components/OnboardingLayout";
import { SelectRow } from "../components/SelectRow";
import { useOnboarding } from "../OnboardingContext";
import { useStep } from "../useStep";
import type { OnboardingScreenProps } from "../../../navigation/types";

export function InterestedInScreen({ navigation }: OnboardingScreenProps<"InterestedIn">) {
  const { answers, setAnswer } = useOnboarding();
  const step = useStep("InterestedIn");
  const selected = answers.interestedIn;

  const toggle = (option: string) =>
    setAnswer(
      "interestedIn",
      selected.includes(option) ? selected.filter((o) => o !== option) : [...selected, option],
    );

  return (
    <OnboardingLayout
      eyebrow="Application"
      title="Who are you interested in?"
      subtitle="Tell us who you're looking to connect with. You can select more than one option."
      {...step}
      ctaDisabled={selected.length === 0}
      onCta={() => navigation.navigate("FirstName")}
      onBack={navigation.goBack}
    >
      <View style={styles.list}>
        {INTERESTED_IN.map((option) => (
          <SelectRow
            key={option}
            label={option}
            variant="fill"
            selected={selected.includes(option)}
            onPress={() => toggle(option)}
          />
        ))}
      </View>
    </OnboardingLayout>
  );
}

const styles = StyleSheet.create({ list: { gap: 12 } });
