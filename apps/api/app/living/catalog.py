"""Founder-locked definitions for NUR's seven Star Systems."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemDefinition:
    slug: str
    title: str
    definition: str
    questions: tuple[str, ...]
    checklist: tuple[str, ...]
    ignored_prediction: str
    followed_prediction: str


SYSTEMS: tuple[SystemDefinition, ...] = (
    SystemDefinition(
        slug="quiet-ambition",
        title="Quiet Ambition",
        definition=(
            "Private hunger, discipline, identity, long-range desire, self-respect, "
            "and work that matters even when nobody applauds."
        ),
        questions=(
            "What do you want but keep minimizing?",
            "What would make this week feel less wasted?",
            "What are you scared to admit you care about?",
            "What is one action nobody needs to see?",
            "Are you protecting your ambition or starving it?",
            "What would your future self be angry you ignored?",
        ),
        checklist=(
            "Define one private goal.",
            "Write why it matters.",
            "Choose one 20-minute move.",
            "Remove one performative task.",
            "Log one quiet win.",
            "Return tomorrow.",
        ),
        ignored_prediction="Open loops are likely to harden into drift and resentment.",
        followed_prediction="Repeated private movement is likely to stabilize identity and confidence.",
    ),
    SystemDefinition(
        slug="rebuild",
        title="Rebuild",
        definition=(
            "Anything damaged, collapsed, lost, neglected, or needing repair: body, "
            "mind, money, trust, relationships, rhythm, home, work, or project."
        ),
        questions=(
            "What needs rebuilding?",
            "Is it relationship, body, mind, money, work, home, project, or trust?",
            "What is still salvageable?",
            "What is not worth saving?",
            "What is the smallest stabilizing action?",
            "What keeps re-breaking it?",
            "What support or boundary is needed?",
        ),
        checklist=(
            "Name the broken area.",
            "Choose the rebuild type.",
            "Define the first repair action.",
            "Remove one repeating damage source.",
            "Create a recovery timeline.",
            "Mark the first repair.",
            "Return with an outcome.",
        ),
        ignored_prediction="The same damage source is likely to repeat without a smaller repair and boundary.",
        followed_prediction="Small stable repairs are likely to restore capacity before ambition expands.",
    ),
    SystemDefinition(
        slug="study",
        title="Study",
        definition=(
            "Deliberate learning, skill-building, research, discipline, exams, reading, "
            "practice, mastery, and understanding."
        ),
        questions=(
            "What subject or skill are you learning?",
            "What is the deadline?",
            "What do you already understand?",
            "What is confusing?",
            "What output proves learning?",
            "Do you need reading, practice, testing, or project work?",
            "What is the next 25-minute session?",
        ),
        checklist=(
            "Choose a study target.",
            "Define success proof.",
            "Create a study block.",
            "Complete one session.",
            "Summarize the learning.",
            "Test recall.",
            "Add a source or research note.",
            "Update the timeline.",
        ),
        ignored_prediction="Passive intake without retrieval or output is likely to feel productive without mastery.",
        followed_prediction="Practice plus recall evidence is likely to improve real readiness.",
    ),
    SystemDefinition(
        slug="money",
        title="Money",
        definition=(
            "Financial reality: earning, spending, debt, saving, survival, opportunity, "
            "negotiation, and economic strategy."
        ),
        questions=(
            "What money pressure exists right now?",
            "Is this debt, income, spending, saving, business, or emergency?",
            "What is urgent versus scary but not urgent?",
            "What is the smallest stabilizing action?",
            "What needs negotiation?",
            "What can generate money?",
            "What should wait because survival comes first?",
        ),
        checklist=(
            "Enter the money concern.",
            "Classify urgent versus not urgent.",
            "Create a money plan.",
            "Log one payment, settlement, or action.",
            "Create one earning task.",
            "Create a debt tracker when needed.",
            "Add the result to the timeline.",
        ),
        ignored_prediction="Unclassified pressure is likely to increase avoidance and compress options.",
        followed_prediction="One verified stabilizing or earning action is likely to improve decision room.",
    ),
    SystemDefinition(
        slug="body",
        title="Body",
        definition=(
            "Physical reality: sleep, energy, pain, movement, food, rest, medical care, "
            "load, and available capacity."
        ),
        questions=(
            "Energy from 0 to 10?",
            "Pain or load from 0 to 10?",
            "Was sleep adequate?",
            "Are food and water adequate?",
            "Is movement or rest needed?",
            "Is this a low-capacity day?",
            "What body action fits under 10 minutes?",
        ),
        checklist=(
            "Check energy.",
            "Check pain or load.",
            "Drink, eat, rest, or move.",
            "Log sleep.",
            "Create a realistic body plan.",
            "Complete one body-supporting action.",
        ),
        ignored_prediction="Plans that exceed present capacity are likely to fail or deepen depletion.",
        followed_prediction="Capacity-matched actions are likely to protect continuity and recovery.",
    ),
    SystemDefinition(
        slug="connection",
        title="Connection",
        definition=(
            "People, relationships, community, conversation, repair, support, group "
            "belonging, boundaries, and social energy."
        ),
        questions=(
            "Who are you thinking about?",
            "Is this support, conflict, repair, distance, or collaboration?",
            "What is unsaid?",
            "What is the next conversation?",
            "Does this need a boundary?",
            "Does this need a council or group NUR?",
        ),
        checklist=(
            "Add the person or orbit.",
            "Log the open conversation.",
            "Send one clear message.",
            "Attempt repair where appropriate.",
            "Set a boundary where needed.",
            "Start a council when multiple people are involved.",
            "Return the outcome.",
        ),
        ignored_prediction="Unspoken loops are likely to accumulate tension or distance.",
        followed_prediction="A clear conversation or boundary is likely to reduce relational ambiguity.",
    ),
    SystemDefinition(
        slug="creation",
        title="Creation",
        definition=(
            "Making things: art, writing, product, code, business, content, systems, "
            "projects, ideas, releases, and deliverables."
        ),
        questions=(
            "What are you making?",
            "Is it an idea, draft, prototype, product, release, content, or art?",
            "What is the current state?",
            "What proves progress?",
            "What is the smallest shippable piece?",
            "What keeps delaying release?",
            "What needs review?",
        ),
        checklist=(
            "Create the project.",
            "Define the deliverable.",
            "Create one task.",
            "Attach evidence.",
            "Run and review the work.",
            "Ship one milestone.",
            "Log the outcome.",
        ),
        ignored_prediction="The work is likely to stall in ideation, avoidance, or review without a shippable edge.",
        followed_prediction="A small reviewed deliverable is likely to turn imagination into momentum.",
    ),
)

BY_SLUG = {system.slug: system for system in SYSTEMS}
BY_TITLE = {system.title: system for system in SYSTEMS}


def require_system(slug: str) -> SystemDefinition:
    try:
        return BY_SLUG[slug]
    except KeyError as exc:
        raise KeyError(f"Unknown NUR System: {slug}") from exc
