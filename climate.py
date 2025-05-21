# climate.py
import random
from config import (SEASON_AVG_TEMPS, SEASON_TEMP_VARIATION, YEARLY_AVG_TEMP_FLUCTUATION_RANGE,
                    SEASON_RAINFALL_PATTERNS, YEARLY_RAINFALL_FLUCTUATION_RANGE, DAY_LENGTH_RATIOS, DEBUG_MODE)
from time_manager import Season

class ClimateManager:
    def __init__(self, time_manager_ref):
        self.time_manager = time_manager_ref
        self.current_yearly_temp_offset = 0.0
        self.current_yearly_rainfall_multiplier = 1.0
        self.current_daily_temperature = 0.0
        self.last_rainfall_info = {"occurred": False, "amount": 0.0, "day": 0, "season": ""}

        self.apply_yearly_fluctuations() # 초기 연간 변동성 적용
        self.update_daily_climate()     # 초기 일일 기후 설정

    def apply_yearly_fluctuations(self):
        """매년 시작 시 호출되어 연간 평균 기온 및 강수량 변동성을 적용합니다."""
        self.current_yearly_temp_offset = random.uniform(*YEARLY_AVG_TEMP_FLUCTUATION_RANGE)
        self.current_yearly_rainfall_multiplier = 1.0 + random.uniform(*YEARLY_RAINFALL_FLUCTUATION_RANGE)
        if DEBUG_MODE:
            print(f"Year {self.time_manager.current_year}: Temp Offset: {self.current_yearly_temp_offset:.2f}C, Rainfall Multiplier: {self.current_yearly_rainfall_multiplier:.2f}x")


    def update_daily_climate(self):
        """매일(cycle) 호출되어 해당 일의 기온을 계산하고, 토양 객체에 적용합니다.
           강수 이벤트도 처리합니다.
        """
        current_season_enum = self.time_manager.current_season
        current_season_str = current_season_enum.value # Enum 값을 문자열로 사용

        # 1. 일일 온도 계산
        base_avg_temp = SEASON_AVG_TEMPS[current_season_str]
        temp_variation_min, temp_variation_max = SEASON_TEMP_VARIATION[current_season_str]
        
        # 계절 내 날짜 진행에 따른 온도 변화 (사인파 유사 패턴 - 단순화)
        # 봄/가을: 중간에서 시작하여 최고/최저점 찍고 다시 중간으로
        # 여름: 초반에 빠르게 상승하여 높은 온도 유지
        # 겨울: 초반에 빠르게 하강하여 낮은 온도 유지
        # MVP에서는 각 날의 평균 온도를 사용하거나, 간단한 변동만 적용
        # 여기서는 해당 계절 평균 + 연간 오프셋 + 일일 무작위 변동으로 단순화
        daily_random_offset = random.uniform(temp_variation_min / 2, temp_variation_max / 2) # 일교차의 일부를 일일 변동으로
        self.current_daily_temperature = base_avg_temp + self.current_yearly_temp_offset + daily_random_offset
        
        # 2. 강수 이벤트 처리
        self.last_rainfall_info["occurred"] = False # 기본적으로 비 안옴
        rainfall_pattern = SEASON_RAINFALL_PATTERNS[current_season_str]
        daily_rain_chance, avg_rain_amount, daily_heavy_rain_chance, heavy_rain_extra = rainfall_pattern

        rain_amount_today = 0
        if random.random() < (daily_rain_chance * self.current_yearly_rainfall_multiplier) : # 연간 강수량 변동 적용
            rain_amount_today = random.uniform(avg_rain_amount * 0.5, avg_rain_amount * 1.5)
            if random.random() < daily_heavy_rain_chance: # 폭우 확률
                rain_amount_today += random.uniform(heavy_rain_extra * 0.5, heavy_rain_extra * 1.5)
            
            rain_amount_today *= self.current_yearly_rainfall_multiplier # 최종 강수량에도 연간 변동 적용
            rain_amount_today = max(0, rain_amount_today) # 음수 방지

        if rain_amount_today > 0:
            self.last_rainfall_info = {
                "occurred": True,
                "amount": rain_amount_today,
                "day": self.time_manager.current_day_in_season,
                "season": current_season_str
            }
            if DEBUG_MODE:
                print(f"Rainfall: {rain_amount_today:.2f}mm on Year {self.time_manager.current_year}, {current_season_str}, Day {self.time_manager.current_day_in_season}")
        
        return self.current_daily_temperature, rain_amount_today


    def get_day_length_ratio(self, season_enum):
        """현재 계절의 낮 길이 비율을 반환합니다."""
        return DAY_LENGTH_RATIOS[season_enum.value]

    def get_last_rainfall_info_str(self):
        if self.last_rainfall_info["occurred"] and self.last_rainfall_info["day"] == self.time_manager.current_day_in_season:
             return f"Last Rain: Today! {self.last_rainfall_info['amount']:.1f}mm"
        elif self.last_rainfall_info["amount"] > 0: # 과거에 비가 왔었다면
            return f"Last Rain: Y{self.time_manager.current_year}, {self.last_rainfall_info['season']} D{self.last_rainfall_info['day']}, {self.last_rainfall_info['amount']:.1f}mm"
        return "Last Rain: None yet"