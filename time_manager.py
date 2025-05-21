# time_manager.py
import enum
from config import CYCLES_PER_DAY, DAYS_PER_SEASON, YEAR_LENGTH_DAYS

class Season(enum.Enum):
    SPRING = "SPRING"
    SUMMER = "SUMMER"
    AUTUMN = "AUTUMN"
    WINTER = "WINTER"

class TimeManager:
    def __init__(self):
        self.current_cycle_in_day = 1 # MVP에서는 1일 1사이클
        self.current_day_in_season = 1
        self.current_season_index = 0
        self.seasons_order = [Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER]
        self.current_season = self.seasons_order[self.current_season_index]
        self.current_year = 1
        self.total_cycles_elapsed = 0

    def update(self):
        """매 시뮬레이션 틱마다 호출되어 시간 진행 로직을 처리합니다."""
        self.total_cycles_elapsed += 1
        self.current_day_in_season += 1

        if self.current_day_in_season > DAYS_PER_SEASON:
            self.current_day_in_season = 1
            self.current_season_index = (self.current_season_index + 1) % len(self.seasons_order)
            self.current_season = self.seasons_order[self.current_season_index]
            if self.current_season == Season.SPRING: # 새해가 봄에 시작
                self.current_year += 1
                return True # 연도 변경 시 True 반환
        return False # 연도 변경 없음

    def get_current_date_str(self):
        """현재 날짜 정보를 문자열로 반환합니다."""
        return f"Year: {self.current_year}, Season: {self.current_season.value}, Day: {self.current_day_in_season}"

    def get_total_days_elapsed(self):
        """시뮬레이션 시작 후 총 경과 일수를 반환합니다."""
        return self.total_cycles_elapsed // CYCLES_PER_DAY