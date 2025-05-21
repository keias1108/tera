# plant.py
import pygame
import enum
import random
from config import (PLANT_COLORS, GRID_SIZE, MIN_HEALTH_FOR_SURVIVAL,
                    ENERGY_COST_FOR_MAINTENANCE_PER_CYCLE, WATER_COST_FOR_MAINTENANCE_PER_CYCLE,
                    PHOTOSYNTHESIS_BASE_EFFICIENCY, WATER_ABSORPTION_RATE,
                    STRESS_DAMAGE_RATE, HEALING_RATE_UNDER_OPTIMAL_CONDITIONS,
                    SAPLING_TO_ADULT_GROWTH_PER_CYCLE, REPRODUCTION_ENERGY_THRESHOLD_FACTOR,
                    REPRODUCTION_WATER_THRESHOLD_FACTOR, SEED_DEATH_CHANCE_PER_CYCLE_IF_UNABLE_TO_GERMINATE,
                    DEAD_PLANT_REMOVAL_CYCLES, DEBUG_MODE)
from plant_species import STRONG_PLANT_SPECIES # 기본 종 특성 가져오기

class PlantState(enum.Enum):
    SEED = "SEED"
    SAPLING = "SAPLING"
    ADULT = "ADULT"
    DEAD = "DEAD"

class Plant(pygame.sprite.Sprite):
    def __init__(self, grid_x, grid_y, species_data=None, initial_state=PlantState.SEED, map_manager_ref=None):
        super().__init__()
        self.species_data = species_data if species_data else STRONG_PLANT_SPECIES # 종 특성
        self.map_manager = map_manager_ref # 맵 매니저 참조

        self.grid_x = grid_x
        self.grid_y = grid_y
        self.age = 0  # cycles 단위 나이
        self.health = 100.0
        self.current_state = initial_state
        self.current_size = 0.01 if initial_state == PlantState.SEED else 0.05 # 초기 크기
        
        self.target_size_for_adult = self.species_data["default_target_size_for_adult"]
        # 성체 최대 크기에 약간의 변동성을 줌
        adult_max_size_base = self.species_data["adult_max_size"]
        self.adult_max_size_actual = random.uniform(
            adult_max_size_base * (1 - 0.1), # ADULT_MAX_SIZE_VARIATION 대신 임의값 사용
            adult_max_size_base * (1 + 0.1)
        )


        self.max_water_capacity = self.current_size * self.species_data["max_water_capacity_factor_size"]
        self.current_water = self.max_water_capacity * 0.5 # 초기 수분
        self.max_energy_capacity = self.current_size * self.species_data["max_energy_capacity_factor_size"]
        self.current_energy = self.max_energy_capacity * 0.5 # 초기 에너지

        self.growth_rate_factor = self.species_data["base_growth_rate_factor"]
        self.reproduction_cooldown = 0
        self.cycles_since_death = 0 # 죽은 후 경과 시간

        self.image = None # 시각화는 Visualization 모듈에서 처리하거나 여기서 직접 생성
        self.rect = None
        self._update_visuals() # 초기 시각화 설정

        if DEBUG_MODE: print(f"Plant created at ({grid_x},{grid_y}), State: {initial_state}")

    def _update_visuals(self):
        """식물의 현재 상태와 크기에 맞게 image와 rect를 업데이트합니다."""
        pixel_size = 0
        color = PLANT_COLORS["DEAD"]

        if self.current_state == PlantState.SEED:
            pixel_size = max(1, int(GRID_SIZE * 0.2))
            color = PLANT_COLORS["SEED"]
        elif self.current_state == PlantState.SAPLING:
            pixel_size = max(2, int(GRID_SIZE * (0.2 + self.current_size * 2))) # 유묘는 크기에 따라 조금 더 커짐
            color = PLANT_COLORS["SAPLING"]
        elif self.current_state == PlantState.ADULT:
            # 성체 크기를 5단계로 나누어 시각화
            size_ratio = self.current_size / self.adult_max_size_actual
            if size_ratio < 0.2: color = PLANT_COLORS["ADULT_STAGE_1"]
            elif size_ratio < 0.4: color = PLANT_COLORS["ADULT_STAGE_2"]
            elif size_ratio < 0.6: color = PLANT_COLORS["ADULT_STAGE_3"]
            elif size_ratio < 0.8: color = PLANT_COLORS["ADULT_STAGE_4"]
            else: color = PLANT_COLORS["ADULT_STAGE_5"]
            pixel_size = max(3, int(GRID_SIZE * (0.3 + self.current_size * 0.6))) # 성체는 더 크게
        elif self.current_state == PlantState.DEAD:
            pixel_size = max(1, int(GRID_SIZE * 0.15))
            color = PLANT_COLORS["DEAD"]

        self.image = pygame.Surface([pixel_size, pixel_size], pygame.SRCALPHA) # SRCAHPLA로 투명 배경
        pygame.draw.circle(self.image, color, (pixel_size // 2, pixel_size // 2), pixel_size // 2)
        
        # 중앙 정렬을 위해 rect 업데이트
        center_x = self.grid_x * GRID_SIZE + GRID_SIZE // 2
        center_y = self.grid_y * GRID_SIZE + GRID_SIZE // 2
        self.rect = self.image.get_rect(center=(center_x, center_y))


    def update(self, current_soil_tile, climate_info, time_manager):
        """매 cycle 호출되어 식물의 생명 주기 및 행동 로직을 처리합니다."""
        if self.current_state == PlantState.DEAD:
            self.cycles_since_death += 1
            if self.cycles_since_death > DEAD_PLANT_REMOVAL_CYCLES:
                # 맵 매니저를 통해 타일 점유 해제 요청
                if self.map_manager:
                    self.map_manager.get_tile(self.grid_x, self.grid_y).set_occupancy(False)
                self.kill() # Pygame 그룹에서 제거
            return

        self.age += 1
        if self.age > self.species_data["max_lifespan_cycles"]:
            self._die("Old age")
            return

        self._absorb_water(current_soil_tile)
        self._photosynthesize(climate_info, time_manager.current_season)
        self._consume_resources_for_life()
        self._check_environmental_stress(current_soil_tile, climate_info)

        if self.health <= MIN_HEALTH_FOR_SURVIVAL:
            self._die("Low health")
            return
        
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -=1

        # 상태별 로직 처리
        if self.current_state == PlantState.SEED:
            self._handle_seed_state(current_soil_tile)
        elif self.current_state == PlantState.SAPLING:
            self._handle_sapling_state()
        elif self.current_state == PlantState.ADULT:
            self._handle_adult_state(current_soil_tile, climate_info) # 성체는 번식 시도
        
        self._update_capacities() # 크기 변경에 따른 용량 업데이트
        self._update_visuals() # 매 업데이트마다 시각적 요소 갱신

    def _update_capacities(self):
        """크기 변경에 따라 최대 수분/에너지 저장량을 업데이트합니다."""
        self.max_water_capacity = self.current_size * self.species_data["max_water_capacity_factor_size"]
        self.max_energy_capacity = self.current_size * self.species_data["max_energy_capacity_factor_size"]
        # 현재량이 최대량을 넘지 않도록 조정
        self.current_water = min(self.current_water, self.max_water_capacity)
        self.current_energy = min(self.current_energy, self.max_energy_capacity)


    def _handle_seed_state(self, current_soil_tile):
        """씨앗 상태의 로직을 처리합니다. (발아 시도)"""
        # 발아 조건 확인
        can_germinate = (current_soil_tile.water_level >= self.species_data["min_water_for_germination_soil"] and
                         current_soil_tile.temperature >= self.species_data["min_temperature_for_germination"] and
                         self.age <= self.species_data["seed_viability_duration_cycles"])

        if can_germinate:
            self.current_state = PlantState.SAPLING
            self.current_size = 0.05 # 유묘 초기 크기
            self.health = 100.0 # 발아 시 건강 회복
            if DEBUG_MODE: print(f"Seed at ({self.grid_x},{self.grid_y}) germinated.")
        elif self.age > self.species_data["seed_viability_duration_cycles"] or \
             random.random() < SEED_DEATH_CHANCE_PER_CYCLE_IF_UNABLE_TO_GERMINATE:
            self._die("Failed to germinate or viability ended")


    def _handle_sapling_state(self):
        """유묘 상태의 로직을 처리합니다. (성장)"""
        self._grow()
        if self.current_size >= self.target_size_for_adult:
            self.current_state = PlantState.ADULT
            if DEBUG_MODE: print(f"Sapling at ({self.grid_x},{self.grid_y}) grew into an ADULT.")

    def _handle_adult_state(self, current_soil_tile, climate_info):
        """성체 상태의 로직을 처리합니다. (성장 및 번식)"""
        self._grow() # 성체도 계속 성장 (최대 크기까지)
        if self.age >= self.species_data["maturity_age_cycles"] and self.reproduction_cooldown == 0:
            self._reproduce(current_soil_tile, climate_info)

    def _grow(self):
        """식물을 성장시킵니다."""
        if self.current_state == PlantState.DEAD: return

        # 성장은 에너지와 물을 소모
        required_energy_for_growth = self.growth_rate_factor * 0.5 * (self.adult_max_size_actual / max(0.1, self.current_size)) # 작을수록 더 많은 자원 필요
        required_water_for_growth = self.growth_rate_factor * 0.3 * (self.adult_max_size_actual / max(0.1, self.current_size))

        max_size_for_state = self.species_data["sapling_max_size"] if self.current_state == PlantState.SAPLING else self.adult_max_size_actual
        
        if self.current_size < max_size_for_state and \
           self.current_energy > required_energy_for_growth and \
           self.current_water > required_water_for_growth:

            growth_amount = self.growth_rate_factor * (1 - (self.current_size / max_size_for_state)) # 최대 크기에 가까울수록 성장률 감소
            growth_amount = max(0, growth_amount) # 음수 성장 방지

            # 실제 성장률은 건강 상태에 영향 받음
            effective_growth = growth_amount * (self.health / 100.0)
            
            self.current_size += effective_growth
            self.current_size = min(self.current_size, max_size_for_state) # 최대 크기 제한

            self.current_energy -= required_energy_for_growth
            self.current_water -= required_water_for_growth
            
            self._update_capacities() # 크기가 변했으므로 용량 업데이트

    def _photosynthesize(self, climate_info, current_season):
        """광합성을 통해 에너지를 생산합니다."""
        if self.current_state == PlantState.SEED or self.current_state == PlantState.DEAD:
            return

        day_length_ratio = climate_info.get_day_length_ratio(current_season)
        # 광합성은 낮 시간에만, 온도와 수분 조건에 영향 받음
        # 단순화: 온도와 내부 수분량이 적절할 때 효율 증가
        temp_efficiency = 0
        optimal_temp_min, optimal_temp_max = self.species_data["optimal_growth_temperature"]
        if optimal_temp_min <= climate_info.current_daily_temperature <= optimal_temp_max:
            temp_efficiency = 1.0
        elif climate_info.current_daily_temperature < optimal_temp_min:
            # 추울수록 효율 감소 (최저 생존 온도까지)
            diff = optimal_temp_min - climate_info.current_daily_temperature
            range_ = optimal_temp_min - self.species_data["min_survival_temperature"]
            if range_ > 0: temp_efficiency = max(0, 1 - (diff / range_))
        else: # 더울수록 효율 감소 (최대 생존 온도까지)
            diff = climate_info.current_daily_temperature - optimal_temp_max
            range_ = self.species_data["max_survival_temperature"] - optimal_temp_max
            if range_ > 0: temp_efficiency = max(0, 1 - (diff / range_))


        water_efficiency = self.current_water / self.max_water_capacity if self.max_water_capacity > 0 else 0
        
        # 크기에 비례한 광합성량, 효율 적용
        produced_energy = (PHOTOSYNTHESIS_BASE_EFFICIENCY * self.current_size *
                           day_length_ratio * temp_efficiency * water_efficiency)
        
        self.current_energy = min(self.current_energy + produced_energy, self.max_energy_capacity)

    def _absorb_water(self, current_soil_tile):
        """토양으로부터 수분을 흡수합니다."""
        if self.current_state == PlantState.SEED or self.current_state == PlantState.DEAD:
            return
        if current_soil_tile.terrain_type != "SOIL": # terrain.TerrainType.SOIL 대신 문자열 사용 (임시)
             # TODO: terrain enum 제대로 참조하도록 수정 필요
             pass


        # 식물의 최대 흡수량은 현재 비어있는 내부 저장 공간과 토양의 가용 수분량에 따라 결정
        potential_absorption = (self.max_water_capacity - self.current_water) * WATER_ABSORPTION_RATE
        available_soil_water = current_soil_tile.water_level
        
        # 토양에서 식물이 가져갈 수 있는 최대량 (토양 수분의 일정 비율)
        max_drawable_from_soil = available_soil_water * 0.1 # 한번에 토양 수분의 10%까지만 가져갈 수 있도록 제한 (과도한 고갈 방지)
        
        actual_absorption = min(potential_absorption, available_soil_water, max_drawable_from_soil)
        
        if actual_absorption > 0:
            absorbed_from_soil = current_soil_tile.consume_water(actual_absorption)
            self.current_water = min(self.current_water + absorbed_from_soil, self.max_water_capacity)


    def _consume_resources_for_life(self):
        """생명 유지를 위해 에너지와 수분을 소모합니다."""
        if self.current_state == PlantState.DEAD: return

        # 소모량은 현재 크기에 비례
        energy_cost = ENERGY_COST_FOR_MAINTENANCE_PER_CYCLE * self.current_size
        water_cost = WATER_COST_FOR_MAINTENANCE_PER_CYCLE * self.current_size

        self.current_energy -= energy_cost
        self.current_water -= water_cost

        if self.current_energy < 0:
            self.health -= abs(self.current_energy) * 0.5 # 에너지 부족 시 건강 감소폭 확대
            self.current_energy = 0
        if self.current_water < 0:
            self.health -= abs(self.current_water) * 0.5 # 수분 부족 시 건강 감소폭 확대
            self.current_water = 0


    def _reproduce(self, current_soil_tile, climate_info):
        """번식을 시도합니다."""
        if not (self.current_state == PlantState.ADULT and
                self.age >= self.species_data["maturity_age_cycles"] and
                self.reproduction_cooldown == 0 and
                self.current_energy >= self.max_energy_capacity * REPRODUCTION_ENERGY_THRESHOLD_FACTOR and
                self.current_water >= self.max_water_capacity * REPRODUCTION_WATER_THRESHOLD_FACTOR and
                self.health > 70): # 건강 상태도 좋아야 번식 가능
            return

        # 번식 조건: 최적 온도 및 수분 조건에 가까울수록 번식 확률 증가 (단순화)
        optimal_temp_min, optimal_temp_max = self.species_data["optimal_growth_temperature"]
        optimal_water_min, optimal_water_max = self.species_data["optimal_soil_water_level"]
        
        temp_ok = optimal_temp_min <= climate_info.current_daily_temperature <= optimal_temp_max
        water_ok = optimal_water_min <= current_soil_tile.water_level <= optimal_water_max

        if not (temp_ok and water_ok and random.random() < 0.3): # 번식 성공 확률 (임의값 30%)
            # 번식 실패해도 쿨다운은 적용 (시도 자체에 대한 쿨다운)
            self.reproduction_cooldown = self.species_data["reproduction_cooldown_cycles_default"] // 2 
            return


        seeds_to_produce = random.randint(1, self.species_data["max_seeds_produced_per_attempt"])
        seeds_produced_count = 0

        for _ in range(seeds_to_produce):
            energy_cost = self.species_data["energy_cost_per_seed_attempt"]
            if self.current_energy >= energy_cost:
                self.current_energy -= energy_cost
                
                # 씨앗 확산 로직 (map_manager를 통해 주변 빈 타일 찾기)
                if self.map_manager:
                    # config에서 SEED_SPREAD_RADIUS_MIN, SEED_SPREAD_RADIUS_MAX 가져오기
                    from config import SEED_SPREAD_RADIUS_MIN, SEED_SPREAD_RADIUS_MAX
                    
                    # 확산 반경 내에서 무작위 위치 선정
                    # (더 정교하게는 거리에 따른 확률 분포 사용 가능)
                    for _attempt in range(5): # 최대 5번 시도하여 빈 땅 찾기
                        spread_radius = random.randint(SEED_SPREAD_RADIUS_MIN, SEED_SPREAD_RADIUS_MAX)
                        angle = random.uniform(0, 2 * 3.14159)
                        dx = int(round(spread_radius * (random.random() * 2 - 1))) # 원형보다는 사각형 범위로 단순화
                        dy = int(round(spread_radius * (random.random() * 2 - 1)))
                        
                        new_x, new_y = self.grid_x + dx, self.grid_y + dy

                        if self.map_manager.is_valid_tile(new_x, new_y):
                            target_tile = self.map_manager.get_tile(new_x, new_y)
                            if target_tile and target_tile.can_plant_grow_here():
                                # map_manager를 통해 새로운 식물(씨앗) 생성 요청
                                self.map_manager.add_new_plant(new_x, new_y, PlantState.SEED, self.species_data)
                                seeds_produced_count += 1
                                break # 씨앗 하나 성공하면 다음 씨앗으로
                if seeds_produced_count > 0 and DEBUG_MODE:
                    print(f"Plant at ({self.grid_x},{self.grid_y}) reproduced {seeds_produced_count} seeds.")
            else:
                break # 에너지 부족하면 더 이상 씨앗 생산 불가
        
        self.reproduction_cooldown = self.species_data["reproduction_cooldown_cycles_default"]


    def _check_environmental_stress(self, current_soil_tile, climate_info):
        """환경 스트레스를 확인하고 건강에 영향을 줍니다."""
        stress_factor = 0

        # 온도 스트레스
        temp = climate_info.current_daily_temperature
        min_survival_temp = self.species_data["min_survival_temperature"]
        max_survival_temp = self.species_data["max_survival_temperature"]
        optimal_temp_min, optimal_temp_max = self.species_data["optimal_growth_temperature"]

        if temp < min_survival_temp or temp > max_survival_temp:
            self._die(f"Extreme temperature: {temp:.1f}C") # 생존 범위를 벗어나면 즉시 죽음
            return
        elif temp < optimal_temp_min:
            stress_factor += (optimal_temp_min - temp) / (optimal_temp_min - min_survival_temp + 1e-6) # 분모 0 방지
        elif temp > optimal_temp_max:
            stress_factor += (temp - optimal_temp_max) / (max_survival_temp - optimal_temp_max + 1e-6)

        # 수분 스트레스 (토양)
        soil_water = current_soil_tile.water_level
        min_survival_water = self.species_data["min_survival_soil_water_level"]
        optimal_water_min, optimal_water_max = self.species_data["optimal_soil_water_level"]
        
        if soil_water < min_survival_water and self.current_state != PlantState.SEED: # 씨앗은 토양 수분 부족으로 바로 죽지 않음
             stress_factor += 1.5 # 건조 스트레스 가중치 크게

        elif soil_water < optimal_water_min:
            stress_factor += (optimal_water_min - soil_water) / (optimal_water_min - min_survival_water + 1e-6)
        # 과습 스트레스는 MVP에서 제외하거나 단순화 (예: 최대치를 넘어서면 약간의 스트레스)
        elif soil_water > optimal_water_max * 1.5: # 최적 수분량의 150%를 초과하면 약간의 과습 스트레스
            stress_factor += (soil_water - (optimal_water_max * 1.5)) / (optimal_water_max * 0.5 + 1e-6) * 0.3 # 과습 스트레스는 조금 약하게


        # 내부 수분 부족 스트레스
        if self.max_water_capacity > 0 and (self.current_water / self.max_water_capacity) < 0.1:
             stress_factor += 1.0


        if stress_factor > 0:
            damage = STRESS_DAMAGE_RATE * stress_factor * (1.0 - self.health / 200.0) # 건강이 낮을수록 더 큰 피해
            self.health -= damage
            self.health = max(MIN_HEALTH_FOR_SURVIVAL -1 , self.health) # 최소 생존 건강 아래로 바로 떨어지진 않게
        else: # 스트레스가 없으면 건강 회복 시도
            # 최적 환경 (온도, 토양 수분 모두 최적 범위 내) 일 때만 회복
            temp_optimal = optimal_temp_min <= temp <= optimal_temp_max
            soil_water_optimal = optimal_water_min <= soil_water <= optimal_water_max
            if temp_optimal and soil_water_optimal and self.current_energy > self.max_energy_capacity * 0.3: # 회복에도 에너지 필요
                recovery_amount = HEALING_RATE_UNDER_OPTIMAL_CONDITIONS * (self.current_energy / self.max_energy_capacity)
                self.health += recovery_amount
                self.health = min(100.0, self.health)
                self.current_energy -= recovery_amount * 0.1 # 회복에 드는 에너지 소모


    def _die(self, reason="Unknown"):
        """식물이 죽습니다."""
        if self.current_state == PlantState.DEAD: return # 이미 죽었으면 아무것도 안함

        if DEBUG_MODE: print(f"Plant at ({self.grid_x},{self.grid_y}) died. Reason: {reason}. Age: {self.age} cycles. Size: {self.current_size:.2f}")
        self.current_state = PlantState.DEAD
        self.health = 0
        self.current_energy = 0
        self.current_water = 0
        self.cycles_since_death = 0 # 죽은 시간 카운트 시작
        # SoilTile의 is_occupied_by_plant는 DEAD 상태가 일정 시간 지난 후 해제 (update 메서드에서 처리)
        self._update_visuals() # 죽은 모습으로 업데이트

    def draw(self, surface):
        """Pygame Surface에 식물을 그립니다. (Sprite Group 사용 시 자동 호출)"""
        if self.image and self.rect: # 이미지가 준비되었을 때만 그림
             surface.blit(self.image, self.rect)