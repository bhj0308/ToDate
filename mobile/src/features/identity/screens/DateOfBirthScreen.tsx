import { useState } from "react";
import { Alert, Text, View } from "react-native";

import { useAuth } from "../../../auth/AuthContext";
import { PrimaryButton } from "../../../components/PrimaryButton";
import { Screen } from "../../../components/Screen";
import { StatusMessage } from "../../../components/StatusMessage";
import { TextField } from "../../../components/TextField";
import { colors } from "../../../theme/colors";
import { useSetDateOfBirth } from "../hooks/useProfile";

/** Returns YYYY-MM-DD only for a real calendar date (rejects 2001-02-30). */
function toIsoDate(year: string, month: string, day: string): string | null {
  const y = Number(year), m = Number(month), d = Number(day);
  if (!/^\d{4}$/.test(year) || !m || !d) return null;
  const date = new Date(Date.UTC(y, m - 1, d));
  if (date.getUTCFullYear() !== y || date.getUTCMonth() !== m - 1 || date.getUTCDate() !== d) return null;
  return date.toISOString().slice(0, 10);
}

/**
 * Onboarding gate: ToDate is 18+. Shown until a birth date is on file.
 * One attempt only — the API suspends the account on an under-18 answer.
 */
export function DateOfBirthScreen() {
  const { refreshUser, logout } = useAuth();
  const setDateOfBirth = useSetDateOfBirth();
  const [year, setYear] = useState("");
  const [month, setMonth] = useState("");
  const [day, setDay] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const isoDate = toIsoDate(year, month, day);

  function submit(dateOfBirth: string) {
    setDateOfBirth.mutate(dateOfBirth, {
      onSuccess: () => refreshUser(),
      onError: (error) => {
        const status = (error as { status?: number }).status;
        if (status === 403) {
          Alert.alert("ToDate is 18+", "You must be 18 or older to use ToDate.", [
            { text: "OK", onPress: logout },
          ]);
        } else if (status === 409) {
          refreshUser(); // already set on another device
        } else {
          setMessage("That doesn't look like a valid date.");
        }
      },
    });
  }

  function confirm() {
    if (!isoDate) {
      setMessage("Enter a valid date.");
      return;
    }
    setMessage(null);
    Alert.alert("Confirm your date of birth", `${isoDate}\n\nThis can't be changed later.`, [
      { text: "Edit", style: "cancel" },
      { text: "Confirm", onPress: () => submit(isoDate) },
    ]);
  }

  return (
    <Screen>
      <Text style={{ fontSize: 22, fontWeight: "700", color: colors.text }}>Your date of birth</Text>
      <Text style={{ color: colors.textMuted, marginTop: 4, marginBottom: 12 }}>
        ToDate is for adults 18 and over. We'll confirm this during verification.
      </Text>
      <View style={{ flexDirection: "row", gap: 8 }}>
        <View style={{ flex: 1.4 }}>
          <TextField label="Year" value={year} onChangeText={setYear} keyboardType="number-pad" maxLength={4} placeholder="1994" />
        </View>
        <View style={{ flex: 1 }}>
          <TextField label="Month" value={month} onChangeText={setMonth} keyboardType="number-pad" maxLength={2} placeholder="06" />
        </View>
        <View style={{ flex: 1 }}>
          <TextField label="Day" value={day} onChangeText={setDay} keyboardType="number-pad" maxLength={2} placeholder="15" />
        </View>
      </View>
      {message && <StatusMessage variant="error" message={message} />}
      <PrimaryButton title="Continue" loading={setDateOfBirth.isPending} onPress={confirm} />
      <View style={{ height: 8 }} />
      <PrimaryButton title="Log out" variant="secondary" onPress={logout} />
    </Screen>
  );
}
