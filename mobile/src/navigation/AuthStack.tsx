import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { OtpRequestScreen } from "../features/identity/screens/OtpRequestScreen";
import { OtpVerifyScreen } from "../features/identity/screens/OtpVerifyScreen";
import type { AuthStackParamList } from "./types";

const Stack = createNativeStackNavigator<AuthStackParamList>();

export function AuthStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="OtpRequest" component={OtpRequestScreen} />
      <Stack.Screen name="OtpVerify" component={OtpVerifyScreen} options={{ headerShown: true, title: "" }} />
    </Stack.Navigator>
  );
}
