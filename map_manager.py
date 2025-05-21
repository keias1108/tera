# map_manager.py
import random
try:
    import noise # Perlin noise
except ImportError:
    print("Warning: 'noise' library not found. Terrain generation will be random.")
    noise = None

# config에서 필요한 상수들을 가져옵니다.
from config import (MAP_WIDTH, MAP_HEIGHT, TERRAIN_NOISE_SCALE, TERRAIN_NOISE_OCTAVES,
                    TERRAIN_WATER_THRESHOLD, TERRAIN_ROCK_THRESHOLD, INITIAL_PLANT_DENSITY,
                    DEBUG_MODE, MIN_INITIAL_PLANT_DISTANCE, MAX_SOIL_WATER_LEVEL) # MAX_SOIL_WATER_LEVEL 추가
from terrain import TerrainType
from soil import SoilTile
from plant import Plant, PlantState
from plant_species import STRONG_PLANT_SPECIES

class MapManager:
    def __init__(self, width, height, climate_manager_ref, plant_group_ref):
        self.width = width
        self.height = height
        self.climate_manager = climate_manager_ref
        self.plant_group = plant_group_ref # 식물 sprite 그룹 참조
        self.game_map = [[None for _ in range(width)] for _ in range(height)]
        self._initialize_map()
        self._initialize_soil_conditions() # 초기 토양 상태 설정

    def _initialize_map(self):
        """맵 데이터 구조를 생성하고 각 셀에 SoilTile 객체를 할당 및 지형을 생성합니다."""
        print("Initializing map...")
        for r in range(self.height):
            for c in range(self.width):
                terrain_type = self._generate_terrain_type(c, r)
                self.game_map[r][c] = SoilTile(c, r, terrain_type)
        print("Map initialized.")

    def _generate_terrain_type(self, x, y):
        """주어진 좌표에 대한 지형 타입을 절차적으로 생성합니다."""
        if noise:
            # noise 라이브러리가 있을 경우 퍼린 노이즈 사용
            value = noise.pnoise2(x * TERRAIN_NOISE_SCALE,
                                  y * TERRAIN_NOISE_SCALE,
                                  octaves=TERRAIN_NOISE_OCTAVES,
                                  persistence=0.5,
                                  lacunarity=2.0,
                                  repeatx=self.width * TERRAIN_NOISE_SCALE * 2, 
                                  repeaty=self.height * TERRAIN_NOISE_SCALE * 2,
                                  base=random.randint(0, 100)) 
            
            normalized_value = (value + 0.7) / 1.4 
            normalized_value = max(0, min(1, normalized_value))

            if normalized_value < TERRAIN_WATER_THRESHOLD:
                return TerrainType.WATER
            elif normalized_value < TERRAIN_ROCK_THRESHOLD:
                return TerrainType.SOIL
            else:
                return TerrainType.ROCK
        else:
            rand_val = random.random()
            if rand_val < 0.15: 
                return TerrainType.WATER
            elif rand_val < 0.8: 
                return TerrainType.SOIL
            else: 
                return TerrainType.ROCK

    def _initialize_soil_conditions(self):
        """모든 SOIL 타입 타일의 초기 온도와 수분량을 설정합니다."""
        initial_temp, _ = self.climate_manager.update_daily_climate() # 초기값 한번 업데이트

        for r in range(self.height):
            for c in range(self.width):
                tile = self.game_map[r][c]
                if tile.terrain_type == TerrainType.SOIL:
                    tile.update_temperature(initial_temp)
                    # MAX_SOIL_WATER_LEVEL이 이제 여기서 사용 가능합니다.
                    tile.water_level = random.uniform(MAX_SOIL_WATER_LEVEL * 0.3, MAX_SOIL_WATER_LEVEL * 0.6)
                elif tile.terrain_type == TerrainType.WATER:
                    tile.water_level = MAX_SOIL_WATER_LEVEL 
                    tile.update_temperature(initial_temp) 
                else: # ROCK
                    tile.update_temperature(initial_temp)
                    tile.water_level = 0


    def initial_plant_placement(self):
        """초기 식물을 맵에 배치합니다."""
        soil_tiles_coords = []
        for r in range(self.height):
            for c in range(self.width):
                if self.game_map[r][c].terrain_type == TerrainType.SOIL:
                    soil_tiles_coords.append((c, r))
        
        if not soil_tiles_coords:
            print("Warning: No SOIL tiles found for plant placement.")
            return

        num_initial_plants = int(len(soil_tiles_coords) * INITIAL_PLANT_DENSITY)
        if DEBUG_MODE: print(f"Attempting to place {num_initial_plants} initial plants.")

        placed_plants_coords = []
        attempts = 0
        max_attempts = num_initial_plants * 10 

        while len(placed_plants_coords) < num_initial_plants and attempts < max_attempts:
            attempts += 1
            coord = random.choice(soil_tiles_coords)
            x, y = coord
            tile = self.get_tile(x,y)

            if tile and tile.can_plant_grow_here():
                too_close = False
                for px, py in placed_plants_coords:
                    distance_sq = (x - px)**2 + (y - py)**2
                    if distance_sq < MIN_INITIAL_PLANT_DISTANCE**2:
                        too_close = True
                        break
                
                if not too_close:
                    self.add_new_plant(x, y, PlantState.SEED, STRONG_PLANT_SPECIES)
                    placed_plants_coords.append((x,y))
        
        if DEBUG_MODE: print(f"Placed {len(placed_plants_coords)} plants after {attempts} attempts.")


    def add_new_plant(self, grid_x, grid_y, initial_state, species_data):
        """새로운 식물을 생성하고 맵과 그룹에 추가합니다."""
        tile = self.get_tile(grid_x, grid_y)
        if tile and tile.can_plant_grow_here():
            new_plant = Plant(grid_x, grid_y, species_data, initial_state, map_manager_ref=self)
            self.plant_group.add(new_plant)
            tile.set_occupancy(True, id(new_plant)) 
            if DEBUG_MODE and initial_state == PlantState.SEED : print(f"New seed placed at ({grid_x}, {grid_y}) by reproduction/initial.")
            return new_plant
        return None

    def get_tile(self, x, y):
        """주어진 격자 좌표의 SoilTile 객체를 반환합니다."""
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.game_map[y][x]
        return None

    def is_valid_tile(self, x, y):
        return 0 <= y < self.height and 0 <= x < self.width

    def update_map_environment(self, daily_temp, daily_rain_amount):
        """맵 전체의 토양 온도와 수분량을 업데이트합니다."""
        for r in range(self.height):
            for c in range(self.width):
                tile = self.game_map[r][c]
                tile.update_temperature(daily_temp)
                if tile.terrain_type == TerrainType.SOIL:
                    if daily_rain_amount > 0:
                        tile.add_water(daily_rain_amount) 
                    
                    evaporation_rate = 0.01 + (tile.temperature / 30.0) * 0.02 + (tile.water_level / MAX_SOIL_WATER_LEVEL) * 0.01
                    evaporation_amount = tile.water_level * evaporation_rate
                    tile.evaporate_water(max(0, evaporation_amount)) 
                
                elif tile.terrain_type == TerrainType.WATER:
                    tile.water_level = MAX_SOIL_WATER_LEVEL


    def get_average_soil_water_level(self):
        """모든 SOIL 타일의 평균 수분량을 계산합니다."""
        total_water = 0
        soil_tile_count = 0
        for r in range(self.height):
            for c in range(self.width):
                tile = self.game_map[r][c]
                if tile.terrain_type == TerrainType.SOIL:
                    total_water += tile.water_level
                    soil_tile_count += 1
        return total_water / soil_tile_count if soil_tile_count > 0 else 0