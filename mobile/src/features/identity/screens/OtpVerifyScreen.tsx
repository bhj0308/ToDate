import { useState } from "react";
import { Text } from "react-native";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { TextField } from "../../../components/TextField";
import { colors } from "../../../theme/colors";
import { useVerifyOtp } from "../hooks/useOtpAuth";
import type { AuthStackScreenProps } from "../../../navigation/types";

export function OtpVerifyScreen({ route }: AuthStackScreenProps<"OtpVerify">) {
  const { challengeId, destination, devCode } = route.params;
  const [code, setCode] = useState(devCode ?? "");
  const verifyOtp = useVerifyOtp();

  async function handleSubmit() {
    await verifyOtp.mutateAsync({ challenge_id: challengeId, code: code.trim() });
    // On success, AuthContext's `login` flips isAuthenticated and RootNavigator
    // swaps to AppTabs automatically — no manual navigation needed here.
  }

  return (
    <Screen scroll={false}>
      <Text style={{ fontSize: 22, fontWeight: "700", color: colors.text }}>Enter your code</Text>
      <Text style={{ color: colors.textMuted, marginBottom: 8 }}>Sent to {destination}</Text>
      {devCode && (
        <StatusMessage variant="empty" message={`Dev mode: code pre-filled (${devCode})`} />
      )}
      <TextField
        label="6-digit code"
        value={code}
        onChangeText={setCode}
        keyboardType="number-pad"
        maxLength={6}
      />
      {verifyOtp.isError && <StatusMessage variant="error" message="Incorrect or expired code." />}
      <PrimaryButton
        title="Verify"
        onPress={handleSubmit}
        loading={verifyOtp.isPending}
        disabled={code.trim().length !== 6}
      />
    </Screen>
  );
}
