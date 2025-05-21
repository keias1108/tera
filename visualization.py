# visualization.py
import pygame
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, INFO_PANEL_HEIGHT, GAME_AREA_HEIGHT,
                    TERRAIN_COLORS, SOIL_COLOR_STEPS, MAX_SOIL_WATER_LEVEL, MAP_HEIGHT, MAP_WIDTH,
                    INFO_FONT_SIZE, INFO_FONT_COLOR, INFO_LINE_SPACING,
                    GAUGE_BAR_WIDTH, GAUGE_BAR_HEIGHT, GAUGE_TEXT_OFFSET, # 게이지바 설정 임포트
                    DEBUG_INFO_START_X, DEBUG_INFO_START_Y, DEBUG_INFO_LINE_SPACING, # 디버그 정보 위치
                    DEBUG_INFO_CATEGORY_SPACING, GAUGE_BAR_COLORS, DEBUG_MODE) # DEBUG_MODE 임포트
from terrain import TerrainType
from plant import PlantState

pygame.font.init()
INFO_FONT = pygame.font.SysFont("arial", INFO_FONT_SIZE)
DEBUG_FONT = pygame.font.SysFont("arial", INFO_FONT_SIZE - 2) # 디버그용 약간 작은 폰트

def draw_grid(surface, map_manager):
    # ... (기존 draw_grid 내용 동일) ...
    for r in range(map_manager.height):
        for c in range(map_manager.width):
            tile = map_manager.get_tile(c, r)
            rect = pygame.Rect(c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            
            color = (0,0,0) 
            if tile.terrain_type == TerrainType.WATER:
                color = TERRAIN_COLORS["WATER"]
            elif tile.terrain_type == TerrainType.ROCK:
                color = TERRAIN_COLORS["ROCK"]
            elif tile.terrain_type == TerrainType.SOIL:
                water_ratio = tile.water_level / MAX_SOIL_WATER_LEVEL if MAX_SOIL_WATER_LEVEL > 0 else 0
                if water_ratio < 0.1: 
                    color = TERRAIN_COLORS["SOIL_DRY"]
                elif water_ratio < 0.3:
                    color = TERRAIN_COLORS["SOIL_MOIST_1"]
                elif water_ratio < 0.6:
                    color = TERRAIN_COLORS["SOIL_MOIST_2"]
                elif water_ratio < 0.85:
                    color = TERRAIN_COLORS["SOIL_MOIST_3"]
                else: 
                    color = TERRAIN_COLORS["SOIL_WET"]
            
            pygame.draw.rect(surface, color, rect)


def draw_plants(surface, plant_group):
    # ... (기존 draw_plants 내용 동일) ...
    for plant in plant_group:
        plant.draw(surface)


def draw_info_panel(surface, time_manager, climate_manager, plant_group, map_manager):
    # ... (기존 draw_info_panel 내용 동일) ...
    panel_rect = pygame.Rect(0, GAME_AREA_HEIGHT, SCREEN_WIDTH, INFO_PANEL_HEIGHT)
    pygame.draw.rect(surface, (30, 30, 30), panel_rect) 

    y_offset = GAME_AREA_HEIGHT + 10 
    
    time_text = time_manager.get_current_date_str()
    draw_text(surface, time_text, 10, y_offset, font=INFO_FONT, color=INFO_FONT_COLOR)
    y_offset += INFO_LINE_SPACING

    total_plants = len(plant_group)
    plant_counts = {state: 0 for state in PlantState}
    for plant in plant_group:
        plant_counts[plant.current_state] += 1
    
    plant_info_str = f"Total Plants: {total_plants} (Seed: {plant_counts[PlantState.SEED]}, Sapling: {plant_counts[PlantState.SAPLING]}, Adult: {plant_counts[PlantState.ADULT]}, Dead: {plant_counts[PlantState.DEAD]})"
    draw_text(surface, plant_info_str, 10, y_offset, font=INFO_FONT, color=INFO_FONT_COLOR)
    y_offset += INFO_LINE_SPACING * 1.5 

    left_x_offset = 10
    right_x_offset = SCREEN_WIDTH // 2 + 10
    env_y_offset = y_offset 

    avg_soil_water = map_manager.get_average_soil_water_level()
    draw_text(surface, f"Avg Soil Water: {avg_soil_water:.1f}mm", left_x_offset, env_y_offset, font=INFO_FONT, color=INFO_FONT_COLOR)
    
    current_temp = climate_manager.current_daily_temperature
    draw_text(surface, f"Current Avg Temp: {current_temp:.1f}C", right_x_offset, env_y_offset, font=INFO_FONT, color=INFO_FONT_COLOR)
    env_y_offset += INFO_LINE_SPACING

    rain_info = climate_manager.get_last_rainfall_info_str()
    draw_text(surface, rain_info, left_x_offset, env_y_offset, font=INFO_FONT, color=INFO_FONT_COLOR)
    
    day_length = climate_manager.get_day_length_ratio(time_manager.current_season) * 24
    draw_text(surface, f"Day Length: {day_length:.1f} hrs", right_x_offset, env_y_offset, font=INFO_FONT, color=INFO_FONT_COLOR)


def draw_text(surface, text, x, y, font=None, color=None):
    # ... (기존 draw_text 내용 동일, INFO_FONT와 INFO_FONT_COLOR를 기본값으로 사용하도록 수정) ...
    if font is None: font = INFO_FONT
    if color is None: color = INFO_FONT_COLOR
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))

# 새로운 함수
def draw_selected_plant_info(surface, plant_object, start_x, start_y):
    """선택된 식물의 상세 정보를 화면에 그립니다."""
    if plant_object is None or not DEBUG_MODE: # DEBUG_MODE가 꺼져있거나 선택된 식물이 없으면 그리지 않음
        return

    current_y = start_y
    
    # 식물 ID 및 좌표
    id_text = f"Plant ID: {plant_object.plant_id}"
    coord_text = f"Pos: ({plant_object.grid_x}, {plant_object.grid_y})"
    draw_text(surface, id_text, start_x, current_y, font=DEBUG_FONT, color=INFO_FONT_COLOR)
    current_y += DEBUG_INFO_LINE_SPACING // 1.5
    draw_text(surface, coord_text, start_x, current_y, font=DEBUG_FONT, color=INFO_FONT_COLOR)
    current_y += DEBUG_INFO_LINE_SPACING

    # 에너지
    energy_ratio = plant_object.current_energy / plant_object.max_energy_capacity if plant_object.max_energy_capacity > 0 else 0
    energy_text = f"Energy: {plant_object.current_energy:.2f} / {plant_object.max_energy_capacity:.2f}"
    draw_text(surface, energy_text, start_x, current_y, font=DEBUG_FONT, color=INFO_FONT_COLOR)
    current_y += DEBUG_INFO_CATEGORY_SPACING
    pygame.draw.rect(surface, GAUGE_BAR_COLORS["BACKGROUND"], (start_x, current_y, GAUGE_BAR_WIDTH, GAUGE_BAR_HEIGHT))
    pygame.draw.rect(surface, GAUGE_BAR_COLORS["ENERGY"], (start_x, current_y, GAUGE_BAR_WIDTH * energy_ratio, GAUGE_BAR_HEIGHT))
    current_y += GAUGE_BAR_HEIGHT + DEBUG_INFO_LINE_SPACING

    # 물
    water_ratio = plant_object.current_water / plant_object.max_water_capacity if plant_object.max_water_capacity > 0 else 0
    water_text = f"Water: {plant_object.current_water:.2f} / {plant_object.max_water_capacity:.2f}"
    draw_text(surface, water_text, start_x, current_y, font=DEBUG_FONT, color=INFO_FONT_COLOR)
    current_y += DEBUG_INFO_CATEGORY_SPACING
    pygame.draw.rect(surface, GAUGE_BAR_COLORS["BACKGROUND"], (start_x, current_y, GAUGE_BAR_WIDTH, GAUGE_BAR_HEIGHT))
    pygame.draw.rect(surface, GAUGE_BAR_COLORS["WATER"], (start_x, current_y, GAUGE_BAR_WIDTH * water_ratio, GAUGE_BAR_HEIGHT))
    current_y += GAUGE_BAR_HEIGHT + DEBUG_INFO_LINE_SPACING

    # 건강
    health_ratio = plant_object.health / 100.0
    health_text = f"Health: {plant_object.health:.2f} / 100.0"
    draw_text(surface, health_text, start_x, current_y, font=DEBUG_FONT, color=INFO_FONT_COLOR)
    current_y += DEBUG_INFO_CATEGORY_SPACING
    pygame.draw.rect(surface, GAUGE_BAR_COLORS["BACKGROUND"], (start_x, current_y, GAUGE_BAR_WIDTH, GAUGE_BAR_HEIGHT))
    pygame.draw.rect(surface, GAUGE_BAR_COLORS["HEALTH"], (start_x, current_y, GAUGE_BAR_WIDTH * health_ratio, GAUGE_BAR_HEIGHT))
    current_y += GAUGE_BAR_HEIGHT + DEBUG_INFO_LINE_SPACING

    # 크기
    size_text = f"Size: {plant_object.current_size:.4f} (Max: {plant_object.adult_max_size_actual:.3f})"
    draw_text(surface, size_text, start_x, current_y, font=DEBUG_FONT, color=INFO_FONT_COLOR)
    current_y += DEBUG_INFO_LINE_SPACING

    # 상태
    state_text = f"State: {plant_object.current_state.value}"
    draw_text(surface, state_text, start_x, current_y, font=DEBUG_FONT, color=INFO_FONT_COLOR)
    current_y += DEBUG_INFO_LINE_SPACING

    # 나이
    age_text = f"Age: {plant_object.age} cycles"
    draw_text(surface, age_text, start_x, current_y, font=DEBUG_FONT, color=INFO_FONT_COLOR)
    current_y += DEBUG_INFO_LINE_SPACING
    
    # 번식 쿨다운 (추가 정보)
    repro_text = f"Repro Cooldown: {plant_object.reproduction_cooldown}"
    draw_text(surface, repro_text, start_x, current_y, font=DEBUG_FONT, color=INFO_FONT_COLOR)
    current_y += DEBUG_INFO_LINE_SPACING