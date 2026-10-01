import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { PhoneNumberScreen } from "../features/identity/screens/PhoneNumberScreen";
import { PhoneVerificationScreen } from "../features/identity/screens/PhoneVerificationScreen";
import { WelcomeScreen } from "../features/identity/screens/WelcomeScreen";
import type { AuthStackParamList } from "./types";

const Stack = createNativeStackNavigator<AuthStackParamList>();

/** Phone-first sign-up: design/screens/01, 05, 06. */
export function AuthStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false, animation: "slide_from_right" }}>
      <Stack.Screen name="Welcome" component={WelcomeScreen} />
      <Stack.Screen name="PhoneNumber" component={PhoneNumberScreen} />
      <Stack.Screen name="PhoneVerification" component={PhoneVerificationScreen} />
    </Stack.Navigator>
  );
}
