# main.py
import pygame
import sys
import time 
import config # config 모듈 임포트 (DEBUG_MODE 등 사용)

from config import (SCREEN_WIDTH, SCREEN_HEIGHT, GAME_AREA_HEIGHT, SIMULATION_CYCLES_PER_SECOND,
                    MAP_WIDTH, MAP_HEIGHT, DEBUG_MODE, GRID_SIZE, # GRID_SIZE 추가
                    DEBUG_INFO_START_X, DEBUG_INFO_START_Y) # 디버그 정보 위치 임포트
from time_manager import TimeManager
from climate import ClimateManager # climate.py로 가정 (이전 수정 사항 반영)
from map_manager import MapManager
from visualization import draw_grid, draw_plants, draw_info_panel, draw_selected_plant_info # 새 함수 임포트

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    # 게임 영역 서피스 크기는 맵 크기와 그리드 크기에 따라 결정
    game_surface_width = MAP_WIDTH * GRID_SIZE
    game_surface_height = MAP_HEIGHT * GRID_SIZE # GAME_AREA_HEIGHT 대신 실제 맵 픽셀 높이 사용
    game_surface = pygame.Surface((game_surface_width, game_surface_height)) 
    
    pygame.display.set_caption("Pygame Plant Ecosystem Simulation MVP")
    clock = pygame.time.Clock()

    time_manager = TimeManager()
    climate_manager = ClimateManager(time_manager_ref=time_manager) 
    all_plants_group = pygame.sprite.Group()
    map_manager = MapManager(width=MAP_WIDTH, height=MAP_HEIGHT, 
                             climate_manager_ref=climate_manager, 
                             plant_group_ref=all_plants_group)
    map_manager.initial_plant_placement()

    running = True
    simulation_paused = False
    last_cycle_time = time.time()
    cycle_interval = 1.0 / SIMULATION_CYCLES_PER_SECOND if SIMULATION_CYCLES_PER_SECOND > 0 else 0

    selected_plant_for_debug = None # 선택된 식물 저장 변수

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    simulation_paused = not simulation_paused
                    if config.DEBUG_MODE: print(f"Simulation {'PAUSED' if simulation_paused else 'RESUMED'}")
                if event.key == pygame.K_RIGHT:
                    if simulation_paused or SIMULATION_CYCLES_PER_SECOND == 0: # 수동 진행은 시뮬레이션 속도 0일때도 가능
                        perform_simulation_cycle(time_manager, climate_manager, map_manager, all_plants_group)
                        if config.DEBUG_MODE: print("Manual cycle advanced by key press.")
                if event.key == pygame.K_d: 
                    config.DEBUG_MODE = not config.DEBUG_MODE # 전역 DEBUG_MODE 변경
                    print(f"Debug mode {'ENABLED' if config.DEBUG_MODE else 'DISABLED'}")
                    if not config.DEBUG_MODE: # 디버그 모드 끌 때 선택된 식물 정보도 끔
                        selected_plant_for_debug = None 
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and config.DEBUG_MODE: # 좌클릭 & 디버그 모드일 때만 식물 선택
                    mouse_x, mouse_y = event.pos # 화면 전체 기준 좌표
                    
                    # 클릭 좌표가 game_surface 영역 내에 있는지 확인
                    if 0 <= mouse_x < game_surface_width and 0 <= mouse_y < game_surface_height:
                        clicked_grid_x = mouse_x // GRID_SIZE
                        clicked_grid_y = mouse_y // GRID_SIZE
                        
                        if config.DEBUG_MODE: print(f"DEBUG: Mouse click at screen ({mouse_x},{mouse_y}) -> grid ({clicked_grid_x},{clicked_grid_y})")

                        newly_selected_plant = None
                        for plant in all_plants_group:
                            if plant.grid_x == clicked_grid_x and plant.grid_y == clicked_grid_y:
                                newly_selected_plant = plant
                                break
                        
                        if newly_selected_plant:
                            selected_plant_for_debug = newly_selected_plant
                            if config.DEBUG_MODE:
                                print(f"DEBUG: Selected plant at ({selected_plant_for_debug.grid_x},{selected_plant_for_debug.grid_y}), ID: {selected_plant_for_debug.plant_id}, State: {selected_plant_for_debug.current_state.value}")
                        else:
                            # 식물이 없는 곳을 클릭하면 선택 해제 (선택적)
                            # selected_plant_for_debug = None 
                            # if config.DEBUG_MODE: print(f"DEBUG: No plant found at grid ({clicked_grid_x},{clicked_grid_y}). Selection cleared.")
                            pass # 빈곳 클릭시 선택 유지 또는 해제 정책 결정 필요 (현재는 유지)
                    # else:
                        # if config.DEBUG_MODE: print(f"DEBUG: Click outside game area.")


        current_time = time.time()
        if not simulation_paused and cycle_interval > 0 and (current_time - last_cycle_time >= cycle_interval):
            perform_simulation_cycle(time_manager, climate_manager, map_manager, all_plants_group)
            last_cycle_time = current_time
        elif cycle_interval == 0 and not simulation_paused: # 속도 0이면 매 프레임 진행하지 않음 (수동 진행만)
            pass


        screen.fill((0, 0, 0))
        
        game_surface.fill((20,20,20)) 
        draw_grid(game_surface, map_manager)
        draw_plants(game_surface, all_plants_group)
        screen.blit(game_surface, (0,0)) # game_surface를 (0,0)에 그림

        draw_info_panel(screen, time_manager, climate_manager, all_plants_group, map_manager)

        # 선택된 식물 정보 표시 (DEBUG_MODE 활성화 시)
        if selected_plant_for_debug and config.DEBUG_MODE:
            # DEBUG_INFO_START_X, DEBUG_INFO_START_Y는 config.py에서 가져옴
            draw_selected_plant_info(screen, selected_plant_for_debug, DEBUG_INFO_START_X, DEBUG_INFO_START_Y)

        pygame.display.flip()
        # FPS 제한은 시뮬레이션 속도와 별개로 유지 가능
        # clock.tick(30) # 루프가 너무 빨리 돌지 않도록 제한 (CPU 사용량 관리)
                         # 단, SIMULATION_CYCLES_PER_SECOND가 매우 높으면 이 값이 영향을 줄 수 있음

    pygame.quit()
    sys.exit()

def perform_simulation_cycle(time_manager, climate_manager, map_manager, plant_group):
    if config.DEBUG_MODE: print(f"\n--- Cycle {time_manager.total_cycles_elapsed + 1} Start ---")
    year_changed = time_manager.update()
    if year_changed:
        climate_manager.apply_yearly_fluctuations()

    current_temp, rain_today = climate_manager.update_daily_climate()
    map_manager.update_map_environment(current_temp, rain_today)

    for plant_sprite in list(plant_group.sprites()): 
        soil_tile = map_manager.get_tile(plant_sprite.grid_x, plant_sprite.grid_y)
        if soil_tile:
            plant_sprite.update(soil_tile, climate_manager, time_manager)
        else:
            if config.DEBUG_MODE: print(f"Warning: Plant {getattr(plant_sprite, 'plant_id', 'N/A')} at ({plant_sprite.grid_x},{plant_sprite.grid_y}) has no valid soil tile. Skipping update.")


if __name__ == '__main__':
    # import config # main 함수 내에서 이미 임포트
    # climate.py 파일명을 확인하고 올바르게 임포트 되었는지 확인 필요
    main()