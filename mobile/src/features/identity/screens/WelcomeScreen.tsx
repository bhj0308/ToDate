import { LinearGradient } from "expo-linear-gradient";
import { ImageBackground, Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { colors } from "../../../theme/colors";
import { headingFont } from "../../onboarding/components/OnboardingLayout";
import type { AuthStackScreenProps } from "../../../navigation/types";

/**
 * design/screens/01-welcome.png
 *
 * The background is cropped out of the flattened welcome export (the band
 * between the wordmark and the headline, so no baked-in text). It's a stopgap:
 * swap in the designer's original photo export for full resolution. The phone
 * icon on the button is still missing — no asset was exported.
 */
const BACKGROUND = require("../../../../assets/images/welcome-bg.jpg");
export function WelcomeScreen({ navigation }: AuthStackScreenProps<"Welcome">) {
  // Phone sign-in is the same flow for new and returning members: the verified
  // number either finds the existing account or creates one.
  const goToPhone = () => navigation.navigate("PhoneNumber");

  return (
    <ImageBackground source={BACKGROUND} resizeMode="cover" style={styles.flex}>
      {/* Darken top and bottom so the wordmark and headline read over the photo. */}
      <LinearGradient
        colors={["rgba(20,12,8,0.55)", "rgba(20,12,8,0)", "rgba(20,12,8,0.15)", colors.backgroundBottom]}
        locations={[0, 0.22, 0.55, 0.88]}
        style={StyleSheet.absoluteFill}
      />
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
    </ImageBackground>
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
