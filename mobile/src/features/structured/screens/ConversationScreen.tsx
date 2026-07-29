import { useMemo, useState } from "react";
import { FlatList, KeyboardAvoidingView, Platform, StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "../../../components/PrimaryButton";
import { StatusMessage } from "../../../components/StatusMessage";
import { TextField } from "../../../components/TextField";
import { colors } from "../../../theme/colors";
import { useAuth } from "../../../auth/AuthContext";
import { useConversation, useSendMessage } from "../hooks/useStructured";

export function ConversationScreen({ matchId }: { matchId: string }) {
  const { user } = useAuth();
  const conversation = useConversation(matchId);
  const sendMessage = useSendMessage(matchId);
  const [draft, setDraft] = useState("");

  // The backend returns messages oldest-first; an inverted FlatList expects
  // newest-first so the newest message renders at the bottom, near the composer.
  const reversedMessages = useMemo(
    () => (conversation.data ? [...conversation.data.messages].reverse() : []),
    [conversation.data],
  );

  if (conversation.isLoading) return <StatusMessage variant="loading" />;
  if (conversation.isError || !conversation.data) return <StatusMessage variant="error" />;

  async function handleSend() {
    const body = draft.trim();
    if (!body) return;
    setDraft("");
    await sendMessage.mutateAsync(body);
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <FlatList
        data={reversedMessages}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        inverted
        ListEmptyComponent={<StatusMessage variant="empty" message="Say hello." />}
        renderItem={({ item }) => (
          <View
            style={[
              styles.bubble,
              item.sender_id === user?.id ? styles.mine : styles.theirs,
            ]}
          >
            <Text style={item.sender_id === user?.id ? styles.mineText : styles.theirsText}>
              {item.body}
            </Text>
          </View>
        )}
      />
      <View style={styles.composer}>
        <View style={styles.input}>
          <TextField label="" placeholder="Message" value={draft} onChangeText={setDraft} />
        </View>
        <PrimaryButton title="Send" onPress={handleSend} loading={sendMessage.isPending} disabled={!draft.trim()} />
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
  list: {
    padding: 16,
    gap: 8,
    flexGrow: 1,
    justifyContent: "flex-end",
  },
  bubble: {
    maxWidth: "80%",
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  mine: {
    backgroundColor: colors.primary,
    alignSelf: "flex-end",
  },
  theirs: {
    backgroundColor: colors.surface,
    alignSelf: "flex-start",
  },
  mineText: {
    color: "#fff",
  },
  theirsText: {
    color: colors.text,
  },
  composer: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  input: {
    flex: 1,
  },
});
