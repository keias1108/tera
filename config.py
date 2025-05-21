# config.py

# 화면 설정
SCREEN_WIDTH = 1200  # 화면 너비
SCREEN_HEIGHT = 800  # 화면 높이
GRID_SIZE = 8       # 각 셀의 크기 (픽셀)
INFO_PANEL_HEIGHT = 150 # 정보 패널 높이
GAME_AREA_HEIGHT = SCREEN_HEIGHT - INFO_PANEL_HEIGHT # 실제 게임 영역 높이

# 맵 크기 (셀 단위)
MAP_WIDTH = 100
MAP_HEIGHT = int(GAME_AREA_HEIGHT / GRID_SIZE) # 화면에 맞게 맵 높이 조정

# 시뮬레이션 시간 설정
SIMULATION_CYCLES_PER_SECOND = 10  # 1초에 진행될 시뮬레이션 cycle 수
CYCLES_PER_DAY = 1 # 1 cycle = 1일
DAYS_PER_SEASON = 90 # 각 계절의 기본 지속 기간 (일)
YEAR_LENGTH_DAYS = DAYS_PER_SEASON * 4 # 1년 (일)

# 지형 생성 파라미터
TERRAIN_NOISE_SCALE = 0.1
TERRAIN_NOISE_OCTAVES = 3
TERRAIN_WATER_THRESHOLD = 0.3
TERRAIN_ROCK_THRESHOLD = 0.8

# 토양 관련 파라미터
MAX_SOIL_WATER_LEVEL = 100.0  # mm, 최대 토양 수분량
INITIAL_SOIL_NUTRIENT_LEVEL = 50.0 # MVP에서는 고정값 또는 단순화

# 기후 파라미터
# 계절별 평균 기온 (℃)
SEASON_AVG_TEMPS = {
    "SPRING": 12.5,
    "SUMMER": 26.5,
    "AUTUMN": 15.0,
    "WINTER": 0.5
}
# 계절별 일교차 범위 (최저/최고 오프셋)
SEASON_TEMP_VARIATION = {
    "SPRING": (-5.0, 5.0),
    "SUMMER": (-4.0, 4.0),
    "AUTUMN": (-6.0, 6.0),
    "WINTER": (-4.0, 4.0)
}
YEARLY_AVG_TEMP_FLUCTUATION_RANGE = (-1.5, 1.5) # 연간 평균 기온 변동폭 (℃)

# 계절별 강수 빈도 (주당 평균 횟수) 및 양 (mm)
# (빈도, 평균양, [폭우 빈도, 폭우 시 추가량])
SEASON_RAINFALL_PATTERNS = {
    "SPRING": (1.5 / 7, 10.0, 0.05 / 7, 15.0), # (일일 확률, 평균양, 일일 폭우 확률, 폭우 추가량)
    "SUMMER": (3.0 / 7, 30.0, 0.1 / 7, 25.0),
    "AUTUMN": (1.5 / 30, 7.5, 0.02 / 30, 10.0), # 월 1.5회 -> 일일 확률로 변환
    "WINTER": (0.5 / 30, 3.0, 0.0, 0.0)  # 월 0.5회 -> 일일 확률로 변환
}
YEARLY_RAINFALL_FLUCTUATION_RANGE = (-0.2, 0.2) # 연간 총 강수량 변동폭 (비율)

# 계절별 낮 길이 비율 (0.0 ~ 1.0)
DAY_LENGTH_RATIOS = {
    "SPRING": 0.5,
    "SUMMER": 0.6,
    "AUTUMN": 0.5,
    "WINTER": 0.4
}

# 식물 관련 파라미터
INITIAL_PLANT_DENSITY = 0.02  # 초기 식물 밀도 (SOIL 셀 중 비율)

# 식물 시각화 색상 (RGB)
PLANT_COLORS = {
    "SEED": (50, 50, 50),       # 어두운 회색
    "SAPLING": (100, 200, 100), # 연두색
    "ADULT_STAGE_1": (0, 180, 0),
    "ADULT_STAGE_2": (0, 150, 0),
    "ADULT_STAGE_3": (0, 120, 0),
    "ADULT_STAGE_4": (0, 100, 0),
    "ADULT_STAGE_5": (0, 80, 0),
    "DEAD": (30, 30, 30)        # 매우 어두운 회색/검은색
}

# 토양 시각화 색상 (RGB)
TERRAIN_COLORS = {
    "WATER": (0, 100, 200),
    "ROCK": (120, 120, 120),
    "SOIL_DRY": (139, 69, 19),      # 매우 건조한 흙 (진한 갈색)
    "SOIL_MOIST_1": (160, 82, 45),  # 약간 건조
    "SOIL_MOIST_2": (101, 67, 33),  # 적당한 수분 (중간 갈색)
    "SOIL_MOIST_3": (85, 56, 25),   # 축축함
    "SOIL_WET": (60, 40, 20)        # 매우 축축함 (어두운 갈색)
}
SOIL_COLOR_STEPS = 5 # 수분량에 따른 토양 색상 단계 수

# 정보 패널 폰트
INFO_FONT_SIZE = 18
INFO_FONT_COLOR = (255, 255, 255)
INFO_LINE_SPACING = 20

# 초기 식물 배치 시 최소 안전 거리 (셀 단위) - 군집화 방지
MIN_INITIAL_PLANT_DISTANCE = 3

# 식물 생존 및 성장
MIN_HEALTH_FOR_SURVIVAL = 0.1 # 최소 생존 건강
ENERGY_COST_FOR_MAINTENANCE_PER_CYCLE = 0.05 # 크기 1.0 기준 생명 유지 에너지 소모량
WATER_COST_FOR_MAINTENANCE_PER_CYCLE = 0.02 # 크기 1.0 기준 생명 유지 수분 소모량
PHOTOSYNTHESIS_BASE_EFFICIENCY = 0.1 # 기본 광합성 효율
WATER_ABSORPTION_RATE = 0.1 # 토양에서 물 흡수율 (가용 수분 대비)
STRESS_DAMAGE_RATE = 5.0 # 환경 스트레스 시 건강 감소율
HEALING_RATE_UNDER_OPTIMAL_CONDITIONS = 2.0 # 최적 환경에서 건강 회복률
SEED_DEATH_CHANCE_PER_CYCLE_IF_UNABLE_TO_GERMINATE = 0.01 # 발아 불가시 씨앗 사망 확률

# 식물 성장
SAPLING_TO_ADULT_GROWTH_PER_CYCLE = 0.01 # 유묘 -> 성체 기본 성장량 (사이즈)
ADULT_MAX_SIZE_VARIATION = 0.2 # 성체 최대 크기 편차 (종 특성 대비 +/-)

# 식물 번식
SEED_SPREAD_RADIUS_MAX = 5 # 씨앗 최대 확산 반경 (셀)
SEED_SPREAD_RADIUS_MIN = 1
REPRODUCTION_ENERGY_THRESHOLD_FACTOR = 0.8 # 최대 에너지 대비 번식 시도 가능 에너지 비율
REPRODUCTION_WATER_THRESHOLD_FACTOR = 0.6 # 최대 수분 대비 번식 시도 가능 수분 비율

# 식물 죽음
DEAD_PLANT_REMOVAL_CYCLES = 90 # 죽은 식물이 맵에서 사라지기까지의 시간

# 디버그 모드
DEBUG_MODE = False