import { DarkTheme, NavigationContainer, type Theme } from "@react-navigation/native";

import { useAuth } from "../auth/AuthContext";
import { StatusMessage } from "../components/StatusMessage";
import { UpdateRequiredScreen } from "../features/release/UpdateRequiredScreen";
import { useUpgradeRequired } from "../features/release/useUpgradeRequired";
import { AuthStack } from "./AuthStack";
import { AppTabs } from "./AppTabs";
import { OnboardingStack } from "./OnboardingStack";
import { colors } from "../theme/colors";

/**
 * Without this, React Navigation paints its own light theme: white headers and
 * white screen cards behind our dark screens.
 */
const navigationTheme: Theme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    background: colors.background,
    card: colors.backgroundBottom,
    text: colors.text,
    border: colors.border,
    primary: colors.secondary,
    notification: colors.danger,
  },
};

export function RootNavigator() {
  const { isHydrating, isAuthenticated, user } = useAuth();
  const upgradeRequired = useUpgradeRequired();

  if (upgradeRequired) {
    return <UpdateRequiredScreen />;
  }

  if (isHydrating) {
    return <StatusMessage variant="loading" />;
  }

  // A stated date of birth marks onboarding as done: nothing that shows a member
  // to others is reachable before the application flow is finished.
  const needsOnboarding = isAuthenticated && !user?.date_of_birth;

  return (
    <NavigationContainer theme={navigationTheme}>
      {!isAuthenticated ? <AuthStack /> : needsOnboarding ? <OnboardingStack /> : <AppTabs />}
    </NavigationContainer>
  );
}
