# visualization.py
import pygame
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, INFO_PANEL_HEIGHT, GAME_AREA_HEIGHT,
                    TERRAIN_COLORS, SOIL_COLOR_STEPS, MAX_SOIL_WATER_LEVEL, MAP_HEIGHT, MAP_WIDTH,
                    INFO_FONT_SIZE, INFO_FONT_COLOR, INFO_LINE_SPACING)
from terrain import TerrainType
from plant import PlantState # PlantState Enum 임포트

pygame.font.init() # 폰트 모듈 초기화
INFO_FONT = pygame.font.SysFont("arial", INFO_FONT_SIZE) # 시스템 폰트 사용, 없으면 기본 폰트

def draw_grid(surface, map_manager):
    """맵 격자와 각 셀의 상태(지형, 수분량)를 그립니다."""
    for r in range(map_manager.height):
        for c in range(map_manager.width):
            tile = map_manager.get_tile(c, r)
            rect = pygame.Rect(c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            
            color = (0,0,0) # 기본 검은색
            if tile.terrain_type == TerrainType.WATER:
                color = TERRAIN_COLORS["WATER"]
            elif tile.terrain_type == TerrainType.ROCK:
                color = TERRAIN_COLORS["ROCK"]
            elif tile.terrain_type == TerrainType.SOIL:
                # 수분량에 따라 색상 변화 (5단계)
                water_ratio = tile.water_level / MAX_SOIL_WATER_LEVEL
                if water_ratio < 0.1: # 매우 건조
                    color = TERRAIN_COLORS["SOIL_DRY"]
                elif water_ratio < 0.3:
                    color = TERRAIN_COLORS["SOIL_MOIST_1"]
                elif water_ratio < 0.6:
                    color = TERRAIN_COLORS["SOIL_MOIST_2"]
                elif water_ratio < 0.85:
                    color = TERRAIN_COLORS["SOIL_MOIST_3"]
                else: # 매우 축축
                    color = TERRAIN_COLORS["SOIL_WET"]
            
            pygame.draw.rect(surface, color, rect)
            # DEBUG: 격자 선 그리기 (옵션)
            # pygame.draw.rect(surface, (50,50,50), rect, 1)


def draw_plants(surface, plant_group):
    """식물들을 화면에 그립니다. Plant 객체의 draw 메서드를 사용합니다."""
    # plant_group.draw(surface) # Sprite Group의 draw 메서드 활용
    # 각 Plant 객체가 자신의 image와 rect를 가지고 있으므로, Group.draw()가 효율적.
    # Plant 클래스의 _update_visuals()에서 image와 rect를 설정해야 함.
    for plant in plant_group:
        plant.draw(surface) # 각 식물의 draw 메서드 호출


def draw_info_panel(surface, time_manager, climate_manager, plant_group, map_manager):
    """화면 상단 또는 하단에 시뮬레이션 정보를 텍스트로 표시합니다."""
    panel_rect = pygame.Rect(0, GAME_AREA_HEIGHT, SCREEN_WIDTH, INFO_PANEL_HEIGHT)
    pygame.draw.rect(surface, (30, 30, 30), panel_rect) # 패널 배경색

    y_offset = GAME_AREA_HEIGHT + 10 # 정보 시작 y 위치
    
    # 1. 시간 정보
    time_text = time_manager.get_current_date_str()
    draw_text(surface, time_text, 10, y_offset)
    y_offset += INFO_LINE_SPACING

    # 2. 식물 수 정보
    total_plants = len(plant_group)
    plant_counts = {state: 0 for state in PlantState}
    for plant in plant_group:
        plant_counts[plant.current_state] += 1
    
    plant_info_str = f"Total Plants: {total_plants} (Seeds: {plant_counts[PlantState.SEED]}, Saplings: {plant_counts[PlantState.SAPLING]}, Adults: {plant_counts[PlantState.ADULT]}, Dead: {plant_counts[PlantState.DEAD]})"
    draw_text(surface, plant_info_str, 10, y_offset)
    y_offset += INFO_LINE_SPACING * 1.5 # 약간 더 넓은 간격

    # 3. 환경 정보 (좌측과 우측으로 나눠서 표시)
    left_x_offset = 10
    right_x_offset = SCREEN_WIDTH // 2 + 10
    env_y_offset = y_offset # 현재 y_offset에서 시작

    avg_soil_water = map_manager.get_average_soil_water_level()
    draw_text(surface, f"Avg Soil Water: {avg_soil_water:.1f}mm", left_x_offset, env_y_offset)
    
    current_temp = climate_manager.current_daily_temperature
    draw_text(surface, f"Current Avg Temp: {current_temp:.1f}C", right_x_offset, env_y_offset)
    env_y_offset += INFO_LINE_SPACING

    rain_info = climate_manager.get_last_rainfall_info_str()
    draw_text(surface, rain_info, left_x_offset, env_y_offset)
    
    day_length = climate_manager.get_day_length_ratio(time_manager.current_season) * 24
    draw_text(surface, f"Day Length: {day_length:.1f} hrs", right_x_offset, env_y_offset)
    # env_y_offset += INFO_LINE_SPACING # 다음 정보가 있다면 추가


def draw_text(surface, text, x, y, font=None, color=None):
    """주어진 위치에 텍스트를 그립니다."""
    if font is None: font = INFO_FONT
    if color is None: color = INFO_FONT_COLOR
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))