/**
 * Sampled from the 2x Figma exports in `design/` — not eyeballed.
 *
 * Role note: in this design the filled CTA is **wine** and **gold** marks
 * selection. That's the reverse of the earlier light theme, so `primary` is now
 * wine and `secondary` gold; components that used them keep working unchanged.
 */
export const colors = {
  // Screens use a vertical gradient from backgroundTop to backgroundBottom.
  backgroundTop: "#452816",
  backgroundBottom: "#271611",
  background: "#2E1A12", // flat fallback where a gradient isn't used

  surface: "#362721", // unselected chip / input fill
  surfaceRaised: "#3B2C26", // picker highlight band, outlined selected row

  text: "#F0EAE0", // headings and primary copy
  textMuted: "#C7BFB6", // body / subtitles
  textSubtle: "#9C8B7C", // uppercase field labels

  primary: "#861738", // wine — filled CTA
  onPrimary: "#F0EAE0",
  primaryDisabled: "#2F1517",
  onPrimaryDisabled: "#8A7168",

  secondary: "#C0955D", // gold — selection fill, accents
  secondaryBright: "#C79E69", // top of the gold gradient
  secondaryDim: "#B38446", // radio dot, gold borders
  onSecondary: "#2A1A10", // text on gold

  border: "#4A3730",
  progressTrack: "#59544E",

  danger: "#FF4D4D",
  success: "#4F7A52",
};
