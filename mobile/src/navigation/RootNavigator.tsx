import { NavigationContainer } from "@react-navigation/native";

import { useAuth } from "../auth/AuthContext";
import { StatusMessage } from "../components/StatusMessage";
import { DateOfBirthScreen } from "../features/identity/screens/DateOfBirthScreen";
import { UpdateRequiredScreen } from "../features/release/UpdateRequiredScreen";
import { useUpgradeRequired } from "../features/release/useUpgradeRequired";
import { AuthStack } from "./AuthStack";
import { AppTabs } from "./AppTabs";

export function RootNavigator() {
  const { isHydrating, isAuthenticated, user } = useAuth();
  const upgradeRequired = useUpgradeRequired();

  if (upgradeRequired) {
    return <UpdateRequiredScreen />;
  }

  if (isHydrating) {
    return <StatusMessage variant="loading" />;
  }

  // Nothing that shows a member to others is reachable without a stated age.
  if (isAuthenticated && !user?.date_of_birth) {
    return <DateOfBirthScreen />;
  }

  return (
    <NavigationContainer>{isAuthenticated ? <AppTabs /> : <AuthStack />}</NavigationContainer>
  );
}
