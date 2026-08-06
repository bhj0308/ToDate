import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { AdminScreen } from "../features/admin/screens/AdminScreen";
import type { AdminStackParamList } from "./types";

const Stack = createNativeStackNavigator<AdminStackParamList>();

export function AdminStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="Admin" component={AdminScreen} options={{ title: "Admin" }} />
    </Stack.Navigator>
  );
}
