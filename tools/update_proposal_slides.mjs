/**
 * Apply the 12 August 2026 feedback decisions to the current nine-slide deck.
 *
 * Usage:
 *   node tools/update_proposal_slides.mjs [source.pptx] [output.pptx]
 */

import path from "node:path";
import { fileURLToPath } from "node:url";

import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const starterPptxPath = path.resolve(
  process.argv[2] ??
    path.join(
      ROOT,
      "outputs/citizen-water-vegetation-cooling-spatial-justice-proposal-shortened-feedback-incorporated-v2.pptx",
    ),
);
const OUTPUT = path.resolve(
  process.argv[3] ?? path.join(ROOT, "outputs/Thesis_Proposal_Slides.pptx"),
);

const PROPOSAL = path.join(ROOT, "outputs/Thesis_Proposal.docx");
const FEEDBACK = "/Users/jsheils/Downloads/Sheils_Proposal_Feedback (1).pages";
const PROJECT_CONFIG = path.join(ROOT, "config/project.toml");
const WATERING_TABLE = path.join(
  ROOT,
  "output/exploratory/tables/watering_concentration.csv",
);
const EQUITY_ASSOCIATIONS = path.join(
  ROOT,
  "output/equity/tables/equity_associations.csv",
);
const EQUITY_SCREEN = path.join(
  ROOT,
  "output/equity/tables/priority_gap_planungsraeume.csv",
);

const presentation = await PresentationFile.importPptx(
  await FileBlob.load(starterPptxPath),
);

function resolve(id) {
  const element = presentation.resolve(id);
  if (!element) throw new Error(`Could not resolve ${id}`);
  return element;
}

function setText(id, value) {
  const shape = resolve(id);
  shape.text = value;
  return shape;
}

function setNotes(slideIndex, body, sources) {
  const slide = presentation.slides.getItem(slideIndex);
  slide.speakerNotes.textFrame.setText(
    [
      body,
      "",
      "[Sources]",
      ...sources.map((source) => `- ${source}`),
      "[/Sources]",
    ].join("\n"),
  );
  slide.speakerNotes.setVisible(true);
}

// Slide 1 — current proposal date and source record.
setText(
  "sh/65g3298r",
  "Joseph Carpenter Sheils  ·  M.Sc. Data Science  ·  Saarland University  ·  August 2026",
);
setNotes(
  0,
  "This presentation follows the feedback-aligned three-part thesis. Part I estimates how greenness, built form, and drought relate to summer LST. Part II tests a recorded-watering association only if its end-Month-2 detectability gate passes. Part III is the guaranteed core and examines whether recorded care reaches environmental and social need.",
  [PROPOSAL, FEEDBACK],
);

// Slide 2 — retain the spatial motivation and refresh traceability.
setNotes(
  1,
  "The maps motivate the spatial question; they are not the thesis estimand. The formal analysis uses finer-scale satellite and official Berlin inputs. Keep the narration to the unequal distribution of heat and recorded care.",
  [PROPOSAL, WATERING_TABLE],
);

// Slide 3 — narration follows the supervisor's density guidance.
setNotes(
  2,
  "Narrate only two decisions: Part III is the guaranteed core, and Part II is conditional on an end-Month-2 power gate. Part I supplies thermal context to Part III. Do not read each box aloud.",
  [PROPOSAL, FEEDBACK],
);

// Slide 4 — shorter title fixes the left-edge clipping in the prior deck.
setText("sh/1cj2d8b6", "Recorded watering is highly concentrated");
setNotes(
  3,
  "The completed descriptive foundation contains 58,474 deduplicated recorded events. The distribution is highly concentrated: the Gini coefficient for logged litres among trees with at least one logged event is 0.700, and 57.9 percent of recorded litres went to the top decile of those watered trees. These statistics describe recorded platform activity, not all watering in Berlin.",
  [WATERING_TABLE, PROPOSAL],
);

// Slide 5 — downgrade existing H3-facing results to preliminary evidence.
setText("sh/58vehgvy", "PRELIMINARY PART III FINDING");
setText(
  "sh/dgbulwnm",
  "Recorded care appears better aligned with environmental than social need",
);
setNotes(
  4,
  "Treat rho = +0.486, rho = -0.123, and the ten-area screen as preliminary, descriptive, and hypothesis-generating until the vulnerability components, transformations, weights, geography, exclusions, and multiplicity handling are locked. The orange 10 is the count of Planungsräume meeting all three screening criteria—not a score and not proof of no watering. After specification lock, H3 becomes hypothesis-guided validation rather than confirmatory testing.",
  [EQUITY_ASSOCIATIONS, EQUITY_SCREEN, PROPOSAL, FEEDBACK],
);

// Slide 6 — make the weather-source division explicit.
setText(
  "sh/87ipkzal",
  "ERA5 provides primary temporal controls; DWD supplies station sensitivity and plausibility context, not LST validation.",
);
setText(
  "sh/w32twb6l",
  "ERA5: temporal controls + drought sensitivity. DWD: station context; not direct LST validation.",
);
setNotes(
  5,
  "Part I uses ERA5 for primary harmonised temporal controls: 2 m temperature, dew point or derived humidity, total precipitation, 10 m wind, surface pressure, and 7-, 14-, and 30-day antecedent summaries; moisture variables support drought sensitivity. DWD station temperature, precipitation, humidity, wind, and sunshine support sensitivity and acquisition-day plausibility context. DWD does not directly validate satellite LST. If the reproducible Landsat/Sentinel panel is not ready by the end of Month 2, freeze Part I at descriptive LST/greenness outputs plus a data audit and activate the Environmental Justice Atlas thermal layer for Part III.",
  [PROPOSAL, FEEDBACK],
);

// Slide 7 — fixed SESOI and the exposure-blind variance source.
setText(
  "sh/l0vuh0rm",
  "Primary: 30-day L/ha. SESOI: −0.03 K per +1,000 L/ha. Proceed only at ≥80% power after a blinded LST variance fit.",
);
setNotes(
  6,
  "Primary exposure is the continuous recorded 30-day dose per approximately 1-ha imagery-support unit, scaled per 1,000 L/ha; season-to-date is secondary. The SESOI is -0.03 K per additional 1,000 L/ha/30 days, equivalent to about -0.10 K for 3,500 L/ha/30 days (roughly ten adequately watered tree-month equivalents). This is a design scenario, not an assumed or published effect. Month 1 audits exposure and coverage. During Months 1–2, an outcome-only Landsat nuisance model estimates residual variance and spatial covariance without watering exposure, preferably using 2017–2019 pre-platform summers or cross-fitting; the H2 coefficient remains masked. At two-sided alpha = 0.05, confirmatory H2 proceeds only if end-Month-2 simulated power is at least 80 percent at the SESOI and the simulated MDE is no larger. Otherwise Part II is exploratory.",
  [PROPOSAL, PROJECT_CONFIG, FEEDBACK],
);

// Slide 8 — make the three schedule-protection triggers concrete.
setText(
  "sh/ri9g7uhw",
  "Three exit rules protect the guaranteed Part III minimum core.",
);
setText(
  "sh/m5gvmhwn",
  "End M2: if the LST panel is not ready, freeze descriptive thermal context.",
);
setText(
  "sh/n6pwfmd8",
  "Use EJA thermal fallback for Part III",
);
setText(
  "sh/7u5w765k",
  "End M2 gate follows an exposure-blind LST nuisance fit.",
);
setText(
  "sh/6twve1oz",
  "Go only at ≥80% power at SESOI; else audit + exploratory diagnostics",
);
setText(
  "sh/i5wva1o3",
  "End M3: protect Planungsraum + district minimum core.",
);
setText(
  "sh/x4ne1wni",
  "Pause Part II until the minimum core is secure",
);
setNotes(
  7,
  "Narrate only three exit rules. One: at end Month 2, if the Landsat/Sentinel panel is not analysis-ready, freeze Part I at descriptive thermal-context layers plus documented sensitivity checks and use the EJA thermal layer for Part III. Two: the Part II gate is run at end Month 2 after the exposure-blind LST nuisance fit; failure yields an exposure audit and exploratory diagnostics. Three: at end Month 3, if behind, defer multiscale extensions and deliver the minimum Planungsraum core—locked vulnerability index, catalogue-normalised care, denominator and weight sensitivity, and priority atlas. Pause Part II until that core is secure.",
  [PROPOSAL, PROJECT_CONFIG, FEEDBACK],
);

// Slide 9 — align the close with the now-resolved sequence.
setText(
  "sh/mdonql4z",
  "The equity foundation shows a preliminary care-gap signal. Part III is locked as the core; Part II proceeds only if the end-Month-2 gate is met.",
);
const nextAction = setText(
  "sh/9gzml0nq",
  "Next: build the blinded LST pilot, run the end-Month-2 gate, and protect the Part III core by Month 3.",
);
nextAction.text.color = "#2F7D57";
setNotes(
  8,
  "The requested decision is approval to proceed with Part III locked as the core. The immediate sequence is now resolved: build the exposure-blind Landsat nuisance panel, run the Part II gate at end Month 2, and protect the Part III minimum core by end Month 3. Describe the existing equity result as a preliminary care-gap signal.",
  [PROPOSAL, FEEDBACK],
);

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(OUTPUT);
console.log(JSON.stringify({ source: starterPptxPath, output: OUTPUT }, null, 2));
