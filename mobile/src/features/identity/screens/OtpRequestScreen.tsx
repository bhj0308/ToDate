import { useState } from "react";
import { Text } from "react-native";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { TextField } from "../../../components/TextField";
import { colors } from "../../../theme/colors";
import { useRequestOtp } from "../hooks/useOtpAuth";
import type { AuthStackScreenProps } from "../../../navigation/types";

/**
 * Email is the only channel offered here: the backend auto-registers a new
 * account on first email OTP verification. Phone OTP requires an existing
 * account (no way to attach a phone number pre-auth yet), so it's left out
 * of this v1 flow rather than presenting a path that would 400.
 */
export function OtpRequestScreen({ navigation }: AuthStackScreenProps<"OtpRequest">) {
  const [email, setEmail] = useState("");
  const requestOtp = useRequestOtp();

  async function handleSubmit() {
    const result = await requestOtp.mutateAsync({ destination: email.trim(), channel: "email" });
    navigation.navigate("OtpVerify", {
      challengeId: result.challenge_id,
      destination: email.trim(),
      devCode: result.dev_code ?? undefined,
    });
  }

  return (
    <Screen scroll={false}>
      <Text style={{ fontSize: 30, fontWeight: "700", color: colors.text, letterSpacing: 1 }}>
        ToDate
      </Text>
      <Text style={{ color: colors.textMuted, marginBottom: 8 }}>
        Enter your email to sign in or create an account.
      </Text>
      <TextField
        label="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        placeholder="you@example.com"
      />
      {requestOtp.isError && <StatusMessage variant="error" message="Couldn't send a code. Check the email and try again." />}
      <PrimaryButton
        title="Send code"
        onPress={handleSubmit}
        loading={requestOtp.isPending}
        disabled={email.trim().length === 0}
      />
    </Screen>
  );
}
