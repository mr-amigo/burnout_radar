# ============================================================
# BURNOUT.PY — Burnout Index Calculator
# Джерела:
# [1] Kiss & Pikó (2025) — BMC Medical Education
# [2] Åkerstedt et al. (2012) — Sleep deprivation and burnout
# [3] Freitas et al. (2025) — MDPI Behavioral Sciences
# ============================================================

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DailyInput:
    mood:             float
    mental_energy:    float
    physical_energy:  float
    sleep_hours:      float
    hydration:        float
    screen_time:      float
    movement_min:     float
    total_task_hours: float
    avg_difficulty:   float
    tasks_total:      int
    tasks_completed:  int
    reflection_text:  Optional[str] = None


@dataclass
class BurnoutResult:
    index:           float
    level:           str
    components:      dict = field(default_factory=dict)
    recommendations: list = field(default_factory=list)


def calculate_burnout(data: DailyInput) -> BurnoutResult:

    # ── РИЗИК-ФАКТОРИ ──
    mood_risk        = (5.0 - data.mood) * 8.0
    mental_risk      = (100.0 - data.mental_energy) * 0.20
    sleep_deficit    = max(0.0, 8.0 - data.sleep_hours)
    sleep_risk       = sleep_deficit * 4.0
    workload_risk    = min(data.total_task_hours / 8.0, 1.5) * 10.0
    difficulty_risk  = (data.avg_difficulty - 1.0) * (15.0 / 4.0)
    incomplete_ratio = (data.tasks_total - data.tasks_completed) / data.tasks_total if data.tasks_total > 0 else 0.0
    amotivation_risk = incomplete_ratio * 15.0
    screen_risk      = min(max(0.0, data.screen_time - 4.0), 8.0)

    # ── ЗАХИСНІ ФАКТОРИ ──
    phys_protection  = (data.physical_energy / 100.0) * 10.0
    move_protection  = min(data.movement_min, 60.0) * 0.10
    hyd_protection   = min(data.hydration, 8.0) * 0.50

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
        recommendations.append("😴 Ти спиш менше 4 годин. Це головна причина виснаження.")
    elif sleep_risk > 8:
        recommendations.append("🌙 Дефіцит сну підвищує ризик вигорання. Рекомендовано 7–8 годин.")

    if mood_risk > 24:
        recommendations.append("💙 Твій настрій дуже низький. Спробуй коротку практику вдячності.")

    if amotivation_risk > 10:
        recommendations.append("✅ Багато незавершених задач. Спробуй розбити їх на менші кроки.")

    if workload_risk > 8:
        recommendations.append("⚠️ Важке навантаження (8+ годин задач). Заплануй паузи кожні 90 хвилин.")

    if screen_risk > 4:
        recommendations.append("📱 Час перед екраном перевищує норму. Спробуй digital detox ввечері.")

    if move_protection < 3:
        recommendations.append("🏃 Мало руху. Навіть 15-хвилинна прогулянка знижує стрес.")

    if not recommendations:
        recommendations.append("✨ Чудовий день! Продовжуй у тому ж темпі.")

    return BurnoutResult(
        index=round(index, 1),
        level=level,
        components=components,
        recommendations=recommendations,
    )
