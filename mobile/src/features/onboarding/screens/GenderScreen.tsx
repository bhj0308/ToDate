import { StyleSheet, View } from "react-native";

import { GENDERS } from "../content";
import { OnboardingLayout } from "../components/OnboardingLayout";
import { SelectRow } from "../components/SelectRow";
import { useOnboarding } from "../OnboardingContext";
import { useStep } from "../useStep";
import type { OnboardingScreenProps } from "../../../navigation/types";

export function GenderScreen({ navigation }: OnboardingScreenProps<"Gender">) {
  const { answers, setAnswer } = useOnboarding();
  const step = useStep("Gender");

  return (
    <OnboardingLayout
      eyebrow="Application"
      title="Select your gender."
      subtitle="Choose the option that represents you."
      {...step}
      ctaDisabled={!answers.gender}
      onCta={() => navigation.navigate("InterestedIn")}
      onBack={navigation.goBack}
    >
      <View style={styles.list}>
        {GENDERS.map((gender) => (
          <SelectRow
            key={gender}
            label={gender}
            selected={answers.gender === gender}
            onPress={() => setAnswer("gender", gender)}
          />
        ))}
      </View>
    </OnboardingLayout>
  );
}

const styles = StyleSheet.create({ list: { gap: 12 } });
