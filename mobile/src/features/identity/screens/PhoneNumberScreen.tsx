import { useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";

import { colors } from "../../../theme/colors";
import { OnboardingLayout } from "../../onboarding/components/OnboardingLayout";
import { useStep } from "../../onboarding/useStep";
import { useRequestOtp } from "../hooks/useOtpAuth";
import type { AuthStackScreenProps } from "../../../navigation/types";

/** (613) 246-2840 as the digits come in. */
function formatNanp(digits: string): string {
  const d = digits.slice(0, 10);
  if (d.length <= 3) return d.length ? `(${d}` : "";
  if (d.length <= 6) return `(${d.slice(0, 3)}) ${d.slice(3)}`;
  return `(${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6)}`;
}

/**
 * design/screens/05-phone-number.png and 05-phone-number-error.png
 *
 * The "+1 ⌄" country selector is drawn as designed but fixed to +1: the
 * picker's open state hasn't been designed yet.
 */
export function PhoneNumberScreen({ navigation }: AuthStackScreenProps<"PhoneNumber">) {
  const step = useStep("PhoneNumber");
  const requestOtp = useRequestOtp();
  const [digits, setDigits] = useState("");
  const [invalid, setInvalid] = useState(false);

  function submit() {
    // The design shows the error after Continue, not while typing.
    if (digits.length !== 10) {
      setInvalid(true);
      return;
    }
    const phone = `+1${digits}`;
    requestOtp.mutate(
      { destination: phone, channel: "phone" },
      {
        onSuccess: (r) =>
          navigation.navigate("PhoneVerification", {
            challengeId: r.challenge_id,
            phone,
            devCode: r.dev_code ?? undefined,
          }),
        onError: () => setInvalid(true), // the API rejected the number
      },
    );
  }

  return (
    <OnboardingLayout
      eyebrow="Application"
      title="Enter your phone number."
      subtitle="Your contact information is for verification and will not be displayed on your profile."
      {...step}
      ctaDisabled={digits.length === 0}
      ctaLoading={requestOtp.isPending}
      onCta={submit}
      onBack={navigation.goBack}
    >
      <Text style={styles.label}>Phone number</Text>
      <View style={[styles.field, invalid && styles.fieldInvalid]}>
        <View style={styles.country}>
          <Text style={styles.countryText}>+1</Text>
          <Text style={styles.chevron}>⌄</Text>
        </View>
        <TextInput
          style={styles.input}
          value={formatNanp(digits)}
          onChangeText={(t) => {
            setDigits(t.replace(/\D/g, "").slice(0, 10));
            setInvalid(false);
          }}
          keyboardType="phone-pad"
          textContentType="telephoneNumber"
          autoComplete="tel"
          placeholder="(613) 246-2840"
          placeholderTextColor={colors.textSubtle}
          autoFocus
        />
      </View>
      {invalid && <Text style={styles.error}>Please enter a valid phone number</Text>}
    </OnboardingLayout>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.textSubtle,
    fontSize: 13,
    fontWeight: "600",
    letterSpacing: 0.5,
    textTransform: "uppercase",
    marginBottom: 8,
  },
  field: {
    flexDirection: "row",
    alignItems: "stretch",
    backgroundColor: colors.surface,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "transparent",
  },
  fieldInvalid: { borderColor: colors.danger, backgroundColor: "#3B1B1A" },
  country: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 18,
    borderRightWidth: 1,
    borderRightColor: colors.border,
  },
  countryText: { color: colors.text, fontSize: 17 },
  chevron: { color: colors.text, fontSize: 14, marginTop: -6 },
  input: { flex: 1, color: colors.text, fontSize: 17, paddingHorizontal: 14, paddingVertical: 14 },
  error: { color: colors.danger, fontSize: 14, marginTop: 8 },
});
