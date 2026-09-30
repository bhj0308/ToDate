import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { OnboardingProvider } from "../features/onboarding/OnboardingContext";
import { BirthdayScreen } from "../features/onboarding/screens/BirthdayScreen";
import { DatingGoalsScreen } from "../features/onboarding/screens/DatingGoalsScreen";
import { FirstNameScreen } from "../features/onboarding/screens/FirstNameScreen";
import { GenderScreen } from "../features/onboarding/screens/GenderScreen";
import { InterestedInScreen } from "../features/onboarding/screens/InterestedInScreen";
import { IntentScreen } from "../features/onboarding/screens/IntentScreen";
import { ValuesRankingScreen } from "../features/onboarding/screens/ValuesRankingScreen";
import type { OnboardingStackParamList } from "./types";

const Stack = createNativeStackNavigator<OnboardingStackParamList>();

/**
 * The "application" flow from design/screens/. The phone (05) and verification
 * (06) steps are missing on purpose — they need the phone-vs-email decision
 * first; see design/README.md.
 */
export function OnboardingStack() {
  return (
    <OnboardingProvider>
      <Stack.Navigator screenOptions={{ headerShown: false, animation: "slide_from_right" }}>
        <Stack.Screen name="ValuesRanking" component={ValuesRankingScreen} />
        <Stack.Screen name="DatingGoals" component={DatingGoalsScreen} />
        <Stack.Screen name="Intent" component={IntentScreen} />
        <Stack.Screen name="Gender" component={GenderScreen} />
        <Stack.Screen name="InterestedIn" component={InterestedInScreen} />
        <Stack.Screen name="FirstName" component={FirstNameScreen} />
        <Stack.Screen name="Birthday" component={BirthdayScreen} />
      </Stack.Navigator>
    </OnboardingProvider>
  );
}
