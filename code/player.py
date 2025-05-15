from settings import *

class Player(py.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites, bow, game):
        super().__init__(groups)
        self.load_images()
        self.state, self.frame_index = 'down', 0
        self.image = py.image.load(join('images', 'player', self.state, '0.png')).convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-60, -90)

        # Di chuyển
        self.pos = py.Vector2(self.rect.center)
        self.direction = py.Vector2()
        self.speed = 300
        self.collision_sprites = collision_sprites

        #death
        self.is_dead = False
        self.death_time = 0
        self.death_duration = 1000
        self.bow = bow
        self.game = game
        self.bow_killed = False
        self.health = 1000

        #health bar
        self.level = 1
        self.max_level = 11
        self.max_exp = 100
        self.current_exp = 0
        self.health_bar = HealthBar(self, game)
        self.info_bar = InfoBar(self, game)
    
    def draw_health_bar(self, surface):
        self.health_bar.update_health()
        self.health_bar.draw(surface)

    def draw_info_bar(self, surface):
        self.health_bar.update_health()
        self.info_bar.update_health()
        self.health_bar.draw(surface)
        self.info_bar.draw(surface)

    def load_images(self):
        self.frames = {'left': [], 'right': [], 'up': [], 'down': [], 'die': []}
        for state in self.frames.keys():           
            for folder_path, sub_folder, file_names in walk(join('images', 'player', state)):
                if file_names:
                    for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                        full_path = join(folder_path, file_name)
                        suft = py.image.load(full_path).convert_alpha()
                        self.frames[state].append(suft)

    def input(self):
        keys = py.key.get_pressed()
        self.direction.x = int(keys[py.K_d] or keys[py.K_RIGHT]) - int(keys[py.K_a] or keys[py.K_LEFT])
        self.direction.y = int(keys[py.K_s] or keys[py.K_DOWN]) - int(keys[py.K_w] or keys[py.K_UP])
        self.direction = self.direction.normalize() if self.direction else self.direction

    def move(self, dt):
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox_rect.x = round(self.pos.x)
        self.collision('horizontal')
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox_rect.y = round(self.pos.y)
        self.collision('vertical')

        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0:  # Đi sang phải
                        self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0:  # Đi sang trái
                        self.hitbox_rect.left = sprite.rect.right
                    # Cập nhật lại vị trí thực tế để tránh bị kẹt
                    self.pos.x = self.hitbox_rect.x

                else:  # direction == 'vertical'
                    if self.direction.y > 0:  # Đi xuống
                        self.hitbox_rect.bottom = sprite.rect.top
                    if self.direction.y < 0:  # Đi lên
                        self.hitbox_rect.top = sprite.rect.bottom
                    self.pos.y = self.hitbox_rect.y

    def animate(self, dt):
        if self.is_dead:
            self.state = 'die'
        else:
            if self.direction.x != 0:
                self.state = 'right' if self.direction.x > 0 else 'left'     
            if self.direction.y != 0:
                self.state = 'down' if self.direction.y > 0 else 'up'
        
        self.frame_index = self.frame_index + 5 * dt if self.direction or self.is_dead else 0
        self.image = self.frames[self.state][int(self.frame_index) % len(self.frames[self.state])]

    def death_timer(self):
        if py.time.get_ticks() - self.death_time >= self.death_duration:
            self.kill()

    def update_exp(self, exp_gain=0):
        if self.level < self.max_level:
            self.current_exp += exp_gain
            if self.current_exp >= self.max_exp:
                self.level_up()

    def level_up(self):
        if self.level < self.max_level:
            self.level += 1
            # Ưu tiên thông báo mở khóa skill hoặc đạt max level
            if self.level == 2: # Mở khóa Skill 2
                self.game.notification_text = "Skill 2 Unlocked!"
                self.game.notification_type = "unlock_skill_2"
            elif self.level == 4: # Mở khóa Skill 3
                self.game.notification_text = "Skill 3 Unlocked!"
                self.game.notification_type = "unlock_skill_3"
            elif self.level == self.max_level: # Đạt cấp tối đa
                self.game.notification_text = "Max Level Reached!"
                self.game.notification_type = "max_level"
            else: # Thông báo lên cấp thông thường
                if hasattr(self.game, 'notification_text'):
                    self.game.notification_text = "Level Up"
                    # self.game.notification_start_time = py.time.get_ticks()
                    self.game.notification_type = "level_up_original" 
            
            self.game.notification_start_time = py.time.get_ticks()

            exp_overflow = self.current_exp - self.max_exp # Giữ lại exp thừa
            self.current_exp = max(0, exp_overflow) # Đặt exp về 0 hoặc exp thừa
            self.max_exp = int(100 * (1.2)**(self.level - 1))
            self.update_game_difficulty()
            self.update_max_health()
            # Có thể gọi update_exp lần nữa nếu có exp thừa
            if self.current_exp > 0:
                self.update_exp(0) # Để kiểm tra level up lần nữa nếu exp thừa đủ và chưa max level

    def update_max_health(self):
        health_ratio = self.health / self.health_bar.max_health
        new_max_health = int(1000 * (1.1)**(self.level - 1))
        self.health = int(new_max_health * health_ratio)
        # Cập nhật max_health cho cả hai thanh
        self.health_bar.max_health = new_max_health
        self.info_bar.max_health = new_max_health
        # Cập nhật lại delayed health
        self.health_bar.delayed_health = self.health
        self.info_bar.delayed_health = self.health

    def update_game_difficulty(self):
        self.game.enemy_create = int(1500 * (0.95)**(self.level - 1))
        self.game.bow_cooldown = int(1000 * (0.95)**(self.level - 1))
        # Chỉ đặt lại timer nếu game đang chạy (không pause)
        if self.game.menu_state == 'none' and self.game.enemy_timer_active:
            py.time.set_timer(self.game.enemy_event, self.game.enemy_create)
        elif not self.game.enemy_timer_active and self.game.menu_state == 'none':
            # Nếu timer đang không active nhưng game đang chạy, bật lại
            py.time.set_timer(self.game.enemy_event, self.game.enemy_create)
            self.game.enemy_timer_active = True

        self.speed = int(300 * (1.05)**(self.level - 1))
        for enemy in self.game.enemy_sprites:
            # Cập nhật tốc độ cho enemy hiện có
            enemy.speed = int(250 * (1.06)**(self.level - 1))
        # Cập nhật damage cooldown cho cả hai thanh
        self.health_bar.damage_cooldown = int(1000 * (0.95)**(self.level - 1))
        self.info_bar.damage_cooldown = int(1000 * (0.95)**(self.level - 1))

    def update(self, dt):
        if self.is_dead and not self.bow_killed:
            self.bow.kill()
            self.bow_killed = True
        if self.is_dead:
            self.death_timer()
            self.animate(dt)
        else:
            self.input()
            self.move(dt)
            self.animate(dt)

class HealthBar:
    def __init__(self, player, game):
        self.player = player
        self.game = game
        self.max_health = 1000
        # self.player.health = self.max_health
        self.health_frame_surf = py.image.load(join('images', 'player', 'hp.png')).convert_alpha()
        self.health_width = 119
        self.health_height = 9
        self.x = WINDOW_WIDTH / 2 - self.health_frame_surf.get_width() / 2
        self.y = WINDOW_HEIGHT / 2 - 118
        self.current_health_width = self.health_width
        # self.health_ratio = self.player.health / self.max_health
        #Thanh máu phụ
        self.delayed_health = self.player.health
        self.delayed_health_width = self.health_width
        self.delay_speed = 0.05
        self.create_health_surface()
        self.delayed_health_surf = py.Surface((self.delayed_health_width, self.health_height), py.SRCALPHA) # Tạo surface cho thanh máu cam
        self.delayed_health_surf.fill('orange')
        # EXP Bar
        # self.max_exp = 100  # EXP cần để lên cấp 2
        # self.current_exp = 0
        self.exp_width = 104
        self.exp_height = 4
        self.font = py.font.Font(None, 26)
        self.damage_cooldown = 1000

    def create_health_surface(self):
        self.health_surf = py.Surface((self.current_health_width, self.health_height), py.SRCALPHA)
        self.health_surf.fill('red')

    def update_health(self):
        self.max_health = self.player.health_bar.max_health # Lấy max_health mới
        # Tính toán tỉ lệ và chiều rộng thanh máu đỏ
        if self.max_health > 0: 
            self.health_ratio = max(0, min(1, self.player.health / self.max_health)) # Đảm bảo tỉ lệ từ 0 đến 1
        else:
            self.health_ratio = 0
        self.current_health_width = int(self.health_width * self.health_ratio)
        self.create_health_surface()

        # Cập nhật thanh máu phụ (cam)
        target_health = self.player.health
        if self.delayed_health > target_health:
            self.delayed_health -= self.delay_speed * (self.delayed_health - target_health) * 0.1 + 1 # Giảm nhanh hơn khi chênh lệch lớn
            self.delayed_health = max(target_health, self.delayed_health) # Không giảm xuống dưới máu hiện tại
        elif self.delayed_health < target_health: # Trường hợp hồi máu
             self.delayed_health = target_health

        # Tính toán chiều rộng thanh máu cam
        if self.max_health > 0:
            delayed_ratio = max(0, min(1, self.delayed_health / self.max_health))
        else:
            delayed_ratio = 0
        self.delayed_health_width = int(self.health_width * delayed_ratio)
        # Tạo lại surface cam (chỉ khi cần vẽ)
        self.delayed_health_surf = py.Surface((self.delayed_health_width, self.health_height), py.SRCALPHA)
        self.delayed_health_surf.fill('orange')

    def draw(self, surface):
        # Vẽ khung nền
        surface.blit(self.health_frame_surf, (self.x, self.y))

        # Tính toán và vẽ EXP Bar
        current_exp_width = 0
        if self.player.max_exp > 0:
             exp_ratio = max(0, min(1, self.player.current_exp / self.player.max_exp)) # Đảm bảo tỉ lệ 0-1
             current_exp_width = int(self.exp_width * exp_ratio) # Dùng self.exp_width của thanh này

        if current_exp_width > 0:
            exp_surf = py.Surface((current_exp_width, self.exp_height), py.SRCALPHA)
            exp_surf.fill('#1BD1FF')
            exp_rect = py.Rect(self.x + 38, self.y + 7 + self.health_height + 9, current_exp_width, self.exp_height)
            surface.blit(exp_surf, exp_rect)

        # Vẽ thanh máu cam
        delayed_health_rect = py.Rect(self.x + 38, self.y + 7, self.delayed_health_width, self.health_height)
        surface.blit(self.delayed_health_surf, delayed_health_rect)

        # Vẽ thanh máu đỏ
        health_rect = py.Rect(self.x + 38, self.y + 7, self.current_health_width, self.health_height)
        surface.blit(self.health_surf, health_rect)

        # Vẽ Level - Lấy level từ Player
        level_text = self.font.render(f"{self.player.level}", True, 'white')
        level_rect = level_text.get_rect(center=(self.x + 17, self.y + 18)) # Vị trí cho HealthBar
        surface.blit(level_text, level_rect)

class InfoBar(HealthBar): # Kế thừa Class HealthBar
    def __init__(self, player, game):
        super().__init__(player, game)

        self.health_frame_surf = self.game.info_bar_surf
        # self.x = WINDOW_WIDTH / 2 - self.health_frame_surf.get_width() / 2
        self.x = WINDOW_WIDTH - self.health_frame_surf.get_width() - 10
        self.y = WINDOW_HEIGHT - self.health_frame_surf.get_height() - 10

        self.health_width = 244
        self.exp_width = 244

        self.cooldown_font = py.font.Font(None, 26)
        self.skill_icon_size = 50 # Kích thước của vùng icon skill

        self.skill_icon_offsets = {
            'skill_1': (173, 21),
            'skill_2': (173 + self.skill_icon_size + 10, 21),
            'skill_3': (173 + self.skill_icon_size * 2 + 20, 21)
        }
        # Tạ lớp phủ cooldown
        self.cooldown_overlay = py.Surface((self.skill_icon_size, self.skill_icon_size), py.SRCALPHA)
        self.cooldown_overlay.fill((0, 0, 0, 180)) 

        self.skill_key_font = py.font.Font(None, 22)
        self.update_health()

    def draw(self, surface):
        surface.blit(self.health_frame_surf, (self.x, self.y))

        health_bar_offset_x = 135
        health_bar_offset_y = 87
        exp_bar_offset_y_diff = 15 # Khoảng cách dọc giữa thanh máu và exp
        level_center_offset_x = 106
        level_center_offset_y = 108

        current_exp_width = 0
        if self.player.max_exp > 0:
            exp_ratio = max(0, min(1, self.player.current_exp / self.player.max_exp))
            # Dùng self.exp_width của InfoBar
            current_exp_width = int(self.exp_width * exp_ratio)

        if current_exp_width > 0:
            exp_surf = py.Surface((current_exp_width, self.exp_height + 4), py.SRCALPHA)
            exp_surf.fill('#1BD1FF')
            exp_rect = py.Rect(
                self.x + health_bar_offset_x,
                self.y + health_bar_offset_y + self.health_height + exp_bar_offset_y_diff,
                current_exp_width,
                self.exp_height
            )
            surface.blit(exp_surf, exp_rect)

        # Vẽ thanh máu cam - Dùng offset của InfoBar
        delayed_health_rect = py.Rect(
            self.x + health_bar_offset_x,
            self.y + health_bar_offset_y,
            self.delayed_health_width,
            self.health_height
        )
        surface.blit(self.delayed_health_surf, delayed_health_rect)

        # Vẽ thanh máu đỏ - Dùng offset của InfoBar
        health_rect = py.Rect(
            self.x + health_bar_offset_x,
            self.y + health_bar_offset_y,
            self.current_health_width,
            self.health_height
        )
        surface.blit(self.health_surf, health_rect)

        # Vẽ Level - Lấy level từ Player, dùng offset của InfoBar
        level_text = self.font.render(f"{self.player.level}", True, 'white')
        level_rect = level_text.get_rect(
            center=(self.x + level_center_offset_x + 1, self.y + level_center_offset_y)
        )
        surface.blit(level_text, level_rect)

        detail_font = py.font.Font(None, 17)
        health_text_str = f"{int(self.player.health)} / {int(self.player.health_bar.max_health)}"
        health_text_surf = detail_font.render(health_text_str, True, 'white')
        health_text_rect = health_text_surf.get_rect(
            center=(self.x + health_bar_offset_x + self.health_width / 2, health_rect.top + 5)
        )
        surface.blit(health_text_surf, health_text_rect)

        exp_text_str = "EXP: MAX"
        if self.player.max_exp > 0:
             exp_text_str = f"{int(self.player.current_exp)} / {int(self.player.max_exp)}"

        exp_text_surf = detail_font.render(exp_text_str, True, 'white')
        exp_bar_y_pos = self.y + health_bar_offset_y + self.health_height + exp_bar_offset_y_diff
        exp_text_rect = exp_text_surf.get_rect(
            center=(self.x + health_bar_offset_x + self.exp_width / 2, exp_bar_y_pos + 5)
        )
        surface.blit(exp_text_surf, exp_text_rect)

        # Vẽ cooldown / trạng thái khóa
        for skill_id, offset in self.skill_icon_offsets.items():
            icon_x = self.x + offset[0]
            icon_y = self.y + offset[1]

            # Vẽ ký tự phím tắt của skill
            if skill_id in self.game.keybindings:
                key_name = py.key.name(self.game.keybindings[skill_id]).upper()
                key_surf = self.skill_key_font.render(key_name, True, 'white')
                key_rect = key_surf.get_rect(topright=(icon_x + self.skill_icon_size - 3, icon_y + 3))
                surface.blit(key_surf, key_rect)

            is_locked = False
            required_level = 0
            if skill_id == 'skill_2':
                required_level = 2
                if self.player.level < required_level:
                    is_locked = True
            elif skill_id == 'skill_3':
                required_level = 4
                if self.player.level < required_level:
                    is_locked = True

            if is_locked:
                # Vẽ lớp phủ màu xám đậm để biểu thị bị khóa
                locked_overlay = py.Surface((self.skill_icon_size, self.skill_icon_size), py.SRCALPHA)
                locked_overlay.fill((50, 50, 50, 200)) # Màu xám đậm, khá mờ
                surface.blit(locked_overlay, (icon_x, icon_y))

                #Vẽ chữ cấp độ yêu cầu nhỏ ở góc
                level_req_font = py.font.Font(None, 18) 
                level_req_text = f"Lv.{required_level}"
                level_req_surf = level_req_font.render(level_req_text, True, 'yellow')
                level_req_rect = level_req_surf.get_rect(bottomright=(icon_x + self.skill_icon_size - 4, icon_y + self.skill_icon_size - 2)) # Góc dưới phải
                surface.blit(level_req_surf, level_req_rect)

            else: # Skill không bị khóa, kiểm tra cooldown
                remaining_cd_seconds = 0 
                is_paused = self.game.menu_state != 'none'

                if is_paused:
                    # Lấy giá trị đã lưu trữ khi pause từ đối tượng game
                    remaining_cd_seconds = self.game.paused_skill_display_cooldowns.get(skill_id, 0)
                else:
                    # Tính toán như bình thường khi game đang chạy
                    remaining_cd_seconds = self.game.get_skill_cooldown_remaining(skill_id)

                if remaining_cd_seconds > 0:
                    # 1. Vẽ lớp phủ mờ cooldown
                    surface.blit(self.cooldown_overlay, (icon_x, icon_y))

                    # 2. Vẽ text thời gian đếm ngược
                    timer_text = f"{remaining_cd_seconds:.1f}"
                    timer_surf = self.cooldown_font.render(timer_text, True, 'white')
                    timer_rect = timer_surf.get_rect(
                        center=(icon_x + self.skill_icon_size / 2, icon_y + self.skill_icon_size / 2)
                    )
                    surface.blit(timer_surf, timer_rect)
    