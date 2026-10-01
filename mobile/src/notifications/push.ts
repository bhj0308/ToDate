import Constants, { ExecutionEnvironment } from "expo-constants";
import * as Device from "expo-device";
import { Platform } from "react-native";

import { api } from "../api/client";

type NotificationsModule = typeof import("expo-notifications");

/**
 * Push needs a development or store build. Expo Go dropped remote push in
 * SDK 53, and on Android merely *loading* expo-notifications there raises an
 * error. So inside Expo Go the module is never required — the rest of the app
 * still runs, just without push.
 */
const isExpoGo = Constants.executionEnvironment === ExecutionEnvironment.StoreClient;

let notifications: NotificationsModule | null = null;

function loadNotifications(): NotificationsModule | null {
  if (isExpoGo) return null;
  if (!notifications) {
    notifications = require("expo-notifications") as NotificationsModule;
    // Show pushes as banners even while the app is open.
    notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowBanner: true,
        shouldShowList: true,
        shouldPlaySound: true,
        shouldSetBadge: false,
      }),
    });
  }
  return notifications;
}

let registeredToken: string | null = null;

/**
 * Ask for permission, get this device's Expo push token and register it with
 * the API. Safe to call on every sign-in; quietly does nothing when push can't
 * work (Expo Go, simulator, permission denied, no EAS project configured yet).
 */
export async function registerForPushNotifications(): Promise<void> {
  const Notifications = loadNotifications();
  if (!Notifications || !Device.isDevice) return;

  const projectId = Constants.expoConfig?.extra?.eas?.projectId as string | undefined;
  if (!projectId) {
    console.warn("Push disabled: no EAS projectId. Run `eas init` to create one.");
    return;
  }

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "default",
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }

  let { status } = await Notifications.getPermissionsAsync();
  if (status !== "granted") {
    ({ status } = await Notifications.requestPermissionsAsync());
  }
  if (status !== "granted") return;

  const { data: token } = await Notifications.getExpoPushTokenAsync({ projectId });
  const { error } = await api.POST("/v1/users/me/push-tokens", {
    body: { token, platform: Platform.OS === "ios" ? "ios" : "android" },
  });
  if (!error) registeredToken = token;
}

/** Call before clearing auth so this device stops receiving the account's pushes. */
export async function unregisterPushNotifications(): Promise<void> {
  if (!registeredToken) return;
  await api.DELETE("/v1/users/me/push-tokens", { body: { token: registeredToken } });
  registeredToken = null;
}

/** For account deletion: the server already removed every token. */
export function forgetPushRegistration(): void {
  registeredToken = null;
}
