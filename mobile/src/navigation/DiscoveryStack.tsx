import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { DiscoveryScreen } from "../features/matchmaking/screens/DiscoveryScreen";
import { UserProfileScreen } from "../features/identity/screens/UserProfileScreen";
import type { DiscoveryStackParamList } from "./types";

const Stack = createNativeStackNavigator<DiscoveryStackParamList>();

export function DiscoveryStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="DiscoveryList" component={DiscoveryScreen} options={{ title: "Discovery" }} />
      <Stack.Screen name="UserProfile" component={UserProfileScreen} options={{ title: "Profile" }} />
    </Stack.Navigator>
  );
}
