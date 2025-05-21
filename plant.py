# plant.py
import pygame
import enum
import random
# DEBUG_MODE 및 필요한 설정값 가져오기
from config import (PLANT_COLORS, GRID_SIZE, MIN_HEALTH_FOR_SURVIVAL,
                    ENERGY_COST_FOR_MAINTENANCE_PER_CYCLE, WATER_COST_FOR_MAINTENANCE_PER_CYCLE,
                    PHOTOSYNTHESIS_BASE_EFFICIENCY, WATER_ABSORPTION_RATE,
                    STRESS_DAMAGE_RATE, HEALING_RATE_UNDER_OPTIMAL_CONDITIONS,
                    SAPLING_TO_ADULT_GROWTH_PER_CYCLE, REPRODUCTION_ENERGY_THRESHOLD_FACTOR,
                    REPRODUCTION_WATER_THRESHOLD_FACTOR, SEED_DEATH_CHANCE_PER_CYCLE_IF_UNABLE_TO_GERMINATE,
                    DEAD_PLANT_REMOVAL_CYCLES, DEBUG_MODE) # DEBUG_MODE 임포트
from plant_species import STRONG_PLANT_SPECIES
from terrain import TerrainType # TerrainType Enum 임포트 (지형 비교용)

class PlantState(enum.Enum):
    SEED = "SEED"
    SAPLING = "SAPLING"
    ADULT = "ADULT"
    DEAD = "DEAD"

class Plant(pygame.sprite.Sprite):
    def __init__(self, grid_x, grid_y, species_data=None, initial_state=PlantState.SEED, map_manager_ref=None):
        super().__init__()
        self.species_data = species_data if species_data else STRONG_PLANT_SPECIES
        self.map_manager = map_manager_ref
        self.plant_id = id(self) # 디버깅을 위한 고유 ID

        self.grid_x = grid_x
        self.grid_y = grid_y
        self.age = 0
        self.health = 100.0
        self.current_state = initial_state
        self.current_size = 0.01 if initial_state == PlantState.SEED else 0.05
        
        self.target_size_for_adult = self.species_data["default_target_size_for_adult"]
        adult_max_size_base = self.species_data["adult_max_size"]
        self.adult_max_size_actual = random.uniform(
            adult_max_size_base * (1 - 0.1),
            adult_max_size_base * (1 + 0.1)
        )

        self.max_water_capacity = self.current_size * self.species_data["max_water_capacity_factor_size"]
        self.current_water = self.max_water_capacity * 0.5
        self.max_energy_capacity = self.current_size * self.species_data["max_energy_capacity_factor_size"]
        self.current_energy = self.max_energy_capacity * 0.5

        self.growth_rate_factor = self.species_data["base_growth_rate_factor"]
        self.reproduction_cooldown = 0
        self.cycles_since_death = 0

        self.image = None
        self.rect = None
        self._update_visuals()

        if DEBUG_MODE: print(f"Plant {self.plant_id} created at ({grid_x},{grid_y}), State: {initial_state}")

    def _update_visuals(self):
        # ... (기존 _update_visuals 내용 동일)
        pixel_size = 0
        color = PLANT_COLORS["DEAD"]

        if self.current_state == PlantState.SEED:
            pixel_size = max(1, int(GRID_SIZE * 0.2))
            color = PLANT_COLORS["SEED"]
        elif self.current_state == PlantState.SAPLING:
            pixel_size = max(2, int(GRID_SIZE * (0.2 + self.current_size * 2))) 
            color = PLANT_COLORS["SAPLING"]
        elif self.current_state == PlantState.ADULT:
            size_ratio = self.current_size / self.adult_max_size_actual if self.adult_max_size_actual > 0 else 0
            if size_ratio < 0.2: color = PLANT_COLORS["ADULT_STAGE_1"]
            elif size_ratio < 0.4: color = PLANT_COLORS["ADULT_STAGE_2"]
            elif size_ratio < 0.6: color = PLANT_COLORS["ADULT_STAGE_3"]
            elif size_ratio < 0.8: color = PLANT_COLORS["ADULT_STAGE_4"]
            else: color = PLANT_COLORS["ADULT_STAGE_5"]
            pixel_size = max(3, int(GRID_SIZE * (0.3 + self.current_size * 0.6)))
        elif self.current_state == PlantState.DEAD:
            pixel_size = max(1, int(GRID_SIZE * 0.15))
            color = PLANT_COLORS["DEAD"]

        self.image = pygame.Surface([pixel_size, pixel_size], pygame.SRCALPHA) 
        pygame.draw.circle(self.image, color, (pixel_size // 2, pixel_size // 2), pixel_size // 2)
        
        center_x = self.grid_x * GRID_SIZE + GRID_SIZE // 2
        center_y = self.grid_y * GRID_SIZE + GRID_SIZE // 2
        self.rect = self.image.get_rect(center=(center_x, center_y))


    def update(self, current_soil_tile, climate_info, time_manager):
        if self.current_state == PlantState.DEAD:
            self.cycles_since_death += 1
            if self.cycles_since_death > DEAD_PLANT_REMOVAL_CYCLES:
                if self.map_manager:
                    tile = self.map_manager.get_tile(self.grid_x, self.grid_y)
                    if tile: tile.set_occupancy(False)
                if DEBUG_MODE: print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) DEAD, removing from group.")
                self.kill()
            return

        if DEBUG_MODE:
            print(f"--- Plant {self.plant_id} ({self.grid_x},{self.grid_y}) Update START --- Age: {self.age}, State: {self.current_state.value}, Size: {self.current_size:.3f}, Health: {self.health:.2f}, Energy: {self.current_energy:.3f}/{self.max_energy_capacity:.3f}, Water: {self.current_water:.3f}/{self.max_water_capacity:.3f}")

        self.age += 1
        if self.age > self.species_data["max_lifespan_cycles"]:
            self._die("Old age")
            return

        self._absorb_water(current_soil_tile)
        self._photosynthesize(climate_info, time_manager.current_season)
        self._consume_resources_for_life() # 생명 유지 자원 소모는 스트레스 체크 전에 수행
        self._check_environmental_stress(current_soil_tile, climate_info) # 스트레스가 건강에 영향

        if self.health <= MIN_HEALTH_FOR_SURVIVAL and self.current_state != PlantState.DEAD : # 이미 죽은 상태가 아니면
            self._die("Low health")
            return
        
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -=1

        if self.current_state == PlantState.SEED:
            self._handle_seed_state(current_soil_tile)
        elif self.current_state == PlantState.SAPLING:
            self._handle_sapling_state()
        elif self.current_state == PlantState.ADULT:
            self._handle_adult_state(current_soil_tile, climate_info)
        
        self._update_capacities()
        self._update_visuals()
        if DEBUG_MODE:
            print(f"--- Plant {self.plant_id} ({self.grid_x},{self.grid_y}) Update END --- Health: {self.health:.2f}, Energy: {self.current_energy:.3f}, Water: {self.current_water:.3f}, Size: {self.current_size:.3f}\n")


    def _update_capacities(self):
        new_max_water = self.current_size * self.species_data["max_water_capacity_factor_size"]
        new_max_energy = self.current_size * self.species_data["max_energy_capacity_factor_size"]
        
        # 최대 용량이 줄어들 경우, 현재 보유량이 새 최대 용량을 초과하지 않도록 조정
        if new_max_water < self.max_water_capacity and self.current_water > new_max_water:
            self.current_water = new_max_water
        if new_max_energy < self.max_energy_capacity and self.current_energy > new_max_energy:
            self.current_energy = new_max_energy
            
        self.max_water_capacity = new_max_water
        self.max_energy_capacity = new_max_energy
        
        # 현재량이 최대량을 넘지 않도록 다시 한번 확인 (용량 증가 시에도 필요)
        self.current_water = min(self.current_water, self.max_water_capacity)
        self.current_energy = min(self.current_energy, self.max_energy_capacity)


    def _handle_seed_state(self, current_soil_tile):
        can_germinate = (current_soil_tile.water_level >= self.species_data["min_water_for_germination_soil"] and
                         current_soil_tile.temperature >= self.species_data["min_temperature_for_germination"] and
                         self.age <= self.species_data["seed_viability_duration_cycles"])

        if can_germinate:
            self.current_state = PlantState.SAPLING
            self.current_size = 0.05 
            self.health = 100.0 
            self._update_capacities() # 중요: 상태 변경 후 즉시 용량 업데이트
            if DEBUG_MODE: print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _handle_seed_state: Germinated! New state: SAPLING, Size: {self.current_size:.3f}")
        elif self.age > self.species_data["seed_viability_duration_cycles"] or \
             random.random() < SEED_DEATH_CHANCE_PER_CYCLE_IF_UNABLE_TO_GERMINATE:
            if DEBUG_MODE: print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _handle_seed_state: Seed failed to germinate or viability ended. Age: {self.age}")
            self._die("Failed to germinate or viability ended")


    def _handle_sapling_state(self):
        grown_this_cycle = self._grow() # _grow가 실제 성장했는지 여부 반환하도록 수정 고려
        if self.current_size >= self.target_size_for_adult:
            self.current_state = PlantState.ADULT
            if DEBUG_MODE: print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _handle_sapling_state: Grew into ADULT. Size: {self.current_size:.3f}")

    def _handle_adult_state(self, current_soil_tile, climate_info):
        grown_this_cycle = self._grow()
        if self.age >= self.species_data["maturity_age_cycles"] and self.reproduction_cooldown == 0:
            self._reproduce(current_soil_tile, climate_info)

    def _grow(self):
        if self.current_state == PlantState.DEAD or self.health <= MIN_HEALTH_FOR_SURVIVAL:
            if DEBUG_MODE: print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _grow: Skipping growth (DEAD or Low Health: {self.health:.2f})")
            return False

        max_size_for_state = self.species_data["sapling_max_size"] if self.current_state == PlantState.SAPLING else self.adult_max_size_actual
        
        if self.current_size >= max_size_for_state:
            if DEBUG_MODE: print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _grow: Already at max size for state ({max_size_for_state:.3f}). Current size: {self.current_size:.3f}")
            return False

        # 성장은 에너지와 물을 소모, 크기가 작을수록 상대적으로 더 많은 기본 자원 필요, 건강도 영향
        # 기본 요구량은 크기에 비례, 성장률은 (1 - 현재크기/최대크기)에 비례
        base_required_energy_for_growth = SAPLING_TO_ADULT_GROWTH_PER_CYCLE * 0.8 * self.current_size 
        base_required_water_for_growth = SAPLING_TO_ADULT_GROWTH_PER_CYCLE * 0.5 * self.current_size
        
        # 건강 상태에 따른 요구량 증가 (건강 안 좋으면 더 많은 자원 필요)
        health_factor = max(0.1, self.health / 100.0) # 최소 0.1
        required_energy_for_growth = base_required_energy_for_growth / health_factor
        required_water_for_growth = base_required_water_for_growth / health_factor


        if DEBUG_MODE:
            print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _grow Attempt: size={self.current_size:.3f}, energy={self.current_energy:.3f}, water={self.current_water:.3f}, health={self.health:.2f}, max_size_state={max_size_for_state:.3f}")
            print(f"Plant {self.plant_id} _grow Req: E={required_energy_for_growth:.4f}, W={required_water_for_growth:.4f}")

        can_grow_this_cycle = (self.current_energy > required_energy_for_growth and
                               self.current_water > required_water_for_growth)

        if DEBUG_MODE: print(f"Plant {self.plant_id} _grow: Growth condition met: {can_grow_this_cycle}")

        if can_grow_this_cycle:
            # 실제 성장량은 기본 성장률 * (최대크기까지 남은 비율) * 건강상태 * (자원충분도 - 단순화하여 일단 제외)
            growth_potential_ratio = (1 - (self.current_size / max_size_for_state))
            growth_amount = self.species_data["base_growth_rate_factor"] * growth_potential_ratio
            
            effective_growth = growth_amount * health_factor # 건강 상태가 좋을수록 잘 자람
            effective_growth = max(0, effective_growth) # 음수 성장 방지
            
            # 너무 작은 성장은 무시 (성장 임계값)
            if effective_growth < 0.0001:
                 if DEBUG_MODE: print(f"Plant {self.plant_id} _grow: Effective growth ({effective_growth:.5f}) too small, skipping actual growth.")
                 return False

            prev_size = self.current_size
            self.current_size += effective_growth
            self.current_size = min(self.current_size, max_size_for_state)

            self.current_energy -= required_energy_for_growth
            self.current_water -= required_water_for_growth
            
            self._update_capacities()

            if DEBUG_MODE:
                print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _grow SUCCESS: prev_size={prev_size:.4f}, growth_amount={growth_amount:.4f}, effective_growth={effective_growth:.4f}, new_size={self.current_size:.4f}")
                print(f"Plant {self.plant_id} _grow Resources After: E={self.current_energy:.3f}, W={self.current_water:.3f}")
            return True
        else:
            if DEBUG_MODE: print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _grow FAILED: Not enough resources or already max size.")
            return False


    def _photosynthesize(self, climate_info, current_season):
        if self.current_state == PlantState.SEED or self.current_state == PlantState.DEAD:
            return

        day_length_ratio = climate_info.get_day_length_ratio(current_season)
        optimal_temp_min, optimal_temp_max = self.species_data["optimal_growth_temperature"]
        
        temp_efficiency = 0
        current_temp = climate_info.current_daily_temperature
        if optimal_temp_min <= current_temp <= optimal_temp_max:
            temp_efficiency = 1.0
        elif current_temp < optimal_temp_min:
            diff = optimal_temp_min - current_temp
            range_ = optimal_temp_min - self.species_data["min_survival_temperature"]
            if range_ > 0: temp_efficiency = max(0, 1 - (diff / range_))
        else: 
            diff = current_temp - optimal_temp_max
            range_ = self.species_data["max_survival_temperature"] - optimal_temp_max
            if range_ > 0: temp_efficiency = max(0, 1 - (diff / range_))

        water_efficiency = self.current_water / self.max_water_capacity if self.max_water_capacity > 0 else 0
        size_factor = max(0.01, self.current_size) # 최소 크기 0.01로 계산 (씨앗 등 매우 작을 때 대비)

        produced_energy = (PHOTOSYNTHESIS_BASE_EFFICIENCY * size_factor *
                           day_length_ratio * temp_efficiency * water_efficiency)
        
        prev_energy = self.current_energy
        self.current_energy = min(self.current_energy + produced_energy, self.max_energy_capacity)

        if DEBUG_MODE:
            print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _photosynthesize: DayRatio={day_length_ratio:.2f}, TempEff={temp_efficiency:.2f} (T={current_temp:.1f}), WaterEff={water_efficiency:.2f}, SizeFactor={size_factor:.2f}")
            print(f"Plant {self.plant_id} _photosynthesize: Produced E={produced_energy:.4f}. Prev E={prev_energy:.3f}, New E={self.current_energy:.3f}/{self.max_energy_capacity:.3f}")


    def _absorb_water(self, current_soil_tile):
        if self.current_state == PlantState.SEED or self.current_state == PlantState.DEAD:
            return
        
        # TerrainType Enum과 직접 비교하도록 수정
        if current_soil_tile.terrain_type != TerrainType.SOIL:
            if DEBUG_MODE: print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _absorb_water: Cannot absorb, not on SOIL. Tile type: {current_soil_tile.terrain_type}")
            return

        # 식물이 흡수 가능한 최대량 (내부 저장 공간 여유분 * 흡수율)
        potential_absorption_by_plant = (self.max_water_capacity - self.current_water) * WATER_ABSORPTION_RATE
        available_soil_water = current_soil_tile.water_level
        
        # 한번에 토양에서 가져갈 수 있는 양 제한 (토양 수분의 10%)
        max_drawable_from_soil_at_once = available_soil_water * 0.2 # 비율 약간 증가시켜봄
        
        # 실제 흡수량은 세 값 중 가장 작은 값
        actual_absorption = min(potential_absorption_by_plant, available_soil_water, max_drawable_from_soil_at_once)
        actual_absorption = max(0, actual_absorption) # 음수 방지
        
        absorbed_from_soil = 0
        if actual_absorption > 0:
            prev_water = self.current_water
            prev_soil_water = current_soil_tile.water_level
            absorbed_from_soil = current_soil_tile.consume_water(actual_absorption)
            self.current_water = min(self.current_water + absorbed_from_soil, self.max_water_capacity)
            if DEBUG_MODE:
                print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _absorb_water: Potential={potential_absorption_by_plant:.3f}, SoilHas={available_soil_water:.2f}, MaxDrawable={max_drawable_from_soil_at_once:.3f}")
                print(f"Plant {self.plant_id} _absorb_water: Absorbed={absorbed_from_soil:.3f}. Prev W={prev_water:.3f}, New W={self.current_water:.3f}. Soil W before={prev_soil_water:.2f}, after={current_soil_tile.water_level:.2f}")
        elif DEBUG_MODE:
             print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _absorb_water: No water absorbed. PotentialByPlant={potential_absorption_by_plant:.3f}, SoilHas={available_soil_water:.2f}, MaxDrawable={max_drawable_from_soil_at_once:.3f}")


    def _consume_resources_for_life(self):
        if self.current_state == PlantState.DEAD: return

        energy_cost = ENERGY_COST_FOR_MAINTENANCE_PER_CYCLE * self.current_size
        water_cost = WATER_COST_FOR_MAINTENANCE_PER_CYCLE * self.current_size

        prev_energy = self.current_energy
        prev_water = self.current_water
        prev_health = self.health

        self.current_energy -= energy_cost
        self.current_water -= water_cost

        health_damage_from_lack = 0
        if self.current_energy < 0:
            health_damage_from_lack += abs(self.current_energy) * 1.0 # 에너지 부족 시 건강 감소폭 증가 (계수 0.5 -> 1.0)
            self.current_energy = 0
        if self.current_water < 0:
            health_damage_from_lack += abs(self.current_water) * 1.0 # 수분 부족 시 건강 감소폭 증가
            self.current_water = 0
        
        if health_damage_from_lack > 0:
            self.health -= health_damage_from_lack
            # self.health = max(0, self.health) # MIN_HEALTH_FOR_SURVIVAL 보다 아래로 내려갈 수 있도록 수정

        if DEBUG_MODE:
            print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _consume_resources: E_cost={energy_cost:.4f}, W_cost={water_cost:.4f}. Prev E={prev_energy:.3f}, W={prev_water:.3f}, H={prev_health:.2f}")
            print(f"Plant {self.plant_id} _consume_resources: New E={self.current_energy:.3f}, W={self.current_water:.3f}, H={self.health:.2f}. LackDamage={health_damage_from_lack:.2f}")


    def _reproduce(self, current_soil_tile, climate_info):
        can_reproduce_base = (self.current_state == PlantState.ADULT and
                              self.age >= self.species_data["maturity_age_cycles"] and
                              self.reproduction_cooldown == 0 and
                              self.current_energy >= self.max_energy_capacity * REPRODUCTION_ENERGY_THRESHOLD_FACTOR and
                              self.current_water >= self.max_water_capacity * REPRODUCTION_WATER_THRESHOLD_FACTOR and
                              self.health > 70)
        
        if not can_reproduce_base:
            if DEBUG_MODE:
                if self.current_state == PlantState.ADULT and self.age >= self.species_data["maturity_age_cycles"] and self.reproduction_cooldown == 0: # 기본적인 번식 시도 가능 조건은 되었을 때만 상세 로그
                    print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _reproduce: Base condition NOT MET. E:{self.current_energy:.2f}(Need>={self.max_energy_capacity * REPRODUCTION_ENERGY_THRESHOLD_FACTOR:.2f}), W:{self.current_water:.2f}(Need>={self.max_water_capacity * REPRODUCTION_WATER_THRESHOLD_FACTOR:.2f}), H:{self.health:.1f}(Need>70)")
            return

        optimal_temp_min, optimal_temp_max = self.species_data["optimal_growth_temperature"]
        optimal_water_min, optimal_water_max = self.species_data["optimal_soil_water_level"]
        temp_ok = optimal_temp_min <= climate_info.current_daily_temperature <= optimal_temp_max
        water_ok = optimal_water_min <= current_soil_tile.water_level <= optimal_water_max
        
        reproduction_chance = 0.1 # 기본 번식 확률 낮춤 (너무 빠르게 퍼지는 것 방지)
        if temp_ok and water_ok:
            reproduction_chance = 0.3 # 최적 환경에서 확률 증가

        if DEBUG_MODE: print(f"Plant {self.plant_id} _reproduce: Attempting. TempOK={temp_ok}, WaterOK={water_ok}, Chance={reproduction_chance:.2f}")

        if not (random.random() < reproduction_chance):
            self.reproduction_cooldown = self.species_data["reproduction_cooldown_cycles_default"] // 3 # 실패 시 쿨다운 짧게
            if DEBUG_MODE: print(f"Plant {self.plant_id} _reproduce: Failed by chance. Cooldown set to {self.reproduction_cooldown}")
            return

        seeds_to_produce = random.randint(1, self.species_data["max_seeds_produced_per_attempt"])
        seeds_produced_count = 0
        initial_energy_before_reproduction = self.current_energy

        for i in range(seeds_to_produce):
            energy_cost = self.species_data["energy_cost_per_seed_attempt"]
            if self.current_energy >= energy_cost:
                self.current_energy -= energy_cost
                
                if self.map_manager:
                    from config import SEED_SPREAD_RADIUS_MIN, SEED_SPREAD_RADIUS_MAX
                    for _attempt in range(10): # 빈 땅 찾기 시도 횟수 증가
                        # 원형으로 좀 더 자연스럽게 확산되도록 수정
                        angle = random.uniform(0, 2 * 3.1415926535)
                        radius = random.uniform(SEED_SPREAD_RADIUS_MIN, SEED_SPREAD_RADIUS_MAX)
                        dx = int(round(radius * pygame.math.Vector2(1, 0).rotate(angle * 180 / 3.1415926535).x)) # Pygame Vector2 사용
                        dy = int(round(radius * pygame.math.Vector2(1, 0).rotate(angle * 180 / 3.1415926535).y))
                        
                        new_x, new_y = self.grid_x + dx, self.grid_y + dy

                        if self.map_manager.is_valid_tile(new_x, new_y):
                            target_tile = self.map_manager.get_tile(new_x, new_y)
                            if target_tile and target_tile.can_plant_grow_here():
                                self.map_manager.add_new_plant(new_x, new_y, PlantState.SEED, self.species_data)
                                seeds_produced_count += 1
                                if DEBUG_MODE: print(f"Plant {self.plant_id} _reproduce: Seed {i+1} success at ({new_x},{new_y}).")
                                break 
                    else: # for-else: break 안걸리면 실행 (빈 땅 못찾음)
                        if DEBUG_MODE: print(f"Plant {self.plant_id} _reproduce: Seed {i+1} failed to find empty spot.")
            else:
                if DEBUG_MODE: print(f"Plant {self.plant_id} _reproduce: Not enough energy for seed {i+1}. Cost={energy_cost:.2f}, Has={self.current_energy:.2f}")
                break 
        
        if seeds_produced_count > 0 and DEBUG_MODE:
            print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _reproduce SUCCESS: Produced {seeds_produced_count} seeds. Energy spent: {initial_energy_before_reproduction - self.current_energy:.2f}")
        
        self.reproduction_cooldown = self.species_data["reproduction_cooldown_cycles_default"]


    def _check_environmental_stress(self, current_soil_tile, climate_info):
        stress_factor = 0
        temp = climate_info.current_daily_temperature
        min_survival_temp = self.species_data["min_survival_temperature"]
        max_survival_temp = self.species_data["max_survival_temperature"]
        optimal_temp_min, optimal_temp_max = self.species_data["optimal_growth_temperature"]

        if temp < min_survival_temp or temp > max_survival_temp:
            if DEBUG_MODE: print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _check_environmental_stress: Dies from EXTREME temperature: {temp:.1f}C")
            self._die(f"Extreme temperature: {temp:.1f}C")
            return # 이미 죽었으므로 추가 스트레스 계산 불필요
            
        if temp < optimal_temp_min:
            stress_factor += ((optimal_temp_min - temp) / (optimal_temp_min - min_survival_temp + 1e-6)) * 1.0 # 가중치 1.0
        elif temp > optimal_temp_max:
            stress_factor += ((temp - optimal_temp_max) / (max_survival_temp - optimal_temp_max + 1e-6)) * 1.0 # 가중치 1.0

        soil_water = current_soil_tile.water_level
        min_survival_water = self.species_data["min_survival_soil_water_level"]
        optimal_water_min, optimal_water_max = self.species_data["optimal_soil_water_level"]
        
        if self.current_state != PlantState.SEED: # 씨앗은 토양 수분 직접 스트레스 덜 받음
            if soil_water < min_survival_water :
                 stress_factor += 1.5 # 건조 스트레스 가중치 크게
            elif soil_water < optimal_water_min:
                stress_factor += ((optimal_water_min - soil_water) / (optimal_water_min - min_survival_water + 1e-6)) * 0.7 # 가중치 0.7
            elif soil_water > optimal_water_max * 1.8: # 과습 기준 강화 (최적의 180%)
                stress_factor += ((soil_water - (optimal_water_max * 1.8)) / (optimal_water_max * 0.8 + 1e-6)) * 0.5 # 과습 스트레스는 조금 약하게


        if self.max_water_capacity > 0 and (self.current_water / self.max_water_capacity) < 0.05: # 내부 수분 5% 미만
             stress_factor += 1.2 # 내부 수분 부족 스트레스 가중치 증가

        prev_health = self.health
        if stress_factor > 0:
            # 건강이 낮을수록 스트레스에 더 취약하게, 최대 피해량 제한
            vulnerability = 1.0 + (1.0 - (self.health / 100.0)) * 0.5 # 건강 0일때 1.5배, 건강 100일때 1배
            damage = min(STRESS_DAMAGE_RATE * stress_factor * vulnerability, 25.0) # 한번에 최대 25 데미지
            self.health -= damage
            # self.health = max(0, self.health) # MIN_HEALTH_FOR_SURVIVAL 보다 아래로 갈 수 있음
            if DEBUG_MODE:
                print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _check_environmental_stress: StressFactor={stress_factor:.2f}, Temp={temp:.1f}, SoilW={soil_water:.1f}, InternalW={self.current_water/self.max_water_capacity if self.max_water_capacity>0 else 0:.2f}")
                print(f"Plant {self.plant_id} _check_environmental_stress: Damage={damage:.2f}. Prev H={prev_health:.2f}, New H={self.health:.2f}")
        else: # 스트레스가 없거나 매우 낮으면 건강 회복 시도
            temp_optimal = optimal_temp_min <= temp <= optimal_temp_max
            soil_water_optimal = optimal_water_min <= soil_water <= optimal_water_max
            if temp_optimal and soil_water_optimal and self.current_energy > self.max_energy_capacity * 0.2 and self.current_water > self.max_water_capacity * 0.2:
                recovery_amount = HEALING_RATE_UNDER_OPTIMAL_CONDITIONS * (self.health / 150.0 + 0.3) # 건강 낮을수록 회복량 조금 줄고, 최소 회복량 보장
                energy_cost_for_healing = recovery_amount * 0.15
                water_cost_for_healing = recovery_amount * 0.1

                if self.current_energy > energy_cost_for_healing and self.current_water > water_cost_for_healing:
                    self.health += recovery_amount
                    self.health = min(100.0, self.health)
                    self.current_energy -= energy_cost_for_healing
                    self.current_water -= water_cost_for_healing
                    if DEBUG_MODE:
                        print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _check_environmental_stress: Optimal conditions. Healing by {recovery_amount:.2f}. Prev H={prev_health:.2f}, New H={self.health:.2f}")


    def _die(self, reason="Unknown"):
        if self.current_state == PlantState.DEAD: return

        if DEBUG_MODE: print(f"Plant {self.plant_id} ({self.grid_x},{self.grid_y}) _die: Reason: {reason}. Age: {self.age} cycles. Size: {self.current_size:.3f}, Health: {self.health:.2f}")
        self.current_state = PlantState.DEAD
        self.health = 0
        self.current_energy = 0
        self.current_water = 0
        self.cycles_since_death = 0
        self._update_visuals()

    def draw(self, surface):
        if self.image and self.rect:
             surface.blit(self.image, self.rect)