import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";

import { colors } from "../theme/colors";
import { DiscoveryStack } from "./DiscoveryStack";
import { MatchesStack } from "./MatchesStack";
import { BillingStack } from "./BillingStack";
import { ProfileStack } from "./ProfileStack";
import type { AppTabParamList } from "./types";

const Tab = createBottomTabNavigator<AppTabParamList>();

export function AppTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.secondary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarLabelStyle: { fontWeight: "600" },
        tabBarStyle: {
          backgroundColor: colors.background,
          borderTopColor: colors.border,
        },
      }}
    >
      <Tab.Screen name="DiscoveryTab" component={DiscoveryStack} options={{ title: "Discovery" }} />
      <Tab.Screen name="MatchesTab" component={MatchesStack} options={{ title: "Matches" }} />
      <Tab.Screen name="BillingTab" component={BillingStack} options={{ title: "Billing" }} />
      <Tab.Screen name="ProfileTab" component={ProfileStack} options={{ title: "Profile" }} />
    </Tab.Navigator>
  );
}
