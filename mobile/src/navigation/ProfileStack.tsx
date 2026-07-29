import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { ProfileScreen } from "../features/identity/screens/ProfileScreen";
import { VerificationStatusScreen } from "../features/verification/screens/VerificationStatusScreen";
import type { ProfileStackParamList } from "./types";

const Stack = createNativeStackNavigator<ProfileStackParamList>();

export function ProfileStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="MyProfile" component={ProfileScreen} options={{ title: "Profile" }} />
      <Stack.Screen
        name="VerificationStatus"
        component={VerificationStatusScreen}
        options={{ title: "Verification" }}
      />
    </Stack.Navigator>
  );
}
