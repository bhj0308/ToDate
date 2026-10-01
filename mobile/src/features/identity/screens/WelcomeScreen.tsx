import { LinearGradient } from "expo-linear-gradient";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { colors } from "../../../theme/colors";
import { headingFont } from "../../onboarding/components/OnboardingLayout";
import type { AuthStackScreenProps } from "../../../navigation/types";

/**
 * design/screens/01-welcome.png
 *
 * Missing assets: the full-bleed photograph and the phone icon on the button
 * weren't exported, so the background is the app gradient and the button has no
 * icon. Drop them in design/images/ and they can be wired in.
 */
export function WelcomeScreen({ navigation }: AuthStackScreenProps<"Welcome">) {
  // Phone sign-in is the same flow for new and returning members: the verified
  // number either finds the existing account or creates one.
  const goToPhone = () => navigation.navigate("PhoneNumber");

  return (
    <LinearGradient colors={[colors.backgroundTop, colors.backgroundBottom]} style={styles.flex}>
      <SafeAreaView style={styles.flex} edges={["top", "bottom"]}>
        <Text style={styles.wordmark}>ToDate</Text>
        <View style={styles.flex} />
        <View style={styles.bottom}>
          <Text style={styles.headline}>Where meaningful relationships begin.</Text>
          <PrimaryButton title="Continue with phone" onPress={goToPhone} />
          <Pressable onPress={goToPhone} style={styles.signIn} hitSlop={8}>
            <Text style={styles.signInText}>
              Already have an account? <Text style={styles.signInLink}>Sign in</Text>
            </Text>
          </Pressable>
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  wordmark: {
    color: colors.text,
    fontFamily: headingFont,
    fontSize: 32,
    textAlign: "center",
    marginTop: 40,
  },
  bottom: { paddingHorizontal: 24, paddingBottom: 16, gap: 20 },
  headline: { color: colors.text, fontSize: 30, lineHeight: 38, textAlign: "center" },
  signIn: { alignItems: "center", paddingVertical: 4 },
  signInText: { color: colors.textMuted, fontSize: 15 },
  signInLink: { color: colors.text, textDecorationLine: "underline" },
});
