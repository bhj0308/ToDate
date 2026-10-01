import { useState } from "react";
import { Alert, Modal, Pressable, StyleSheet, Text, View } from "react-native";

import { useAuth } from "../../../auth/AuthContext";
import { PrimaryButton } from "../../../components/PrimaryButton";
import { colors } from "../../../theme/colors";
import { useSetDateOfBirth, useUpdateMyProfile } from "../../identity/hooks/useProfile";
import { BirthdayWheel } from "../components/BirthdayWheel";
import { OnboardingLayout, headingFont } from "../components/OnboardingLayout";
import { useOnboarding } from "../OnboardingContext";
import { useStep } from "../useStep";
import type { OnboardingScreenProps } from "../../../navigation/types";

function ageOn(dob: Date, today = new Date()): number {
  let age = today.getFullYear() - dob.getFullYear();
  const beforeBirthday =
    today.getMonth() < dob.getMonth() ||
    (today.getMonth() === dob.getMonth() && today.getDate() < dob.getDate());
  return beforeBirthday ? age - 1 : age;
}

/** Local YYYY-MM-DD — toISOString() would shift the date for anyone west of UTC. */
function toIsoDate(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

const DEFAULT_DOB = new Date(new Date().getFullYear() - 25, 0, 1);

export function BirthdayScreen({ navigation }: OnboardingScreenProps<"Birthday">) {
  const { answers, setAnswer } = useOnboarding();
  const { refreshUser, logout } = useAuth();
  const step = useStep("Birthday");
  const setDateOfBirth = useSetDateOfBirth();
  const updateProfile = useUpdateMyProfile();
  const [confirming, setConfirming] = useState(false);

  const birthday = answers.birthday ?? DEFAULT_DOB;
  const saving = setDateOfBirth.isPending || updateProfile.isPending;

  async function confirm() {
    setConfirming(false);
    try {
      // Name first: if the birth date is rejected the account is suspended, and
      // saving the profile afterwards would just fail.
      if (answers.firstName.trim()) {
        await updateProfile.mutateAsync({ display_name: answers.firstName.trim() });
      }
      await setDateOfBirth.mutateAsync(toIsoDate(birthday));
      await refreshUser(); // clears the onboarding gate in RootNavigator
    } catch (error) {
      const status = (error as { status?: number }).status;
      if (status === 403) {
        Alert.alert("ToDate is 18+", "You must be 18 or older to use ToDate.", [
          { text: "OK", onPress: logout },
        ]);
      } else if (status === 409) {
        await refreshUser(); // already set on another device
      } else {
        Alert.alert("Couldn't save that", "Please try again.");
      }
    }
  }

  return (
    <>
      <OnboardingLayout
        eyebrow="Profile basics"
        title={`Nice to meet you,\n${answers.firstName.trim() || "[name]"}.\nWhen is your birthday?`}
        {...step}
        // Disabled until a date is picked, as in the design: the birthday can't
        // be changed later, so accepting the default by accident isn't allowed.
        ctaDisabled={!answers.birthday}
        ctaLoading={saving}
        onCta={() => setConfirming(true)}
        onBack={navigation.goBack}
        // The wheel scrolls vertically; a page scroll around it would fight it.
        scrollEnabled={false}
      >
        <Text style={styles.label}>Birthday</Text>
        <BirthdayWheel value={birthday} onChange={(d) => setAnswer("birthday", d)} />
      </OnboardingLayout>

      <Modal visible={confirming} transparent animationType="slide">
        <View style={styles.backdrop}>
          <View style={styles.sheet}>
            <View style={styles.grabber} />
            <Text style={styles.sheetTitle}>Are you {ageOn(birthday)}?</Text>
            <Text style={styles.sheetBody}>
              Please ensure your date of birth is correct, as this cannot be changed later.
            </Text>
            <PrimaryButton title="My age is correct" onPress={confirm} loading={saving} />
            <Pressable onPress={() => setConfirming(false)} style={styles.goBack}>
              <Text style={styles.goBackText}>Go back</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </>
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
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.5)", justifyContent: "flex-end" },
  sheet: {
    backgroundColor: colors.backgroundTop,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 24,
    paddingTop: 12,
    paddingBottom: 32,
  },
  grabber: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.textSubtle,
    alignSelf: "center",
    marginBottom: 20,
  },
  sheetTitle: { color: colors.text, fontSize: 28, fontFamily: headingFont, marginBottom: 8 },
  sheetBody: { color: colors.textMuted, fontSize: 15, lineHeight: 22, marginBottom: 20 },
  goBack: { paddingVertical: 14, alignItems: "center" },
  goBackText: { color: colors.textMuted, fontSize: 16 },
});
