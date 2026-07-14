export const SUPPORTED_LOCALES = [
  "en", "ur", "hi", "bn", "pa", "ar", "fa", "tr", "id", "ms",
  "zh-Hans", "zh-Hant", "ja", "ko", "vi", "th", "fil", "ta", "te",
  "mr", "gu", "kn", "ml", "ru", "uk", "pl", "de", "fr", "es", "pt",
  "it", "nl", "sv", "ro", "sw",
] as const;
export type SupportedLocale = typeof SUPPORTED_LOCALES[number];

const RTL = new Set(["ur", "fa", "ar"]);
export const POLISHED_BETA_LOCALES = ["en", "ur", "hi", "fa", "ar", "es", "fr", "zh-Hans"] as const;
const POLISHED = new Set<string>(POLISHED_BETA_LOCALES);

export type LocaleMeta = {
  locale: SupportedLocale;
  label: string;
  status: "polished_beta" | "draft_unreviewed";
  dir: "ltr" | "rtl";
};

const LABELS: Record<string, string> = {
  en: "English",
  ur: "Urdu",
  hi: "Hindi",
  bn: "Bangla",
  pa: "Punjabi",
  ar: "Arabic",
  fa: "Persian",
  tr: "Turkish",
  id: "Indonesian",
  ms: "Malay",
  "zh-Hans": "Chinese Simplified",
  "zh-Hant": "Chinese Traditional",
  ja: "Japanese",
  ko: "한국어",
  vi: "Vietnamese",
  th: "Thai",
  fil: "Filipino",
  ta: "Tamil",
  te: "Telugu",
  mr: "Marathi",
  gu: "Gujarati",
  kn: "Kannada",
  ml: "Malayalam",
  ru: "Russian",
  uk: "Ukrainian",
  pl: "Polish",
  de: "German",
  fr: "French",
  es: "Spanish",
  pt: "Portuguese",
  it: "Italian",
  nl: "Dutch",
  sv: "Swedish",
  ro: "Romanian",
  sw: "Swahili",
};

export function resolveLocale(raw: string | null | undefined): SupportedLocale {
  const value = (raw || "en").trim();
  if (SUPPORTED_LOCALES.includes(value as SupportedLocale)) return value as SupportedLocale;
  const base = value.split("-")[0];
  if (base === "zh") return "zh-Hans";
  if (SUPPORTED_LOCALES.includes(base as SupportedLocale)) return base as SupportedLocale;
  return "en";
}

export function dirForLocale(locale: string): "ltr" | "rtl" {
  return RTL.has(resolveLocale(locale)) ? "rtl" : "ltr";
}

export function writingPreferenceForLocale(locale: string): "roman" | "script" | "default" {
  const resolved = resolveLocale(locale);
  if (resolved === "ur") return "roman";
  if (RTL.has(resolved)) return "script";
  return "default";
}

const LOCALE_META_ORDER = [
  ...POLISHED_BETA_LOCALES,
  ...SUPPORTED_LOCALES.filter(locale => !POLISHED.has(locale)),
] as SupportedLocale[];

export const LOCALE_META: LocaleMeta[] = LOCALE_META_ORDER.map(locale => ({
  locale,
  label: LABELS[locale],
  status: POLISHED.has(locale) ? "polished_beta" : "draft_unreviewed",
  dir: dirForLocale(locale),
}));

export const CORE_COPY: Record<string, { privateBoundary: string; askPlaceholder: string }> = {
  en: { privateBoundary: "Private Orbit", askPlaceholder: "Say it plainly..." },
  ur: { privateBoundary: "Private Orbit", askPlaceholder: "Seedha bolo..." },
  hi: { privateBoundary: "Private Orbit", askPlaceholder: "Seedha bolo..." },
  fa: { privateBoundary: "مدار خصوصی", askPlaceholder: "روشن بگو..." },
  ar: { privateBoundary: "مدار خاص", askPlaceholder: "قلها بوضوح..." },
  es: { privateBoundary: "Orbita privada", askPlaceholder: "Dilo claramente..." },
  fr: { privateBoundary: "Orbite privee", askPlaceholder: "Dis-le simplement..." },
  "zh-Hans": { privateBoundary: "私人轨道", askPlaceholder: "直接说..." },
};

export type CriticalCopy = {
  talk: {
    kicker: string;
    title: string;
    titleEmphasis: string;
    subtitle: string;
    seed: string;
    send: string;
    holding: string;
    modeTalk: string;
    thinkDeeper: string;
    challenge: string;
    summarize: string;
    observed: string;
    inferred: string;
    hypotheses: string;
    uncertainty: string;
    nextMove: string;
    useMoveInPlan: string;
    currentThread: string;
    currentThreadSub: string;
    keepPrivate: string;
    saveToJournal: string;
    makePlan: string;
    recordWhatChanged: string;
    outcomePlaceholder: string;
    outcomeSave: string;
    outcomeSaving: string;
    onlyThisOrbit: string;
    changeBoundary: string;
    whatNurHolding: string;
    holdingPopulated: (count: number) => string;
    holdingEmpty: string;
    correctModel: string;
    correctionSub: string;
    correctionPlaceholder: string;
    saveCorrection: string;
    intentionalMixedRomanUrdu: string | null;
  };
  systems: {
    kicker: string;
    title: string;
    titleEmphasis: string;
    subtitle: string;
    activeSystems: string;
    outcomesReturned: string;
    insightsEvolving: string;
    mapLabel: string;
    mapSubtitle: string;
    addSystem: string;
    addSystemHint: string;
    systemField: string;
    ownerLedger: string;
    shareOrbit: string;
    researchField: string;
  };
  capsule: {
    kicker: string;
    activeLine: string;
    revokedLine: string;
    expiredLine: string;
    purpose: string;
    access: string;
    expires: string;
    noExpiry: string;
    included: string;
    includedSub: string;
    excluded: string;
    askTitle: string;
    askSub: string;
    askPlaceholder: string;
    ask: string;
    inactiveNote: string;
    shareTitle: string;
    shareSub: string;
    purposeLabel: string;
    purposePlaceholder: string;
    emailLabel: string;
    emailPlaceholder: string;
    capabilityLabel: string;
    readOnly: string;
    askScoped: string;
    expiryLabel: string;
    noExpiryShort: string;
    in7Days: string;
    in30Days: string;
    includedSources: string;
    emptySources: string;
    excludedNote: (count: number) => string;
    captureIntoOrbit: string;
    decisionPlaceholder: string;
    referencePlaceholder: string;
    keepDecision: string;
    keepReference: string;
    createContextCapsule: string;
    capsuleLive: string;
    roomAddress: string;
    roomSignIn: string;
    existingCapsules: string;
    revoked: string;
    activeNoExpiry: string;
    audit: string;
    revoke: string;
    accessAudit: string;
    createNeeds: string;
    createdToast: string;
    createError: string;
    revokedToast: string;
  };
};

const enCritical: CriticalCopy = {
  talk: {
    kicker: "Ask NUR",
    title: "Talk in a room",
    titleEmphasis: "that stays yours.",
    subtitle: "NUR does not carry this anywhere unless you choose it.",
    seed: "Start where the pressure is, not where the plan is.",
    send: "Send",
    holding: "Holding",
    modeTalk: "talk",
    thinkDeeper: "Think deeper",
    challenge: "challenge",
    summarize: "summarize",
    observed: "Observed",
    inferred: "Inferred",
    hypotheses: "Hypotheses",
    uncertainty: "Uncertainty",
    nextMove: "Next move",
    useMoveInPlan: "Use this move in Plan",
    currentThread: "Current thread",
    currentThreadSub: "Design continuity without burying the voice underneath it.",
    keepPrivate: "Keep private",
    saveToJournal: "Save to Journal",
    makePlan: "Make a Plan",
    recordWhatChanged: "Record what changed",
    outcomePlaceholder: "What changed in the real world?",
    outcomeSave: "Return outcome",
    outcomeSaving: "Returning",
    onlyThisOrbit: "only this Orbit",
    changeBoundary: "change boundary",
    whatNurHolding: "What NUR is holding",
    holdingPopulated: count => `${count} persisted Talk turns are available in this private ledger.`,
    holdingEmpty: "No persisted Talk turns yet. Say one true line to begin.",
    correctModel: "Correct the model",
    correctionSub: "Corrections are saved as owner-scoped evidence, not hidden prompt magic.",
    correctionPlaceholder: "What should NUR stop assuming?",
    saveCorrection: "Save correction",
    intentionalMixedRomanUrdu: null,
  },
  systems: {
    kicker: "Systems universe",
    title: "A living universe for",
    titleEmphasis: "what you are becoming.",
    subtitle: "A private Orbit when you need it. Shared systems when you choose them.",
    activeSystems: "active systems",
    outcomesReturned: "outcomes returned",
    insightsEvolving: "insights evolving",
    mapLabel: "NUR systems constellation map",
    mapSubtitle: "Neural Upgrade Rewiring",
    addSystem: "Add system",
    addSystemHint: "When a life problem needs its own sky.",
    systemField: "System field",
    ownerLedger: "owner ledger",
    shareOrbit: "Share this Orbit",
    researchField: "Research field",
  },
  capsule: {
    kicker: "Approved Context Capsule",
    activeLine: "held open, deliberately.",
    revokedLine: "has been revoked.",
    expiredLine: "has expired.",
    purpose: "Purpose",
    access: "Access",
    expires: "Expires",
    noExpiry: "No expiry — revocable at any time",
    included: "What is included",
    includedSub: "Only these approved sources exist inside this room.",
    excluded: "What is excluded",
    askTitle: "Ask about this context",
    askSub: "Answers draw only on the included sources — nothing else can be reached.",
    askPlaceholder: "Ask within the approved boundary…",
    ask: "Ask",
    inactiveNote: "The owner's boundary now closes this room. Nothing here is cached, and no answers remain readable.",
    shareTitle: "Share this Orbit, deliberately.",
    shareSub: "A Context Capsule carries only what you approve — never your life, never your voice.",
    purposeLabel: "purpose",
    purposePlaceholder: "e.g. Get a designer useful in 20 minutes",
    emailLabel: "who can access",
    emailPlaceholder: "their email — named, never public",
    capabilityLabel: "what they can do",
    readOnly: "Read only",
    askScoped: "Ask scoped questions",
    expiryLabel: "expires",
    noExpiryShort: "No expiry (revocable)",
    in7Days: "In 7 days",
    in30Days: "In 30 days",
    includedSources: "Included sources",
    emptySources: "Nothing shareable yet — capture a decision or reference below.",
    excludedNote: count => `${count} source${count === 1 ? "" : "s"} stay${count === 1 ? "s" : ""} excluded — the recipient sees the boundary, never the content.`,
    captureIntoOrbit: "Capture into this Orbit",
    decisionPlaceholder: "a decision already made…",
    referencePlaceholder: "a reference or constraint…",
    keepDecision: "keep decision",
    keepReference: "keep reference",
    createContextCapsule: "Create Context Capsule",
    capsuleLive: "Capsule live",
    roomAddress: "Room address",
    roomSignIn: "They sign in with their own Orbit; the room opens only for them.",
    existingCapsules: "Existing capsules",
    revoked: "revoked",
    activeNoExpiry: "active · no expiry",
    audit: "audit",
    revoke: "revoke",
    accessAudit: "Access audit",
    createNeeds: "A capsule needs a purpose, a named recipient, and at least one source.",
    createdToast: "Capsule created. The boundary is visible and revocable.",
    createError: "The capsule could not be created.",
    revokedToast: "Revoked. The room closed immediately.",
  },
};

export const CRITICAL_COPY: Record<string, CriticalCopy> = {
  en: enCritical,
  ur: {
    ...enCritical,
    talk: {
      ...enCritical.talk,
      kicker: "NUR se baat",
      title: "Apne kamray mein baat",
      titleEmphasis: "jo tera rehta hai.",
      subtitle: "NUR isay kahin nahi le jata jab tak tu khud na chahay.",
      seed: "Jahan pressure hai wahan se shuru kar, plan wali acting se nahi.",
      send: "Bhej",
      holding: "Hold ho raha",
      modeTalk: "baat",
      thinkDeeper: "Aur gehra soch",
      challenge: "challenge kar",
      summarize: "summary bana",
      observed: "Jo dekha",
      inferred: "Jo infer hua",
      hypotheses: "Imkan",
      uncertainty: "Jo unsure hai",
      nextMove: "Agla qadam",
      useMoveInPlan: "Is qadam ko Plan mein daal",
      currentThread: "Current thread",
      currentThreadSub: "Continuity bana, magar awaaz ko daba ke nahi.",
      keepPrivate: "Private rakho",
      saveToJournal: "Journal mein rakho",
      makePlan: "Plan banao",
      recordWhatChanged: "Record what changed",
      outcomePlaceholder: "Asal duniya mein kya badla?",
      outcomeSave: "Outcome return karo",
      outcomeSaving: "Return ho raha",
      onlyThisOrbit: "sirf yeh Orbit",
      changeBoundary: "boundary badlo",
      whatNurHolding: "NUR kya hold kar raha hai",
      holdingPopulated: count => `${count} persisted Talk turns is private ledger mein hain.`,
      holdingEmpty: "Abhi koi persisted Talk turn nahi. Aik sachchi line bol ke shuru kar.",
      correctModel: "Model ko correct kar",
      correctionSub: "Corrections owner-scoped evidence hain, chhupa hua prompt magic nahi.",
      correctionPlaceholder: "NUR kya assume na kare?",
      saveCorrection: "Correction save karo",
      intentionalMixedRomanUrdu: "Roman Urdu preference: product terms jaise NUR, Orbit, Talk, Plan intentional mixed writing mein rehte hain.",
    },
    systems: { ...enCritical.systems, kicker: "Systems universe", title: "Zinda universe", titleEmphasis: "jo tu ban rahi hai.", addSystem: "System add kar", shareOrbit: "Yeh Orbit share kar" },
    capsule: { ...enCritical.capsule, kicker: "Approved Context Capsule", activeLine: "khula hai, jaan-boojh kar.", revokedLine: "revoke ho chuka hai.", expiredLine: "expire ho chuka hai.", ask: "Pooch", shareTitle: "Yeh Orbit jaan-boojh kar share kar.", purposeLabel: "maqsad", emailLabel: "kis ko access hai", createContextCapsule: "Context Capsule banao", revoked: "revoke ho gaya", audit: "audit", revoke: "revoke" },
  },
  hi: {
    ...enCritical,
    talk: { ...enCritical.talk, kicker: "NUR se baat", title: "Apne room mein baat", titleEmphasis: "jo tumhara rehta hai.", send: "Bhejo", thinkDeeper: "Aur gehra socho" },
    systems: { ...enCritical.systems, title: "Ek zinda universe", titleEmphasis: "jo tum ban rahe ho.", addSystem: "System jodo" },
    capsule: { ...enCritical.capsule, activeLine: "khula hai, jaan-boojh kar.", ask: "Poochho", shareTitle: "Is Orbit ko jaan-boojh kar share karo.", createContextCapsule: "Context Capsule banao" },
  },
  fa: {
    ...enCritical,
    talk: { ...enCritical.talk, kicker: "از NUR بپرس", title: "در اتاقی حرف بزن", titleEmphasis: "که برای تو می‌ماند.", send: "ارسال", holding: "در حال نگه‌داشتن", thinkDeeper: "عمیق‌تر فکر کن" },
    systems: { ...enCritical.systems, title: "یک جهان زنده برای", titleEmphasis: "آنچه می‌شوی.", activeSystems: "سیستم فعال", addSystem: "افزودن سیستم", shareOrbit: "اشتراک این مدار" },
    capsule: { ...enCritical.capsule, kicker: "کپسول زمینه تاییدشده", activeLine: "آگاهانه باز نگه داشته شده.", revokedLine: "لغو شده است.", expiredLine: "منقضی شده است.", ask: "بپرس", shareTitle: "این مدار را آگاهانه به اشتراک بگذار.", purposeLabel: "هدف", emailLabel: "چه کسی دسترسی دارد", createContextCapsule: "ساخت کپسول زمینه", revoked: "لغو شده", audit: "بازرسی", revoke: "لغو" },
  },
  ar: {
    ...enCritical,
    talk: { ...enCritical.talk, kicker: "اسأل NUR", title: "تحدث في غرفة", titleEmphasis: "تبقى لك.", send: "إرسال", holding: "جار الحفظ", thinkDeeper: "فكر بعمق" },
    systems: { ...enCritical.systems, title: "كون حي لما", titleEmphasis: "تصير إليه.", activeSystems: "أنظمة نشطة", addSystem: "أضف نظاما", shareOrbit: "شارك هذا المدار" },
    capsule: { ...enCritical.capsule, kicker: "كبسولة سياق معتمدة", activeLine: "مفتوحة عمدا.", revokedLine: "تم إلغاؤها.", expiredLine: "انتهت صلاحيتها.", ask: "اسأل", shareTitle: "شارك هذا المدار بوضوح.", purposeLabel: "الغرض", emailLabel: "من يمكنه الوصول", createContextCapsule: "أنشئ كبسولة سياق", revoked: "ملغى", audit: "تدقيق", revoke: "إلغاء" },
  },
  es: {
    ...enCritical,
    talk: { ...enCritical.talk, kicker: "Pregunta a NUR", title: "Habla en una sala", titleEmphasis: "que sigue siendo tuya.", send: "Enviar", holding: "Guardando", thinkDeeper: "Pensar mas profundo" },
    systems: { ...enCritical.systems, title: "Un universo vivo para", titleEmphasis: "lo que estas llegando a ser.", activeSystems: "sistemas activos", addSystem: "Agregar sistema", shareOrbit: "Compartir este Orbit" },
    capsule: { ...enCritical.capsule, kicker: "Capsula de contexto aprobada", activeLine: "abierta deliberadamente.", revokedLine: "ha sido revocada.", expiredLine: "ha expirado.", ask: "Preguntar", shareTitle: "Comparte este Orbit deliberadamente.", purposeLabel: "proposito", emailLabel: "quien puede acceder", createContextCapsule: "Crear Context Capsule", revoked: "revocada", audit: "auditoria", revoke: "revocar" },
  },
  fr: {
    ...enCritical,
    talk: { ...enCritical.talk, kicker: "Demander a NUR", title: "Parle dans une piece", titleEmphasis: "qui reste a toi.", send: "Envoyer", holding: "En cours", thinkDeeper: "Penser plus loin" },
    systems: { ...enCritical.systems, title: "Un univers vivant pour", titleEmphasis: "ce que tu deviens.", activeSystems: "systemes actifs", addSystem: "Ajouter un systeme", shareOrbit: "Partager cet Orbit" },
    capsule: { ...enCritical.capsule, kicker: "Capsule de contexte approuvee", activeLine: "ouverte deliberement.", revokedLine: "a ete revoquee.", expiredLine: "a expire.", ask: "Demander", shareTitle: "Partager cet Orbit deliberement.", purposeLabel: "objectif", emailLabel: "qui peut acceder", createContextCapsule: "Creer Context Capsule", revoked: "revoquee", audit: "audit", revoke: "revoquer" },
  },
  "zh-Hans": {
    ...enCritical,
    talk: { ...enCritical.talk, kicker: "询问 NUR", title: "在一个房间里说", titleEmphasis: "它仍属于你。", send: "发送", holding: "正在保存", thinkDeeper: "深入思考" },
    systems: { ...enCritical.systems, title: "一个活的宇宙", titleEmphasis: "承载你正在成为的样子。", activeSystems: "活跃系统", addSystem: "添加系统", shareOrbit: "分享此轨道" },
    capsule: { ...enCritical.capsule, kicker: "已批准的上下文胶囊", activeLine: "被有意保持开放。", revokedLine: "已被撤销。", expiredLine: "已过期。", ask: "询问", shareTitle: "有意分享此轨道。", purposeLabel: "目的", emailLabel: "谁可以访问", createContextCapsule: "创建上下文胶囊", revoked: "已撤销", audit: "审计", revoke: "撤销" },
  },
};

for (const locale of SUPPORTED_LOCALES) {
  CORE_COPY[locale] ??= CORE_COPY.en;
  CRITICAL_COPY[locale] ??= enCritical;
}
