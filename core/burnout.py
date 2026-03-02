# ============================================================
# BURNOUT.PY — Burnout Index Calculator
# Адаптовано під моделі: Task, HealthLog, MoodEntry
# Джерела:
# [1] Kiss & Pikó (2025) — BMC Medical Education
# [2] Åkerstedt et al. (2012) — Sleep deprivation and burnout
# [3] Freitas et al. (2025) — MDPI Behavioral Sciences
# ============================================================

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DailyInput:
    mood:             float  # 1-5
    mental_energy:    float  # 1-10
    physical_energy:  float  # 1-10
    sleep_hours:      float
    water_ml:         int    # мілілітри
    screen_time:      float  # години
    steps:            int
    total_task_hours: float  # години (duration/60)
    avg_difficulty:   float  # 1-5
    tasks_total:      int
    tasks_completed:  int


@dataclass
class BurnoutResult:
    index:           float
    level:           str
    components:      dict = field(default_factory=dict)
    recommendations: list = field(default_factory=list)


def calculate_burnout(data: DailyInput) -> BurnoutResult:

    # ── РИЗИК-ФАКТОРИ ──

    # Настрій (макс 32)
    mood_risk = (5.0 - data.mood) * 8.0

    # Ментальна енергія 1-10 → нормалізуємо до 0-100
    mental_pct = (data.mental_energy - 1) / 9 * 100
    mental_risk = (100.0 - mental_pct) * 0.20

    # Сон (макс 32)
    sleep_deficit = max(0.0, 8.0 - data.sleep_hours)
    sleep_risk = sleep_deficit * 4.0

    # Навантаження задачами (макс 15)
    workload_risk = min(data.total_task_hours / 8.0, 1.5) * 10.0

    # Складність задач (макс 15)
    difficulty_risk = (data.avg_difficulty - 1.0) * (15.0 / 4.0)

    # Незавершені задачі (макс 15)
    incomplete_ratio = (data.tasks_total - data.tasks_completed) / data.tasks_total if data.tasks_total > 0 else 0.0
    amotivation_risk = incomplete_ratio * 15.0

    # Екранний час понад 6h (макс 8)
    screen_risk = min(max(0.0, data.screen_time - 6.0), 8.0)

    # ── ЗАХИСНІ ФАКТОРИ ──

    # Фізична енергія 1-10 → нормалізуємо до 0-100
    physical_pct = (data.physical_energy - 1) / 9 * 100
    phys_protection = (physical_pct / 100.0) * 10.0

    # Кроки (макс 6)
    if data.steps >= 7000:
        move_protection = 6.0
    elif data.steps >= 3000:
        move_protection = 3.0
    else:
        move_protection = 0.0

    # Гідрація (макс 4)
    if data.water_ml >= 2000:
        hyd_protection = 4.0
    elif data.water_ml >= 1500:
        hyd_protection = 2.0
    else:
        hyd_protection = 0.0

    # ── РОЗРАХУНОК ──
    total_risk       = mood_risk + mental_risk + sleep_risk + workload_risk + difficulty_risk + amotivation_risk + screen_risk
    total_protection = phys_protection + move_protection + hyd_protection
    raw_score        = total_risk - total_protection

    RAW_MAX = 100.0
    RAW_MIN = -20.0
    index   = (raw_score - RAW_MIN) / (RAW_MAX - RAW_MIN) * 100.0
    index   = max(0.0, min(100.0, index))

    # ── РІВЕНЬ ──
    if index < 34:
        level = "Low"
    elif index < 67:
        level = "Moderate"
    else:
        level = "High"

    # ── КОМПОНЕНТИ ──
    components = {
        "mood_risk":            round(mood_risk, 1),
        "mental_risk":          round(mental_risk, 1),
        "sleep_risk":           round(sleep_risk, 1),
        "workload_risk":        round(workload_risk, 1),
        "difficulty_risk":      round(difficulty_risk, 1),
        "amotivation_risk":     round(amotivation_risk, 1),
        "screen_risk":          round(screen_risk, 1),
        "phys_protection":      round(-phys_protection, 1),
        "move_protection":      round(-move_protection, 1),
        "hyd_protection":       round(-hyd_protection, 1),
        "raw_score":            round(raw_score, 1),
    }

    # ── РЕКОМЕНДАЦІЇ ──
    recommendations = []

    if sleep_risk > 16:
        recommendations.append("😴 You slept less than 4 hours — this is the leading cause of exhaustion.")
    elif sleep_risk > 8:
        recommendations.append("🌙 Sleep deficit increases burnout risk. Aim for 7–8 hours.")

    if mood_risk > 24:
        recommendations.append("💙 Your mood is very low. Try a short gratitude practice or talk to a friend.")

    if amotivation_risk > 10:
        recommendations.append("✅ Many incomplete tasks. Try breaking them into smaller steps.")

    if workload_risk > 8:
        recommendations.append("⚠️ Heavy workload (8+ hours of tasks). Plan breaks every 90 minutes.")

    if screen_risk > 4:
        recommendations.append("📱 Screen time is above normal. Try a digital detox in the evening.")

    if move_protection == 0:
        recommendations.append("🏃 Very little movement today. Even a 15-minute walk reduces stress.")

    if not recommendations:
        recommendations.append("✨ Great day! All indicators look good. Keep it up!")

    return BurnoutResult(
        index=round(index, 1),
        level=level,
        components=components,
        recommendations=recommendations,
    )
