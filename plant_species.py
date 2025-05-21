# plant_species.py

# 강인한 단일 종의 특성 데이터
STRONG_PLANT_SPECIES = {
    "species_name": "Resilient Herb",
    "optimal_growth_temperature": (15.0, 28.0),  # (최적 범위 시작, 끝) ℃
    "min_survival_temperature": -5.0,  # ℃
    "max_survival_temperature": 40.0,  # ℃
    "optimal_soil_water_level": (30.0, 70.0), # (최적 범위 시작, 끝) mm
    "min_survival_soil_water_level": 5.0,    # mm (토양 수분 조건)
    "max_lifespan_cycles": 3 * 360,  # 최대 수명 (3년)
    "seed_viability_duration_cycles": 360, # 씨앗 발아 가능 기간 (일)
    "min_water_for_germination_soil": 15.0, # 씨앗 발아 최소 토양 수분량 (mm)
    "min_temperature_for_germination": 12.0, # 씨앗 발아 최소 온도 (℃)
    "max_water_capacity_factor_size": 2.0,   # 크기 1.0일 때 최대 내부 수분 저장량 (내부 단위)
    "max_energy_capacity_factor_size": 2.0,  # 크기 1.0일 때 최대 내부 에너지 저장량 (내부 단위)
    "base_growth_rate_factor": 0.05,         # 기본 성장률 계수 (크기 단위 / cycle)
    "default_target_size_for_adult": 0.28,    # 성체로 간주되는 최소 크기 (0.0 ~ 1.0)
    "maturity_age_cycles": int(0.3 * 360),     # 성숙하여 번식 가능한 최소 나이 (0.5년)
    "energy_cost_per_seed_attempt": 0.5,     # 씨앗 1개 생산 시도에 드는 에너지 비용
    "max_seeds_produced_per_attempt": 3,     # 번식 시도당 최대 씨앗 생산 개수
    "reproduction_cooldown_cycles_default": 30, # 기본 번식 쿨다운 (일)
    "sapling_max_size": 0.29, # 유묘 단계의 최대 크기
    "adult_max_size": 1.0, # 성체의 최대 크기 (정규화)
}