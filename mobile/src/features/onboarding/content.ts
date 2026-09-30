/** Option text taken verbatim from the Figma screens in `design/screens/`. */

export const VALUES = [
  "Loyalty",
  "Communication",
  "Emotional connection",
  "Physical chemistry",
  "Financial stability",
  "Ambition & growth",
  "Intelligence",
  "Shared values",
  "Romance",
  "Fun & adventure",
] as const;

export const DATING_GOALS = [
  "A life partner",
  "A long-term relationship",
  "Marriage",
  "Casual dating",
  "Friendship",
  "Common law marriage",
  "Networking",
  "I'm not sure of my dating goals yet",
] as const;

/**
 * Order matters: per the designer's note (design/reference/note-intent-warning-rule.png)
 * picking either of the LAST TWO shows the community warning.
 */
export const INTENTS = [
  "I know what I'm looking for",
  "I'm ready for something serious",
  "I'm ready to put effort into finding my person",
  "I just want to see what's out there",
  "I want people to chat with",
] as const;

export const LOW_INTENT_OPTIONS = INTENTS.slice(-2);

export const INTENT_WARNING =
  "ToDate is a community meant for serious daters, looking to find their forever match. If this isn't you, your application may not be accepted.";

export const GENDERS = ["Woman", "Man", "Non-binary"] as const;
export const INTERESTED_IN = ["Women", "Men", "Non-binary"] as const;
