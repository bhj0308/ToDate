import { useRef, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { colors } from "../../../theme/colors";
import { OnboardingLayout } from "../../onboarding/components/OnboardingLayout";
import { useStep } from "../../onboarding/useStep";
import { useRequestOtp, useVerifyOtp } from "../hooks/useOtpAuth";
import type { AuthStackScreenProps } from "../../../navigation/types";

const LENGTH = 6;

/**
 * design/screens/06-phone-verification.png
 *
 * One hidden input drives six display boxes, so paste and iOS/Android SMS
 * autofill work. The error line reuses 05's pattern — 06 has no error state
 * in the design.
 */
export function PhoneVerificationScreen({
  navigation,
  route,
}: AuthStackScreenProps<"PhoneVerification">) {
  const { phone, devCode } = route.params;
  const step = useStep("PhoneVerification");
  const verifyOtp = useVerifyOtp();
  const requestOtp = useRequestOtp();
  const inputRef = useRef<TextInput>(null);

  // Outside production the API returns the code, so the flow works without SMS.
  const [code, setCode] = useState(devCode ?? "");
  const [challengeId, setChallengeId] = useState(route.params.challengeId);
  const [error, setError] = useState<string | null>(null);

  function submit() {
    setError(null);
    verifyOtp.mutate(
      { challenge_id: challengeId, code },
      {
        // On success AuthContext logs in and RootNavigator moves on by itself.
        onError: (e) => {
          const detail = (e as { detail?: unknown }).detail;
          setError(
            typeof detail === "string" && detail.includes("invite")
              ? "ToDate is invite-only right now."
              : "That code didn't work. Check it and try again.",
          );
        },
      },
    );
  }

  function resend() {
    setError(null);
    requestOtp.mutate(
      { destination: phone, channel: "phone" },
      {
        onSuccess: (r) => {
          setChallengeId(r.challenge_id);
          setCode(r.dev_code ?? "");
        },
      },
    );
  }

  return (
    <OnboardingLayout
      eyebrow="Application"
      title="Phone verification"
      subtitle="Enter the verification code we sent to your phone number."
      {...step}
      ctaDisabled={code.length !== LENGTH}
      ctaLoading={verifyOtp.isPending}
      onCta={submit}
      onBack={navigation.goBack}
    >
      <Text style={styles.label}>6 digit code</Text>
      <Pressable style={styles.boxes} onPress={() => inputRef.current?.focus()}>
        {Array.from({ length: LENGTH }, (_, i) => (
          <View key={i} style={styles.box}>
            <Text style={styles.digit}>{code[i] ?? ""}</Text>
          </View>
        ))}
      </Pressable>
      <TextInput
        ref={inputRef}
        value={code}
        onChangeText={(t) => {
          setCode(t.replace(/\D/g, "").slice(0, LENGTH));
          setError(null);
        }}
        keyboardType="number-pad"
        textContentType="oneTimeCode"
        autoComplete="sms-otp"
        maxLength={LENGTH}
        autoFocus
        style={styles.hiddenInput}
      />
      {error && <Text style={styles.error}>{error}</Text>}
      <Pressable onPress={resend} disabled={requestOtp.isPending} style={styles.resend}>
        <Text style={styles.resendText}>Resend code</Text>
      </Pressable>
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
  boxes: { flexDirection: "row", gap: 8 },
  box: {
    flex: 1,
    height: 52,
    borderRadius: 10,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
  digit: { color: colors.text, fontSize: 22 },
  hiddenInput: { position: "absolute", width: 1, height: 1, opacity: 0 },
  error: { color: colors.danger, fontSize: 14, marginTop: 8 },
  resend: { alignSelf: "center", marginTop: 28, padding: 6 },
  resendText: { color: colors.text, fontSize: 16, textDecorationLine: "underline" },
});
