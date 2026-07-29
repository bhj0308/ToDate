import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { BillingScreen } from "../features/entitlements/screens/BillingScreen";
import type { BillingStackParamList } from "./types";

const Stack = createNativeStackNavigator<BillingStackParamList>();

export function BillingStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="Billing" component={BillingScreen} options={{ title: "Billing" }} />
    </Stack.Navigator>
  );
}
