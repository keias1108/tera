# main.py
import pygame
import sys
import time # 프레임 속도 제어를 위해 time 모듈 사용

from config import (SCREEN_WIDTH, SCREEN_HEIGHT, GAME_AREA_HEIGHT, SIMULATION_CYCLES_PER_SECOND,
                    MAP_WIDTH, MAP_HEIGHT, DEBUG_MODE)
from time_manager import TimeManager
from climate import ClimateManager # climate.py로 파일명 변경 필요 -> climate_py로 임시 사용
from map_manager import MapManager
from visualization import draw_grid, draw_plants, draw_info_panel # 식물 그리기 함수 임포트

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    game_surface = pygame.Surface((MAP_WIDTH * config.GRID_SIZE, MAP_HEIGHT * config.GRID_SIZE)) # 게임 영역 서피스
    pygame.display.set_caption("Pygame Plant Ecosystem Simulation MVP")
    clock = pygame.time.Clock()

    # --- 주요 객체 생성 ---
    time_manager = TimeManager()
    # ClimateManager는 TimeManager 참조가 필요하므로 TimeManager 생성 후 초기화
    climate_manager = ClimateManager(time_manager_ref=time_manager) 
    
    # 식물들을 담을 Sprite Group 생성
    all_plants_group = pygame.sprite.Group()
    
    # MapManager는 ClimateManager와 plant_group 참조가 필요
    map_manager = MapManager(width=MAP_WIDTH, height=MAP_HEIGHT, 
                             climate_manager_ref=climate_manager, 
                             plant_group_ref=all_plants_group)
    
    map_manager.initial_plant_placement() # 초기 식물 배치

    running = True
    simulation_paused = False
    last_cycle_time = time.time()
    cycle_interval = 1.0 / SIMULATION_CYCLES_PER_SECOND

    # --- 메인 게임 루프 ---
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE: # 스페이스바로 시뮬레이션 일시정지/재개
                    simulation_paused = not simulation_paused
                    if DEBUG_MODE: print(f"Simulation {'PAUSED' if simulation_paused else 'RESUMED'}")
                if event.key == pygame.K_RIGHT: # 오른쪽 화살표 키로 수동으로 1 cycle 진행 (디버그용)
                    if simulation_paused:
                        perform_simulation_cycle(time_manager, climate_manager, map_manager, all_plants_group)
                        if DEBUG_MODE: print("Manual cycle advanced.")
                if event.key == pygame.K_d: # 디버그 모드 토글 (예시)
                    config.DEBUG_MODE = not config.DEBUG_MODE
                    print(f"Debug mode {'ENABLED' if config.DEBUG_MODE else 'DISABLED'}")


        current_time = time.time()
        if not simulation_paused and (current_time - last_cycle_time >= cycle_interval):
            perform_simulation_cycle(time_manager, climate_manager, map_manager, all_plants_group)
            last_cycle_time = current_time


        # --- 그리기 ---
        screen.fill((0, 0, 0))  # 전체 화면 검은색으로 채우기
        
        # 게임 영역 그리기 (game_surface에 먼저 그림)
        game_surface.fill((20,20,20)) # 게임 영역 배경색 (그리드 바깥)
        draw_grid(game_surface, map_manager)
        draw_plants(game_surface, all_plants_group) # 식물 그룹 그리기
        
        # 게임 서피스를 메인 스크린에 blit
        screen.blit(game_surface, (0,0))

        # 정보 패널 그리기 (메인 스크린에 직접 그림)
        draw_info_panel(screen, time_manager, climate_manager, all_plants_group, map_manager)

        pygame.display.flip()
        # clock.tick(30) # FPS 제한 (그리기 루프에 대한 제한, 시뮬레이션 속도와는 별개)
                         # SIMULATION_CYCLES_PER_SECOND로 시뮬레이션 속도를 제어하므로 여기선 너무 낮출 필요 없음.

    pygame.quit()
    sys.exit()

def perform_simulation_cycle(time_manager, climate_manager, map_manager, plant_group):
    """한 시뮬레이션 사이클의 로직을 수행합니다."""
    year_changed = time_manager.update()
    if year_changed:
        climate_manager.apply_yearly_fluctuations() # 새해가 되면 연간 변동성 적용

    # 1. 일일 기후 업데이트 (온도, 강수량 계산)
    current_temp, rain_today = climate_manager.update_daily_climate()

    # 2. 맵 환경 업데이트 (토양 온도, 수분 등)
    map_manager.update_map_environment(current_temp, rain_today)

    # 3. 식물 업데이트
    # plant_group.sprites()로 현재 그룹 내 모든 스프라이트의 리스트를 가져와 순회 (이터레이션 중 변경 문제 방지)
    for plant_sprite in list(plant_group.sprites()): 
        # 식물이 위치한 타일 정보 가져오기
        soil_tile = map_manager.get_tile(plant_sprite.grid_x, plant_sprite.grid_y)
        if soil_tile:
            # plant.update() 호출 시 climate_manager 자체를 넘겨주어 필요한 정보(온도, 일조량 등)를 가져가도록 함
            plant_sprite.update(soil_tile, climate_manager, time_manager)
        else:
            if DEBUG_MODE: print(f"Warning: Plant at ({plant_sprite.grid_x},{plant_sprite.grid_y}) has no valid soil tile. Skipping update.")
            # 필요시 이 식물을 제거하는 로직 추가 가능
            # plant_sprite.kill() 

    if DEBUG_MODE and time_manager.total_cycles_elapsed % 30 == 0 : # 일정 주기마다 정보 출력
        print(f"Cycle: {time_manager.total_cycles_elapsed}, Date: {time_manager.get_current_date_str()}, Plants: {len(plant_group)}")


if __name__ == '__main__':
    # config.py의 일부 값들을 main.py 실행 시점에 맞게 조정 (예: MAP_HEIGHT)
    # 이 부분은 config.py 자체에서 계산하거나, main 시작 전에 설정하는 것이 더 깔끔할 수 있습니다.
    # 여기서는 config.py에 GAME_AREA_HEIGHT를 사용한 계산이 이미 있다고 가정합니다.
    import config # config 모듈 임포트 (MAP_WIDTH, MAP_HEIGHT 등 사용 위함)
    
    # main.py에서 ClimateManager 임포트 시 파일명 확인
    # climate.py 로 생성했으므로, from climate import ClimateManager 가 맞습니다.
    # 현재 코드에서는 climate_py로 되어있어 수정이 필요합니다.
    # -> 위 main 함수 내에서 from climate_py import ClimateManager를 from climate import ClimateManager로 변경했다고 가정.
    #    (실제 파일 생성 시에는 climate.py로 생성할 것이므로)

    main()