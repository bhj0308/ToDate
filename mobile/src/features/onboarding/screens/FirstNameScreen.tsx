import { StyleSheet, Text, TextInput, View } from "react-native";

import { OnboardingLayout } from "../components/OnboardingLayout";
import { useOnboarding } from "../OnboardingContext";
import { useStep } from "../useStep";
import { colors } from "../../../theme/colors";
import type { OnboardingScreenProps } from "../../../navigation/types";

export function FirstNameScreen({ navigation }: OnboardingScreenProps<"FirstName">) {
  const { answers, setAnswer } = useOnboarding();
  const step = useStep("FirstName");

  return (
    <OnboardingLayout
      eyebrow="Profile basics"
      title={"First thing's first,\ntell us your name."}
      {...step}
      ctaDisabled={answers.firstName.trim().length === 0}
      onCta={() => navigation.navigate("Birthday")}
      onBack={navigation.goBack}
    >
      <View>
        <Text style={styles.label}>First name</Text>
        <TextInput
          style={styles.input}
          value={answers.firstName}
          onChangeText={(t) => setAnswer("firstName", t)}
          placeholder="Julian"
          placeholderTextColor={colors.textSubtle}
          autoCapitalize="words"
          autoCorrect={false}
          returnKeyType="done"
        />
      </View>
    </OnboardingLayout>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.textSubtle,
    fontSize: 12,
    letterSpacing: 1.5,
    textTransform: "uppercase",
    marginBottom: 8,
  },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.secondaryDim,
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: colors.text,
    fontSize: 16,
  },
});
