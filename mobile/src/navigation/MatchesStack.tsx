import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { MatchListScreen } from "../features/matchmaking/screens/MatchListScreen";
import { MatchDetailScreen } from "../features/matchmaking/screens/MatchDetailScreen";
import { UserProfileScreen } from "../features/identity/screens/UserProfileScreen";
import type { MatchesStackParamList } from "./types";

const Stack = createNativeStackNavigator<MatchesStackParamList>();

export function MatchesStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="MatchList" component={MatchListScreen} options={{ title: "Matches" }} />
      <Stack.Screen name="MatchDetail" component={MatchDetailScreen} options={{ title: "Match" }} />
      <Stack.Screen name="UserProfile" component={UserProfileScreen} options={{ title: "Profile" }} />
    </Stack.Navigator>
  );
}
