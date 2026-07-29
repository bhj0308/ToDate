import { NavigationContainer } from "@react-navigation/native";

import { useAuth } from "../auth/AuthContext";
import { StatusMessage } from "../components/StatusMessage";
import { AuthStack } from "./AuthStack";
import { AppTabs } from "./AppTabs";

export function RootNavigator() {
  const { isHydrating, isAuthenticated } = useAuth();

  if (isHydrating) {
    return <StatusMessage variant="loading" />;
  }

  return (
    <NavigationContainer>{isAuthenticated ? <AppTabs /> : <AuthStack />}</NavigationContainer>
  );
}
