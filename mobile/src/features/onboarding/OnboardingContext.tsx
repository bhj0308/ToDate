import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

export type OnboardingAnswers = {
  /** Ranked most-important first. */
  values: string[];
  datingGoals: string[];
  intents: string[];
  gender: string | null;
  interestedIn: string[];
  firstName: string;
  birthday: Date | null;
};

const EMPTY: OnboardingAnswers = {
  values: [],
  datingGoals: [],
  intents: [],
  gender: null,
  interestedIn: [],
  firstName: "",
  birthday: null,
};

type OnboardingState = {
  answers: OnboardingAnswers;
  setAnswer: <K extends keyof OnboardingAnswers>(key: K, value: OnboardingAnswers[K]) => void;
};

const OnboardingContext = createContext<OnboardingState | null>(null);

/**
 * Holds the application answers while someone works through onboarding.
 *
 * Only `firstName` and `birthday` have somewhere to go today — they're saved on
 * the last step. The rest (values, goals, intent, gender, interestedIn) have no
 * backend fields yet; see design/README.md "Where the designs and the build
 * disagree". They're kept here so the flow is complete and reviewable, and so
 * wiring them up later is a one-line change per answer.
 */
export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [answers, setAnswers] = useState<OnboardingAnswers>(EMPTY);

  const value = useMemo<OnboardingState>(
    () => ({
      answers,
      setAnswer: (key, v) => setAnswers((prev) => ({ ...prev, [key]: v })),
    }),
    [answers],
  );

  return <OnboardingContext.Provider value={value}>{children}</OnboardingContext.Provider>;
}

export function useOnboarding(): OnboardingState {
  const ctx = useContext(OnboardingContext);
  if (!ctx) throw new Error("useOnboarding must be used within OnboardingProvider");
  return ctx;
}
