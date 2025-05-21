# soil.py
from terrain import TerrainType
from config import MAX_SOIL_WATER_LEVEL, INITIAL_SOIL_NUTRIENT_LEVEL

class SoilTile:
    def __init__(self, grid_x, grid_y, terrain_type=TerrainType.SOIL):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.terrain_type = terrain_type
        self.water_level = 0.0  # 초기값은 ClimateManager에서 설정
        self.temperature = 0.0 # 초기값은 ClimateManager에서 설정
        self.nutrient_level = INITIAL_SOIL_NUTRIENT_LEVEL # MVP에서는 단순 고정값
        self.is_occupied_by_plant = False
        self.plant_id = None # 해당 타일을 점유한 식물의 ID (선택적)

    def update_temperature(self, new_temp):
        """토양 온도를 업데이트합니다."""
        self.temperature = new_temp

    def add_water(self, amount):
        """토양에 수분을 추가합니다."""
        if self.terrain_type == TerrainType.SOIL:
            self.water_level = min(self.water_level + amount, MAX_SOIL_WATER_LEVEL)

    def evaporate_water(self, amount):
        """토양에서 수분을 증발시킵니다."""
        if self.terrain_type == TerrainType.SOIL:
            self.water_level = max(self.water_level - amount, 0.0)

    def consume_water(self, amount):
        """식물에 의해 수분이 소모됩니다."""
        if self.terrain_type == TerrainType.SOIL:
            consumed = min(self.water_level, amount)
            self.water_level -= consumed
            return consumed
        return 0.0

    def can_plant_grow_here(self):
        """식물이 이 타일에서 자랄 수 있는지 확인합니다."""
        return self.terrain_type == TerrainType.SOIL and not self.is_occupied_by_plant

    def set_occupancy(self, occupied: bool, plant_id=None):
        """타일의 식물 점유 상태를 설정합니다."""
        self.is_occupied_by_plant = occupied
        self.plant_id = plant_id if occupied else None

    def __repr__(self):
        return f"SoilTile({self.grid_x},{self.grid_y}, {self.terrain_type.name}, W:{self.water_level:.1f}, T:{self.temperature:.1f})"