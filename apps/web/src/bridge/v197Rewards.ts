export type V197GlowTransaction = {
  id: string;
  event_type: string;
  source_kind: string;
  source_id: string;
  system_slug?: string | null;
  final_points: number;
  reason: string;
  created_at: string;
};

export type V197GlowStreak = {
  streak_key: string;
  current_count: number;
  best_count: number;
  last_event_date: string | null;
  repairs_remaining: number;
};

export type V197GlowSummary = {
  balance: number;
  lifetime_points: number;
  today_points?: number;
  weekly_points?: number;
  level?: number;
  rank?: string;
  next_unlock?: { level: number; rank: string; threshold: number; points_remaining: number } | null;
  recent_transactions: V197GlowTransaction[];
  streaks: V197GlowStreak[];
  achievements?: Array<{
    achievement_key: string;
    achievement_metadata: Record<string, unknown>;
    unlocked_at: string;
  }>;
  daily_quest?: Record<string, unknown>;
  weekly_mission?: Record<string, unknown>;
};

export type V197GlowAward = {
  awarded_points: number;
  balance: number;
  lifetime_points: number;
  idempotent_replay: boolean;
  streak: V197GlowStreak | null;
  achievements_unlocked?: string[];
};

function timeLabel(iso: string): string {
  const timestamp = Date.parse(iso);
  if (Number.isNaN(timestamp)) return "persisted";
  const days = Math.max(0, Math.floor((Date.now() - timestamp) / 86_400_000));
  if (days === 0) return "today";
  if (days === 1) return "yesterday";
  return `${days} days`;
}

function empty(node: Element): void {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function makeTodayRow(document: Document, transaction: V197GlowTransaction): HTMLElement {
  const row = document.createElement("div");
  row.className = "glow-item";
  row.dataset.glowTransactionId = transaction.id;

  const icon = document.createElement("span");
  icon.className = "glow-icon nur-v136-v89-mini-host";
  const description = document.createElement("span");
  description.textContent = `${transaction.reason} · +${transaction.final_points}`;
  const time = document.createElement("time");
  time.textContent = timeLabel(transaction.created_at);
  row.append(icon, description, time);
  return row;
}

function makeRailRow(document: Document, transaction: V197GlowTransaction): HTMLButtonElement {
  const row = document.createElement("button");
  row.type = "button";
  row.className = "v172-glow-row";
  row.dataset.glowTransactionId = transaction.id;
  row.disabled = true;

  const icon = document.createElement("span");
  icon.textContent = "✦";
  const copy = document.createElement("div");
  const title = document.createElement("b");
  title.textContent = `${transaction.reason} · +${transaction.final_points}`;
  const detail = document.createElement("small");
  detail.textContent = `Persisted · ${timeLabel(transaction.created_at)}`;
  copy.append(title, detail);
  row.append(icon, copy);
  return row;
}

/** Renders only values returned by the persisted Glow ledger. */
export function renderPersistedGlow(
  document: Document,
  summary: V197GlowSummary,
  afterRender?: () => void,
): void {
  // Hydration must never impersonate a fresh reward animation.
  void afterRender;
  const primaryStreak = summary.streaks[0];
  const todayPanel = document.querySelector<HTMLElement>("#page-today .glow-row");
  const todayHeading = document.querySelector<HTMLElement>("#page-today .today-grid > aside .panel-title");
  const todaySub = document.querySelector<HTMLElement>("#page-today .today-grid > aside .panel-sub");

  if (todayHeading) todayHeading.textContent = `${summary.balance} Glow Points · Level ${summary.level ?? 1}`;
  if (todaySub) {
    todaySub.textContent = primaryStreak
      ? `${summary.today_points ?? 0} today · ${summary.weekly_points ?? 0} this week · ${primaryStreak.current_count} day streak`
      : `${summary.today_points ?? 0} today · ${summary.weekly_points ?? 0} this week · ${summary.rank ?? "Orbit Seed"}`;
  }
  if (todayPanel) {
    empty(todayPanel);
    if (summary.recent_transactions.length === 0) {
      const emptyState = document.createElement("div");
      emptyState.className = "glow-item";
      emptyState.textContent = "No persisted Glow yet. Complete one real action.";
      todayPanel.append(emptyState);
    } else {
      summary.recent_transactions.slice(0, 3).forEach(transaction => {
        todayPanel.append(makeTodayRow(document, transaction));
      });
    }
  }

  const railCard = document.querySelector<HTMLElement>(".v172-glow-list, .clean-glows-card");
  const railHeading = railCard?.querySelector<HTMLElement>(".clean-card-heading > span");
  if (railHeading) {
    railHeading.textContent = primaryStreak
      ? `Recent Glows · ${summary.balance} · ${summary.rank ?? "Orbit Seed"} · ${primaryStreak.current_count} day streak`
      : `Recent Glows · ${summary.balance} · ${summary.rank ?? "Orbit Seed"}`;
  }
  if (railCard) {
    railCard.querySelectorAll(".v172-glow-row, .clean-glow-list > *").forEach(node => node.remove());
    const railContainer = railCard.querySelector<HTMLElement>(".clean-glow-list") ?? railCard;
    summary.recent_transactions.slice(0, 3).forEach(transaction => {
      railContainer.append(makeRailRow(document, transaction));
    });
    if (summary.recent_transactions.length === 0) {
      const emptyState = document.createElement("p");
      emptyState.className = "context-title";
      emptyState.textContent = "No persisted Glow yet.";
      railContainer.append(emptyState);
    }
  }

  const principle = document.querySelector<HTMLElement>(".v172-glow-principle .context-title");
  if (principle) principle.textContent = "Glow Points move only after the server confirms a real action.";
}

export function announcePersistedGlow(document: Document, award: V197GlowAward): void {
  if (award.idempotent_replay) return;
  const universeWindow = document.defaultView as (Window & { nurToast?: (message: string) => void }) | null;
  universeWindow?.nurToast?.(`+${award.awarded_points} Glow · ${award.balance} total`);
  const star = document.querySelector<HTMLElement>("#iSpark");
  star?.click();
}
