from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprite

from random import choice
from math import radians
import math
import time
import json

class Game:
    def __init__(self):
        #Setup
        py.init()
        self.display_surface = py.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        py.display.set_caption("Chibi Survival")
        self.clock = py.time.Clock()
        self.running = True
        
        #Group
        self.all_sprites = AllSprite()
        self.collision_sprites = py.sprite.Group()
        self.bullet_sprites = py.sprite.Group()
        self.skill_sprites = py.sprite.Group()
        self.enemy_sprites = py.sprite.Group()

        #bow timer
        self.can_shoot = True
        self.shoot_time = 0
        self.bow_cooldown = 1000

        #enemy timer
        self.enemy_create = 1500
        self.enemy_event = py.event.custom_type()
        # py.time.set_timer(self.enemy_event, self.enemy_create)
        self.spam_positions = []
        self.damaged_enemies = {}

        #sound
        self.sound_shoot = py.mixer.Sound(join('audio', 'shoot.wav'))
        self.sound_shoot.set_volume(0.3)
        self.impact_sound = py.mixer.Sound(join('audio', 'impact.ogg'))
        self.impact_sound.set_volume(0.3)
        self.music = py.mixer.Sound(join('audio', 'music.wav'))
        self.music.set_volume(0.3)
        # self.music.play(loops=-1)
        #  Lưu trữ âm lượng hiện tại  
        self.music_volume = self.music.get_volume() # Lấy âm lượng ban đầu
        self.sfx_volume = self.sound_shoot.get_volume()  

        # Tạo font chữ
        self.font = py.font.Font(None, 45)
        self.title_font = py.font.Font(None, 55) 
        self.label_font = py.font.Font(None, 40)
        self.home_button_font = py.font.Font(None, 40) 

        # notification
        self.notification_font = py.font.Font(None, 22)
        self.notification_text = None
        self.notification_start_time = 0
        self.notification_duration = 1500
        self.notification_float_in_duration = 300

        # Tạo các dòng chữ
        self.menu_options = ["Continue", "Setting", "Home"]
        self.menu_rects = []
        self.pause_start_time = 0

        # Keybindings
        self.keybindings = {
            'skill_1': py.K_q,
            'skill_2': py.K_e,
            'skill_3': py.K_r
        }
        self.load_keybindings()
        self.rebinding_skill = None # None, 'skill_1', 'skill_2', 'skill_3'

        # Thời gian cooldown cho từng skill
        self.skill_cooldowns = {
            'skill_1': 5000,
            'skill_2': 8000,
            'skill_3': 12000
        }
        self.paused_skill_display_cooldowns = {}
        self.blur_overlay = py.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), py.SRCALPHA)
        self.blur_overlay.fill((128, 128, 128, 150))
        # Thời điểm cuối cùng mỗi skill được sử dụng
        self.skill_last_used = {
            'skill_1': 0,
            'skill_2': 0,
            'skill_3': 0
        }

        #setup
        self.load_images()
        # self.setup()

        # Bắt đầu với trạng thái 'home'
        self.menu_state = 'home'
        self.enemy_timer_active = False
        self.previous_menu_state = 'home'
        self.intro_back_button_rect = None

        # Game Over
        self.game_over = False
        self.start_time = 0
        self.enemies_killed = 0
        self.high_score = 0
        self.new_record = False
        self.load_high_score()
        self.game_over_options = ["Replay", "Exit", "Home"]
        self.game_over_rects = []
        self.survival_time = 0

        self.home_buttons = []
        self.create_home_menu()
        # Animation cho màn hình Home
        self.home_anim_start_time = 0
        self.home_anim_duration = 500 
        self.home_anim_delay = 150 # Thời gian trễ giữa các phần tử

    def load_images(self):
        self.imgBg = py.image.load(join('images', 'bg.png'))
        self.bullet_surf = py.image.load(join('images', 'weapon', 'arrow.png')).convert_alpha()    
        
        # self.skill_surf = py.image.load(join('images', 'skill', '7.png')).convert_alpha()
        self.skill_frames = []
        for folder_path, _, file_names in walk(join('images', 'skill')):
            if file_names:
                for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = py.image.load(full_path).convert_alpha()
                    self.skill_frames.append(surf)

        folders = list(walk(join('images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = py.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)
        #pause
        self.btnPause_surf = py.image.load(join('images', 'setting', 'pause.png')).convert_alpha()
        self.btnPause_rect = self.btnPause_surf.get_rect(topleft=(5, 5))
        self.tblPause_surf = py.image.load(join('images', 'setting', 'tbl_pause.png')).convert_alpha()
        self.tblPause_rect = self.tblPause_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        # Thêm tải ảnh cho Settings  
        self.tblSetting_surf = py.image.load(join('images', 'setting', 'tbl_setting.png')).convert_alpha()
        self.btnBack_surf = py.image.load(join('images', 'setting', 'back.png')).convert_alpha()
        self.tblSetting_rect = self.tblSetting_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.btnBack_rect = self.btnBack_surf.get_rect(topleft=(5, 5))

        # Volume Controls  
        self.btnDecrease_surf = py.image.load(join('images', 'setting', 'btn_decrease.png')).convert_alpha()
        self.btnIncrease_surf = py.image.load(join('images', 'setting', 'btn_increase.png')).convert_alpha()
        self.volume_bar_surf = py.image.load(join('images', 'setting', 'volumn.png')).convert_alpha()

        # Music Volume Rects  
        self.music_volume_bar_rect = self.volume_bar_surf.get_rect(
            center=(self.tblSetting_rect.centerx + 60, self.tblSetting_rect.centery - 120)
        )
        self.btnMusicDecrease_rect = self.btnDecrease_surf.get_rect(
            centery=self.music_volume_bar_rect.centery,
            right=self.music_volume_bar_rect.left + 55
        )
        self.btnMusicIncrease_rect = self.btnIncrease_surf.get_rect(
            centery=self.music_volume_bar_rect.centery,
            left=self.music_volume_bar_rect.right - 55
        )

        #   SFX Volume Rects  
        self.sfx_volume_bar_rect = self.volume_bar_surf.get_rect(
            center=(self.tblSetting_rect.centerx + 60, self.tblSetting_rect.centery - 35)
        )
        self.btnSfxDecrease_rect = self.btnDecrease_surf.get_rect(
            centery=self.sfx_volume_bar_rect.centery,
            right=self.sfx_volume_bar_rect.left + 55
        )
        self.btnSfxIncrease_rect = self.btnIncrease_surf.get_rect(
            centery=self.sfx_volume_bar_rect.centery,
            left=self.sfx_volume_bar_rect.right - 55
        )
        #finish
        self.tblFinish_surf = py.image.load(join('images', 'setting', 'tbl_finish.png')).convert_alpha()
        self.tblFinish_rect = self.tblFinish_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        #button
        self.btnBig_surf = py.image.load(join('images', 'setting', 'L_button.png')).convert_alpha()
        self.btnSmall_surf = py.image.load(join('images', 'setting', 'S_button.png')).convert_alpha()
        self.btnXLarge_surf = py.image.load(join('images', 'setting', 'XL_button.png')).convert_alpha()

        #skill - Chưa dùng đến
        self.skill1_setting = py.image.load(join('images', 'infobar', 'skill1.jpeg')).convert_alpha()
        self.skill2_setting = py.image.load(join('images', 'infobar', 'skill2.jpeg')).convert_alpha()
        self.skill3_setting = py.image.load(join('images', 'infobar', 'skill3.jpeg')).convert_alpha()
        #info bar
        self.info_bar_surf = py.image.load(join('images', 'infobar', 'info_bar.png')).convert_alpha()
        #notify
        self.tblNotify_surf = py.image.load(join('images', 'setting', 'notify.png')).convert_alpha()

    def save_keybindings(self):
        """Lưu keybindings hiện tại vào file JSON."""
        try:
            with open('keybindings.json', 'w') as f:
                # Lưu key code dưới dạng số nguyên
                json.dump(self.keybindings, f, indent=4)
        except IOError as e:
            print(f"Lỗi khi lưu keybindings: {e}")

    def load_keybindings(self):
        try:
            with open('keybindings.json', 'r') as f:
                loaded_bindings = json.load(f)
                # Đảm bảo key là số nguyên (Pygame key constants)
                self.keybindings = {k: int(v) for k, v in loaded_bindings.items()}
                # Kiểm tra xem có đủ 3 skill không, nếu thiếu thì dùng default
                if 'skill_1' not in self.keybindings: self.keybindings['skill_1'] = py.K_q
                if 'skill_2' not in self.keybindings: self.keybindings['skill_2'] = py.K_e
                if 'skill_3' not in self.keybindings: self.keybindings['skill_3'] = py.K_r

        except FileNotFoundError:
            print("Không tìm thấy file keybindings.json. Sử dụng giá trị mặc định.")
            # Nếu file không tồn tại, keybindings đã có giá trị mặc định rồi
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Lỗi khi đọc file keybindings.json: {e}. Sử dụng giá trị mặc định.")
            # Reset về mặc định nếu file bị lỗi
            self.keybindings = {
                'skill_1': py.K_q,
                'skill_2': py.K_e,
                'skill_3': py.K_r
            }
        self.save_keybindings()

    def get_skill_cooldown_ms(self, skill_id):
        level = self.player.level
        base_cooldown = self.skill_cooldowns.get(skill_id, 0)
        reduction_count = 0

        if skill_id == 'skill_1':
            # Skill 1 giảm cooldown ở level 3, 5, 7, 9 
            reduction_levels = [3, 5, 7, 9]
            reduction_amount = 500
            min_cooldown = 3000
            for reduction_level in reduction_levels:
                if level >= reduction_level:
                    reduction_count += 1
                else:
                    break
            calculated_cooldown = base_cooldown - (reduction_count * reduction_amount)
            return max(min_cooldown, calculated_cooldown)

        elif skill_id == 'skill_2':
            # Skill 2 giảm cooldown ở level 6, 10, 11
            reduction_levels = [6, 10, 11]
            reduction_amount = 1000
            min_cooldown = 4000
            for reduction_level in reduction_levels:
                if level >= reduction_level:
                    reduction_count += 1
                else:
                    break
            calculated_cooldown = base_cooldown - (reduction_count * reduction_amount)
            return max(min_cooldown, calculated_cooldown)

        elif skill_id == 'skill_3':
            # Skill 3 giảm cooldown ở level 8
            reduction_levels = [8]
            reduction_amount = 2000
            for reduction_level in reduction_levels:
                if level >= reduction_level:
                    reduction_count += 1
                else:
                    break
            calculated_cooldown = base_cooldown - (reduction_count * reduction_amount)
            return max(0, calculated_cooldown)
        else:
            return 0

    def is_skill_ready(self, skill_id):
        if skill_id not in self.skill_last_used: # Kiểm tra skill tồn tại
             return False
        if skill_id == 'skill_2' and self.player.level < 2:
            return False # Skill 2 bị khóa dưới cấp 2
        if skill_id == 'skill_3' and self.player.level < 4:
            return False # Skill 3 bị khóa dưới cấp 4
        current_time = py.time.get_ticks()
        last_used = self.skill_last_used.get(skill_id, 0)
        # Lấy cooldown cần thiết dựa trên level hiện tại
        required_cooldown_ms = self.get_skill_cooldown_ms(skill_id)
        return current_time - last_used >= required_cooldown_ms
    
    def get_skill_cooldown_remaining(self, skill_id):
        """Lấy thời gian cooldown còn lại (giây), dựa trên cooldown động."""
        if skill_id not in self.skill_last_used:
            return 0
        current_time = py.time.get_ticks()
        last_used = self.skill_last_used.get(skill_id, 0)
        # Lấy cooldown cần thiết dựa trên level hiện tại
        required_cooldown_ms = self.get_skill_cooldown_ms(skill_id)
        elapsed = current_time - last_used

        if elapsed < required_cooldown_ms:
            remaining_ms = required_cooldown_ms - elapsed
            return max(0, remaining_ms / 1000.0) # Chuyển sang giây
        else:
            return 0

    def input(self):
        # Chỉ xử lý input game nếu player và bow tồn tại (tức là game đã start)
        if not hasattr(self, 'player') or not hasattr(self, 'bow') or self.player.is_dead:
            return
        keys = py.key.get_pressed()

        if self.bow and py.mouse.get_pressed()[0] and self.can_shoot:  # Kiểm tra đã vẽ cung tên chưa trước khi bắn
            self.sound_shoot.play()
            pos = self.bow.rect.center + self.bow.player_direction * 50
            Bullet(self.bullet_surf, pos, self.bow.player_direction, (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = py.time.get_ticks()
        # Skill 1 - Sử dụng keybinding đã lưu
        if self.bow and keys[self.keybindings['skill_1']]:
            if self.is_skill_ready('skill_1'):
                self.skill_last_used['skill_1'] = py.time.get_ticks()
                self.sound_shoot.play()
                pos = self.bow.rect.center + self.bow.player_direction * 50
                num_bullets = 5
                angle_offset = 15
                for i in range(num_bullets):
                    angle = radians(angle_offset * (i - num_bullets // 2))
                    rotated_direction = py.Vector2(
                        self.bow.player_direction.x * math.cos(angle) - self.bow.player_direction.y * math.sin(angle),
                        self.bow.player_direction.x * math.sin(angle) + self.bow.player_direction.y * math.cos(angle)
                    )
                    Skill_1(self.bullet_surf, pos, rotated_direction, (self.all_sprites, self.skill_sprites))
            else:
                remaining_cd = self.get_skill_cooldown_remaining('skill_1')
                if remaining_cd > 0: 
                    self.notification_text = f"Skill 1 on cooldown"
                    self.notification_start_time = py.time.get_ticks()

        # Skill 2 - Sử dụng keybinding đã lưu
        if self.bow and keys[self.keybindings['skill_2']]:
            if self.is_skill_ready('skill_2'):
                self.skill_last_used['skill_2'] = py.time.get_ticks()
                Skill_2(self.player.rect.center, self.player, (self.all_sprites, self.skill_sprites))
            else:
                if self.player.level < 2:
                    self.notification_text = "Skill 2 is locked, level 2 required"
                    self.notification_start_time = py.time.get_ticks()
                else: # Đủ cấp độ -> đang cooldown
                    remaining_cd = self.get_skill_cooldown_remaining('skill_2')
                    if remaining_cd > 0:
                        self.notification_text = f"Skill 2 on cooldown"
                        self.notification_start_time = py.time.get_ticks()

        # Skill 3 - Sử dụng keybinding đã lưu
        if self.bow and keys[self.keybindings['skill_3']]:
            if self.is_skill_ready('skill_3'):
                self.skill_last_used['skill_3'] = py.time.get_ticks()
                self.sound_shoot.play()
                pos = self.bow.rect.center + self.bow.player_direction * 555
                Skill_3(self.skill_frames, pos, self.bow.player_direction, (self.all_sprites, self.skill_sprites))
            else:
                if self.player.level < 4:
                    self.notification_text = "Skill 3 is locked, level 4 required"
                    self.notification_start_time = py.time.get_ticks()
                else: # Đủ cấp độ -> đang cooldown
                    remaining_cd = self.get_skill_cooldown_remaining('skill_3')
                    if remaining_cd > 0:
                        self.notification_text = f"Skill 3 on cooldown"
                        self.notification_start_time = py.time.get_ticks()

    def bow_timer(self):
        if not self.can_shoot:
            current_time = py.time.get_ticks()
            # Đảm bảo player tồn tại trước khi truy cập bow_cooldown
            bow_cd = self.bow_cooldown if not hasattr(self, 'player') else self.player.game.bow_cooldown
            if current_time - self.shoot_time >= bow_cd:
                self.can_shoot = True     
     
    def setup(self):
        # Xóa sprite cũ nếu có
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.bullet_sprites.empty()
        self.skill_sprites.empty()
        self.enemy_sprites.empty()
        self.spam_positions.clear()
        self.damaged_enemies.clear()

        map_data = load_pygame(join('data', 'maps', 'world.tmx'))

        # Load Ground
        for x, y, image in map_data.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        # Load Objects (có va chạm vật lý)
        for obj in map_data.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        # Load Collisions (vùng vô hình)
        for obj in map_data.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), py.Surface((obj.width, obj.height)), self.collision_sprites)

        # Load Entities (Player và Enemy Spawns)
        player_pos = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2) # Vị trí mặc định nếu không tìm thấy
        for obj in map_data.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                player_pos = (obj.x, obj.y)
            else: # Enemy spawn point
                self.spam_positions.append((obj.x, obj.y))

        # Tạo Player và Bow (SAU KHI đã có collision_sprites)
        self.bow = Bow(None, self.all_sprites) # Tạo bow trước
        self.player = Player(player_pos, self.all_sprites, self.collision_sprites, self.bow, self)
        self.bow.set_player(self.player) # Gán player cho bow

        # Reset các biến trạng thái game
        self.start_time = py.time.get_ticks()
        self.enemies_killed = 0
        self.game_over = False
        self.new_record = False
        self.survival_time = 0
        # Reset skill cooldowns
        current_time = py.time.get_ticks()
        for skill_id in self.skill_last_used:
            self.skill_last_used[skill_id] = current_time # Reset thời gian sử dụng

        # Khởi động lại timer enemy và nhạc
        self.enemy_create = int(1500 * (0.95)**(self.player.level - 1)) # Tính lại enemy_create dựa trên level (nếu có reset giữa game)
        py.time.set_timer(self.enemy_event, self.enemy_create)
        self.enemy_timer_active = True
        self.music.play(loops=-1)
    
    def reset_game(self):
        if self.enemy_timer_active:
            py.time.set_timer(self.enemy_event, 0)
            self.enemy_timer_active = False
        self.music.stop()

        # Gọi setup để tạo lại mọi thứ
        self.setup()
        # Đặt lại trạng thái menu về 'none' để bắt đầu chơi
        self.set_menu_state('none')

    def bullet_collision(self):
        if self.bullet_sprites and self.enemy_sprites:
            for bullet in self.bullet_sprites:
                for enemy in self.enemy_sprites:
                    if enemy.hitbox_rect.colliderect(bullet.rect):
                        self.impact_sound.play()
                        enemy.destroy()
                        bullet.kill()
                        self.enemies_killed += 1
                        break
    
    def skill_collision(self):
        for skill in self.skill_sprites:
            if isinstance(skill, Skill_1):
                for enemy in self.enemy_sprites:
                    if enemy.hitbox_rect.colliderect(skill.rect):
                        self.impact_sound.play()
                        enemy.destroy()
                        self.enemies_killed += 1
                        skill.kill()
                        break
            elif isinstance(skill, Skill_2):
                pass
            elif isinstance(skill, Skill_3):
                if skill.frame_index == 7 and skill.mask:  #(7.png)
                    for enemy in self.enemy_sprites:
                        if enemy.death_time == 0 and py.sprite.collide_mask(skill, enemy):
                            enemy.destroy()
                            self.enemies_killed += 1
        
    def player_collision(self):
        if self.menu_state == 'none' and not self.player.is_dead:
            colliding_enemies_data = py.sprite.spritecollide(self.player, self.enemy_sprites, False, py.sprite.collide_mask)
            if colliding_enemies_data:
                current_time = py.time.get_ticks()
                damage = 0
                # Tạo một bản sao của dictionary để tránh lỗi khi thay đổi trong lúc lặp
                current_damaged_enemies = self.damaged_enemies.copy()

                for enemy in colliding_enemies_data:
                    # Kiểm tra xem enemy có trong damaged_enemies không VÀ đã đủ cooldown chưa
                    if enemy not in self.damaged_enemies or current_time - self.damaged_enemies.get(enemy, 0) >= self.player.health_bar.damage_cooldown:
                        damage += 100
                        current_damaged_enemies[enemy] = current_time # Cập nhật thời gian gây sát thương

                self.damaged_enemies = current_damaged_enemies # Cập nhật lại dictionary gốc

                if damage > 0: # Chỉ trừ máu nếu có sát thương mới
                    self.player.health -= damage
                    if self.player.health <= 0:
                        self.player.is_dead = True
                        self.player.death_time = py.time.get_ticks()
                        py.mixer.pause()
            else:
                 pass

    def _calculate_float_in_animation(self, animation_start_time, current_time, animation_duration, target_y, start_y_offset=30, initial_alpha=0, final_alpha=255):
        elapsed_time = current_time - animation_start_time
        progress = 0.0
        if animation_duration > 0:
            progress = min(1.0, elapsed_time / animation_duration)
        elif current_time >= animation_start_time: 
            progress = 1.0

        current_animated_y = target_y - start_y_offset * (1 - progress)
        current_animated_alpha = initial_alpha + (final_alpha - initial_alpha) * progress
        return current_animated_y, int(current_animated_alpha)

    def draw_notification(self):
        if self.notification_text:
            current_time = py.time.get_ticks()
            elapsed_total_time = current_time - self.notification_start_time

            if elapsed_total_time < self.notification_duration:
                if "Level Up" in self.notification_text:
                    # Thông báo Level Up: float-in ở giữa màn hình
                    notification_surf = self.notification_font.render(self.notification_text, True, '#181425')
                    target_center_x = WINDOW_WIDTH / 2
                    target_center_y = WINDOW_HEIGHT / 2 - 70

                    animated_y, animated_alpha = self._calculate_float_in_animation(
                        animation_start_time=self.notification_start_time,
                        current_time=current_time,
                        animation_duration=self.notification_float_in_duration,
                        target_y=target_center_y,
                        start_y_offset=-30,
                        initial_alpha=0,
                        final_alpha=255
                    )
                    
                    notification_surf.set_alpha(animated_alpha)
                    notification_rect = notification_surf.get_rect(center=(target_center_x, animated_y))


                    self.display_surface.blit(notification_surf, notification_rect)
                else:
                    # Thông báo skill (cooldown/locked): không hiệu ứng
                    notification_surf = self.notification_font.render(self.notification_text, True, '#181425')
                    if hasattr(self, 'player') and hasattr(self.player, 'info_bar'):
                        info_bar_x = self.player.info_bar.x
                        info_bar_y = self.player.info_bar.y
                        info_bar_width = self.player.info_bar.health_frame_surf.get_width()
                        notification_rect = notification_surf.get_rect(midbottom=(info_bar_x + info_bar_width / 2 + 56, info_bar_y))
                        self.display_surface.blit(notification_surf, notification_rect)
            else:
                self.notification_text = None

    def set_menu_state(self, new_state):
        old_state = self.menu_state
        # Lưu trạng thái hiện tại trước khi thay đổi (trừ khi đang ở settings)
        if self.menu_state != 'settings':
            self.previous_menu_state = self.menu_state

        self.menu_state = new_state

        game_inactive_states = ['paused', 'settings', 'home', 'introduction']
        is_paused_now = (new_state in game_inactive_states)
        was_paused_before = (old_state in game_inactive_states)

        current_ticks = py.time.get_ticks()

        if is_paused_now and not was_paused_before: # Chuyển từ chạy ('none') sang pause/settings/home
            # Phần xử lý logic pause
            if self.enemy_timer_active:
                py.time.set_timer(self.enemy_event, 0)
                self.enemy_timer_active = False
            py.mixer.pause()
            self.pause_start_time = current_ticks # Ghi lại thời điểm bắt đầu pause

            # Lưu trữ giá trị cooldown để hiển thị
            self.paused_skill_display_cooldowns.clear() # Xóa giá trị cũ
            if hasattr(self, 'player'):
                for skill_id in self.skill_cooldowns: # Lặp qua các skill đã định nghĩa
                    # Tính thời gian còn lại TẠI THỜI ĐIỂM PAUSE này
                    remaining_seconds = self.get_skill_cooldown_remaining(skill_id)
                    # Chỉ lưu nếu còn cooldown
                    if remaining_seconds > 0:
                        self.paused_skill_display_cooldowns[skill_id] = remaining_seconds

        elif not is_paused_now and was_paused_before: # Chuyển từ pause/settings/home sang chạy ('none')
            # Phần xử lý logic unpause (điều chỉnh skill_last_used)
            if self.pause_start_time > 0: # Đảm bảo đã có thời điểm bắt đầu pause hợp lệ
                paused_duration = current_ticks - self.pause_start_time
                if hasattr(self, 'player'):
                    for skill_id in self.skill_last_used:
                        if self.skill_last_used[skill_id] < self.pause_start_time:
                            self.skill_last_used[skill_id] += paused_duration
                self.pause_start_time = 0 # Reset lại thời điểm bắt đầu pause

            # Xóa giá trị cooldown hiển thị đã lưu
            self.paused_skill_display_cooldowns.clear()

            # Phần khởi động lại game
            if hasattr(self, 'player'):
                if not self.enemy_timer_active:
                    self.enemy_create = int(1500 * (0.95)**(self.player.level - 1))
                    py.time.set_timer(self.enemy_event, self.enemy_create)
                    self.enemy_timer_active = True
                py.mixer.unpause()

        if new_state == 'paused' and not self.menu_rects:
            self.create_pause_menu()
        elif new_state == 'home' and old_state != 'home': # Chỉ reset anim time khi thực sự chuyển đến home
            self.home_anim_start_time = py.time.get_ticks()
            self.create_pause_menu()
        elif new_state == 'home' and not self.home_buttons:
            self.create_home_menu()

    def create_home_menu(self):
        self.home_buttons.clear()
        button_texts = ["Start Game", "Setting", "Introduction", "Exit"]
        start_y = WINDOW_HEIGHT * 0.38

        for i, text in enumerate(button_texts):
            button_rect = self.btnXLarge_surf.get_rect(
                center=(250, start_y + 100 * i)
            )
            action = text.lower().replace(" ", "_") # vd: "start_game", "setting", "introduction", "exit"
            self.home_buttons.append({'text': text, 'rect': button_rect, 'action': action})

    def draw_home_menu(self):
        current_time = py.time.get_ticks()
        # self.display_surface.fill("black")
        imgBg_rect = self.imgBg.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.display_surface.blit(self.imgBg, imgBg_rect)
        # Vẽ Tiêu đề với hiệu ứng float-in
        title_target_center_x = 250
        title_target_center_y = WINDOW_HEIGHT * 0.18
        title_anim_y, title_alpha = self._calculate_float_in_animation(
            animation_start_time=self.home_anim_start_time, # Tiêu đề bắt đầu ngay
            current_time=current_time,
            animation_duration=self.home_anim_duration,
            target_y=title_target_center_y,
            start_y_offset=-50, # Float từ dưới lên
            initial_alpha=0,
            final_alpha=255
        )
        title_surf = self.title_font.render("Chibi Survival", True, 'orange')
        title_surf.set_alpha(title_alpha)
        title_rect = title_surf.get_rect(center=(title_target_center_x, title_anim_y))
        self.display_surface.blit(title_surf, title_rect)

        # Vẽ các nút với hiệu ứng float-in và trễ
        for i, button in enumerate(self.home_buttons):
            button_anim_actual_start_time = self.home_anim_start_time + (i + 1) * self.home_anim_delay
            
            button_target_center_y = button['rect'].centery # Lấy Y mục tiêu từ rect đã tạo
            button_target_center_x = button['rect'].centerx

            btn_anim_y, btn_alpha = self._calculate_float_in_animation(
                animation_start_time=button_anim_actual_start_time,
                current_time=current_time,
                animation_duration=self.home_anim_duration,
                target_y=button_target_center_y,
                start_y_offset=-50, # Float từ dưới lên
                initial_alpha=0,
                final_alpha=255
            )

            animated_button_rect = self.btnXLarge_surf.get_rect(center=(button_target_center_x, btn_anim_y))
            temp_btn_bg_surf = self.btnXLarge_surf.copy()
            temp_btn_bg_surf.set_alpha(btn_alpha)
            self.display_surface.blit(temp_btn_bg_surf, animated_button_rect)

            text_surf = self.home_button_font.render(button['text'], True, 'white')
            text_surf.set_alpha(btn_alpha)
            text_rect = text_surf.get_rect(center=animated_button_rect.center)
            self.display_surface.blit(text_surf, text_rect)

    def draw_introduction_screen(self):
        imgBg_rect = self.imgBg.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.display_surface.blit(self.imgBg, imgBg_rect)
        if hasattr(self, 'tblSetting_surf') and hasattr(self, 'tblSetting_rect'):
            self.display_surface.blit(self.tblSetting_surf, self.tblSetting_rect)
        else:
            self.display_surface.fill((20, 20, 40))
            print("Warning: tblSetting_surf hoặc tblSetting_rect không khả dụng cho màn hình Introduction.")

        self.intro_back_button_rect = self.btnBack_surf.get_rect(topleft=(5, 5))
        self.display_surface.blit(self.btnBack_surf, self.intro_back_button_rect)

        # Tiêu đề
        title_surf = self.title_font.render("Game Introduction", True, 'orange')
        title_rect = title_surf.get_rect(center=(self.tblSetting_rect.centerx, self.tblSetting_rect.top + 180))
        self.display_surface.blit(title_surf, title_rect)

        # Nội dung
        line_spacing = 30
        current_y = title_rect.bottom + 20
        content_font = py.font.Font(None, 30)
        label_font = py.font.Font(None, 35)
        text_color = 'white'
        highlight_color = 'lightgreen'
        section_color = 'lightblue'
        content_area_left = self.tblSetting_rect.left + 250 # Lề trái cho nội dung bên trong bảng

        # Mục tiêu game
        obj_title_surf = label_font.render("Mục tiêu:", True, section_color)
        obj_title_rect = obj_title_surf.get_rect(topleft=(content_area_left, current_y))
        self.display_surface.blit(obj_title_surf, obj_title_rect)
        current_y += line_spacing + 5

        objective_lines = [
            "- Sống sót càng lâu càng tốt.",
            "- Tiêu diệt kẻ thù để nhận điểm kinh nghiệm (EXP) và lên cấp.",
            "- Lên cấp giúp bạn mạnh hơn, mở khóa và cải thiện kỹ năng."
        ]
        for line in objective_lines:
            line_surf = content_font.render(line, True, text_color)
            line_rect = line_surf.get_rect(topleft=(content_area_left + 30, current_y))
            self.display_surface.blit(line_surf, line_rect)
            current_y += line_spacing

        current_y += line_spacing # Khoảng cách giữa các mục

        # Điều khiển
        ctrl_title_surf = label_font.render("Điều khiển:", True, section_color)
        ctrl_title_rect = ctrl_title_surf.get_rect(topleft=(content_area_left, current_y))
        self.display_surface.blit(ctrl_title_surf, ctrl_title_rect)
        current_y += line_spacing + 5

        controls_info = [
            ("Di chuyển:", "W, A, S, D hoặc các phím mũi tên"),
            ("Bắn (tấn công thường):", "Chuột trái"),
            (f"Skill 1 (Đa tiễn):", f"Phím {py.key.name(self.keybindings['skill_1']).upper()} (Mở khóa: Cấp 1)"),
            (f"Skill 2 (Hồi máu):", f"Phím {py.key.name(self.keybindings['skill_2']).upper()} (Mở khóa: Cấp 2)"),
            (f"Skill 3 (Thần tiễn):", f"Phím {py.key.name(self.keybindings['skill_3']).upper()} (Mở khóa: Cấp 4)"),
            ("Tạm dừng/Mở Menu:", "ESC")
        ]
        # key_description_offset dùng để đặt vị trí bắt đầu của mô tả phím, cách lề của nhãn
        key_description_offset = 300
        for label, key_info in controls_info:
            label_surf = content_font.render(label, True, highlight_color)
            label_rect = label_surf.get_rect(topleft=(content_area_left + 30, current_y))
            self.display_surface.blit(label_surf, label_rect)

            key_surf = content_font.render(key_info, True, text_color)
            # Đặt vị trí mô tả phím dựa trên vị trí của nhãn và offset
            key_rect = key_surf.get_rect(topleft=(label_rect.left + key_description_offset, current_y))
            self.display_surface.blit(key_surf, key_rect)
            current_y += line_spacing

    def create_pause_menu(self):
        self.menu_rects.clear() # Xóa cũ
        y_offset = -100
        self.btnContinue_rect = None
        for option in self.menu_options:
            text_surface = self.font.render(option, True, 'white')
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + y_offset))
            self.menu_rects.append((text_surface, text_rect))
            y_offset += 103
            if option == "Continue":
                self.txtContinue_rect = text_rect        

    def draw_pause_menu(self):
        self.display_surface.blit(self.tblPause_surf, self.tblPause_rect)

        for index, (text_surface, text_rect) in enumerate(self.menu_rects):
            clickable_rect = py.Rect(0, 0, 176, 69)
            clickable_rect.center = text_rect.center
            self.display_surface.blit(text_surface, text_rect)

    def draw_settings_menu(self):
        # Vẽ nền và nút back
        self.display_surface.blit(self.tblSetting_surf, self.tblSetting_rect)
        self.display_surface.blit(self.btnBack_surf, self.btnBack_rect)

        # Vẽ Tiêu đề Music 
        title_surf = self.title_font.render("Volume", True, 'white')
        title_rect = title_surf.get_rect(center=(self.tblSetting_rect.centerx, self.tblSetting_rect.centery - 190)) # Vị trí trên cùng
        self.display_surface.blit(title_surf, title_rect)

        # Vẽ Music Volume  
        music_label_surf = self.label_font.render("Music", True, 'white')
        music_label_rect = music_label_surf.get_rect(
            midright=(self.btnMusicDecrease_rect.left - 15, self.music_volume_bar_rect.centery) # Bên trái nút giảm
        )
        self.display_surface.blit(music_label_surf, music_label_rect)
        # Nút và thanh nền
        self.display_surface.blit(self.btnDecrease_surf, self.btnMusicDecrease_rect)
        self.display_surface.blit(self.btnIncrease_surf, self.btnMusicIncrease_rect)
        self.display_surface.blit(self.volume_bar_surf, self.music_volume_bar_rect)
        # Thanh fill màu
        padx = 62
        pady = 54
        volume_fill_max_width = max(0, self.music_volume_bar_rect.width - (padx * 2))
        volume_fill_height = max(0, self.music_volume_bar_rect.height - (pady * 2))
        music_volume_width = int(volume_fill_max_width * self.music_volume)
        fill_rect_x = self.music_volume_bar_rect.left + padx
        fill_rect_y = self.music_volume_bar_rect.top + pady
        music_volume_fill_rect = py.Rect(fill_rect_x, fill_rect_y, music_volume_width, volume_fill_height)
        if music_volume_width > 0:
            py.draw.rect(self.display_surface, '#4CAF50', music_volume_fill_rect)

        # Vẽ SFX Volume  
        sfx_label_surf = self.label_font.render("SFX", True, 'white')
        sfx_label_rect = sfx_label_surf.get_rect(
            midright=(self.btnSfxDecrease_rect.left - 15, self.sfx_volume_bar_rect.centery) # Bên trái nút giảm SFX
        )
        self.display_surface.blit(sfx_label_surf, sfx_label_rect)
        # Nút và thanh nền
        self.display_surface.blit(self.btnDecrease_surf, self.btnSfxDecrease_rect)
        self.display_surface.blit(self.btnIncrease_surf, self.btnSfxIncrease_rect)
        self.display_surface.blit(self.volume_bar_surf, self.sfx_volume_bar_rect)
        # Thanh fill màu
        sfx_volume_width = int(volume_fill_max_width * self.sfx_volume)
        sfx_fill_rect_x = self.sfx_volume_bar_rect.left + padx
        sfx_fill_rect_y = self.sfx_volume_bar_rect.top + pady
        sfx_volume_fill_rect = py.Rect(sfx_fill_rect_x, sfx_fill_rect_y, sfx_volume_width, volume_fill_height)
        if sfx_volume_width > 0:
            py.draw.rect(self.display_surface, '#4CAF50', sfx_volume_fill_rect)

        # Vẽ Tiêu đề Control 
        title_surf2 = self.title_font.render("Control", True, 'white')
        title_rect2 = title_surf2.get_rect(center=(self.tblSetting_rect.centerx, self.tblSetting_rect.centery + 60))
        self.display_surface.blit(title_surf2, title_rect2)

        # Font và màu cho phím  
        key_font = py.font.Font(None, 35)
        key_color = 'white'
        rebinding_color = 'yellow'

        # Vẽ các nút chức năng (Skill 1, Skill 2, Skill 3)  
        skill_y = title_rect2.bottom + 50 # Vị trí Y cho hàng nút skill
        button_spacing = 260 # Khoảng cách giữa các nút hiển thị phím
        label_key_spacing = 0 # Khoảng cách giữa nhãn skill và nút phím

        # Skill 1 
        skill1_label_surf = self.label_font.render("Skill 1", True, 'white')
        skill1_label_rect = skill1_label_surf.get_rect(
            midright=(self.tblSetting_rect.centerx - button_spacing, skill_y)
        )
        self.display_surface.blit(skill1_label_surf, skill1_label_rect)

        self.skill1_key_rect = self.btnSmall_surf.get_rect(
            midleft=(skill1_label_rect.right + label_key_spacing, skill_y)
        )
        self.display_surface.blit(self.btnSmall_surf, self.skill1_key_rect)

        key1_text = "..." if self.rebinding_skill == 'skill_1' else py.key.name(self.keybindings['skill_1']).upper()
        key1_color = rebinding_color if self.rebinding_skill == 'skill_1' else key_color
        key1_surf = key_font.render(key1_text, True, key1_color)
        key1_rect = key1_surf.get_rect(center=self.skill1_key_rect.center)
        self.display_surface.blit(key1_surf, key1_rect)

        # Skill 2  
        skill2_label_surf = self.label_font.render("Skill 2", True, 'white')
        skill2_label_rect = skill2_label_surf.get_rect(
             midright=(self.tblSetting_rect.centerx, skill_y)
        )
        self.display_surface.blit(skill2_label_surf, skill2_label_rect)

        self.skill2_key_rect = self.btnSmall_surf.get_rect(
            midleft=(skill2_label_rect.right + label_key_spacing, skill_y)
        )
        self.display_surface.blit(self.btnSmall_surf, self.skill2_key_rect)

        key2_text = "..." if self.rebinding_skill == 'skill_2' else py.key.name(self.keybindings['skill_2']).upper()
        key2_color = rebinding_color if self.rebinding_skill == 'skill_2' else key_color
        key2_surf = key_font.render(key2_text, True, key2_color)
        key2_rect = key2_surf.get_rect(center=self.skill2_key_rect.center)
        self.display_surface.blit(key2_surf, key2_rect)

        # Skill 3  
        skill3_label_surf = self.label_font.render("Skill 3", True, 'white')
        skill3_label_rect = skill3_label_surf.get_rect(
             midright=(self.tblSetting_rect.centerx + button_spacing, skill_y)
        )
        self.display_surface.blit(skill3_label_surf, skill3_label_rect)

        self.skill3_key_rect = self.btnSmall_surf.get_rect(
            midleft=(skill3_label_rect.right + label_key_spacing, skill_y)
        )
        self.display_surface.blit(self.btnSmall_surf, self.skill3_key_rect)

        key3_text = "..." if self.rebinding_skill == 'skill_3' else py.key.name(self.keybindings['skill_3']).upper()
        key3_color = rebinding_color if self.rebinding_skill == 'skill_3' else key_color
        key3_surf = key_font.render(key3_text, True, key3_color)
        key3_rect = key3_surf.get_rect(center=self.skill3_key_rect.center)
        self.display_surface.blit(key3_surf, key3_rect)

        # Hướng dẫn  
        if self.rebinding_skill:
            rebind_text_surf = key_font.render(f"Press a new key for {self.rebinding_skill.replace('_', ' ').title()} (ESC to cancel)", True, 'yellow')
            rebind_text_rect = rebind_text_surf.get_rect(center=(self.tblSetting_rect.centerx, self.skill2_key_rect.bottom + 10))
            self.display_surface.blit(rebind_text_surf, rebind_text_rect)

    def check_new_record(self):
        total_score = self.enemies_killed * 100 + int(self.get_survival_time() * 5)
        if total_score > self.high_score:
            self.high_score = total_score
            self.new_record = True
            self.save_high_score()

    def save_high_score(self):
        with open('high_score.txt', 'w') as file:
            file.write(str(self.high_score))

    def load_high_score(self):
        try:
            with open('high_score.txt', 'r') as file:
                self.high_score = int(file.read())
        except FileNotFoundError:
            self.high_score = 0

    def get_survival_time(self):
            # if not self.game_over:
            #     self.survival_time = (py.time.get_ticks() - self.start_time) / 1000 # Thay đổi ở đây
        return self.survival_time

    def create_gameover_menu(self):
        self.game_over_rects.clear()
        x_offset = -200
        for option in self.game_over_options:
            text_surface = self.font.render(option, True, 'white')
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH / 2 + x_offset, WINDOW_HEIGHT / 2 + 270))
            self.game_over_rects.append((text_surface, text_rect))
            x_offset += 190

    def draw_gameover_menu(self):
        if not self.game_over_rects:
            self.create_gameover_menu()
        self.display_surface.blit(self.tblFinish_surf, self.tblFinish_rect)
        # Game Over
        game_over_text = self.font.render("GAME OVER", True, 'white')
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 151))
        self.display_surface.blit(game_over_text, game_over_rect)
        # Thông tin
        minutes = int(self.survival_time // 60)
        seconds = int(self.survival_time % 60)
        total_score = self.enemies_killed * 100 + int(self.survival_time) * 5
        info_x = WINDOW_WIDTH / 2 - 245
        value_x = WINDOW_WIDTH / 2 + 220
        y_offset = WINDOW_HEIGHT / 2 - 90
        # Thời gian sống
        survival_time_text = self.font.render("Survival Time", True, 'black')
        survival_time_rect = survival_time_text.get_rect(topleft=(info_x, y_offset))
        self.display_surface.blit(survival_time_text, survival_time_rect)
        survival_time_value = self.font.render(f"{minutes:02d}:{seconds:02d}", True, 'black')
        survival_time_value_rect = survival_time_value.get_rect(topright=(value_x, y_offset))
        self.display_surface.blit(survival_time_value, survival_time_value_rect)
        y_offset += 50
        # Kẻ thù đã tiêu diệt
        enemies_killed_text = self.font.render("Enemies Killed", True, 'black')
        enemies_killed_rect = enemies_killed_text.get_rect(topleft=(info_x, y_offset))
        self.display_surface.blit(enemies_killed_text, enemies_killed_rect)
        enemies_killed_value = self.font.render(f"{self.enemies_killed}", True, 'black')
        enemies_killed_value_rect = enemies_killed_value.get_rect(topright=(value_x, y_offset))
        self.display_surface.blit(enemies_killed_value, enemies_killed_value_rect)
        y_offset += 50
        # Tổng điểm
        total_score_text = self.font.render("Total Score", True, 'black')
        total_score_rect = total_score_text.get_rect(topleft=(info_x, y_offset))
        self.display_surface.blit(total_score_text, total_score_rect)
        total_score_value = self.font.render(f"{total_score}", True, 'black')
        total_score_value_rect = total_score_value.get_rect(topright=(value_x, y_offset))
        self.display_surface.blit(total_score_value, total_score_value_rect)
        y_offset += 50
        # Kỉ lục mới
        if self.new_record:
            new_record_text = self.font.render("New Record!", True, 'red')
            new_record_rect = new_record_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 75))
            self.display_surface.blit(new_record_text, new_record_rect)
        # Lựa chọn
        for text_surface, text_rect in self.game_over_rects:
            button_rect = self.btnBig_surf.get_rect(center=text_rect.center)
            self.display_surface.blit(self.btnBig_surf, button_rect)
            self.display_surface.blit(text_surface, text_rect)

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            current_ticks = py.time.get_ticks()
            if hasattr(self, 'player') and self.player.is_dead and not self.game_over:
                if current_ticks - self.player.death_time >= self.player.death_duration:
                    self.game_over = True
                    # Tính thời gian sống sót tại thời điểm chết
                    self.survival_time = (self.player.death_time - self.start_time) / 1000
                    self.check_new_record()
                    # Dừng timer enemy khi game over
                    if self.enemy_timer_active:
                        py.time.set_timer(self.enemy_event, 0)
                        self.enemy_timer_active = False

            for event in py.event.get():
                if event.type == py.QUIT:
                    self.running = False
                # Tạo enemy chỉ khi game đang chạy
                if event.type == self.enemy_event and self.menu_state == 'none' and not self.game_over:
                    # Đảm bảo player và spam_positions đã được khởi tạo
                    if hasattr(self, 'player') and self.spam_positions:
                        Enemy(choice(self.spam_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)

                if event.type == py.KEYDOWN:
                    # Xử lý nhấn phím KHI ĐANG CHỜ rebind  
                    if self.menu_state == 'settings' and self.rebinding_skill:
                        if event.key == py.K_ESCAPE:
                            self.rebinding_skill = None
                        else:
                            new_key = event.key
                            # Kiểm tra trùng lặp với các skill khác
                            is_duplicate = False
                            for skill_id, existing_key in self.keybindings.items():
                                if skill_id != self.rebinding_skill and existing_key == new_key:
                                    is_duplicate = True
                                    print(f"Lỗi: Phím '{py.key.name(new_key)}' đã được gán cho {skill_id.replace('_', ' ').title()}.")
                                    break 

                            # Kiểm tra các phím đã dùng (WASD)
                            used_keys = [py.K_w, py.K_a, py.K_s, py.K_d, py.K_LEFT, py.K_RIGHT, py.K_UP, py.K_DOWN, py.K_ESCAPE]
                            if new_key in used_keys:
                                print(f"Lỗi: Không thể gán phím '{py.key.name(new_key)}'.")
                                is_duplicate = True

                            if not is_duplicate:
                                print(f"Đã gán phím '{py.key.name(new_key).upper()}' cho {self.rebinding_skill.title()}")
                                self.keybindings[self.rebinding_skill] = new_key
                                self.rebinding_skill = None
                                self.save_keybindings()
                    # Xử lý nhấn ESC để thoát menu
                    elif event.key == py.K_ESCAPE: # Xử lý ESC khi KHÔNG rebind
                        if self.menu_state == 'none':
                            self.set_menu_state('paused')
                        elif self.menu_state == 'paused':
                            self.set_menu_state('none')
                        elif self.menu_state == 'settings':
                            if not self.rebinding_skill: # Nếu không rebind -> quay lại trạng thái trước đó
                                self.set_menu_state(self.previous_menu_state) # Quay lại home hoặc paused
                            else: # Nếu đang rebind -> hủy rebind
                                self.rebinding_skill = None

                if event.type == py.MOUSEBUTTONUP:
                    if self.menu_state == 'home':
                        for button in self.home_buttons:
                            if button['rect'].collidepoint(event.pos):
                                action = button['action']
                                if action == 'start_game':
                                    self.reset_game()
                                elif action == 'setting':
                                    self.set_menu_state('settings')
                                elif action == 'introduction':
                                    self.set_menu_state('introduction')
                                elif action == 'exit':
                                    self.running = False
                                break
                    elif self.menu_state == 'introduction':
                        if self.intro_back_button_rect and self.intro_back_button_rect.collidepoint(event.pos):
                            self.set_menu_state('home')            
                    elif self.menu_state == 'paused':
                        for index, (text_surface, text_rect) in enumerate(self.menu_rects):
                            clickable_rect = py.Rect(0, 0, 176, 69)
                            clickable_rect.center = text_rect.center
                            if clickable_rect.collidepoint(event.pos):
                                option = self.menu_options[index]
                                if option == "Continue":
                                    self.set_menu_state('none')
                                elif option == "Setting":
                                    self.set_menu_state('settings') 
                                elif option == "Home":
                                    self.set_menu_state('home')
                                break
                    elif self.menu_state == 'settings':
                        # Click trong menu settings
                        if self.btnBack_rect.collidepoint(event.pos):
                            if self.rebinding_skill:
                                self.rebinding_skill = None
                                print("Đã hủy gán phím.")
                            self.set_menu_state(self.previous_menu_state)
                        # Xử lý click Music
                        elif self.btnMusicDecrease_rect.collidepoint(event.pos):
                            self.music_volume = max(0.0, self.music_volume - 0.1)
                            self.music.set_volume(self.music_volume)
                        elif self.btnMusicIncrease_rect.collidepoint(event.pos):
                            self.music_volume = min(1.0, self.music_volume + 0.1)
                            self.music.set_volume(self.music_volume)
                        # Xử lý click SFX
                        elif self.btnSfxDecrease_rect.collidepoint(event.pos):
                            self.sfx_volume = max(0.0, self.sfx_volume - 0.1)
                            self.sound_shoot.set_volume(self.sfx_volume)
                            self.impact_sound.set_volume(self.sfx_volume)
                        elif self.btnSfxIncrease_rect.collidepoint(event.pos):
                            self.sfx_volume = min(1.0, self.sfx_volume + 0.1)
                            self.sound_shoot.set_volume(self.sfx_volume)
                            self.impact_sound.set_volume(self.sfx_volume)
                        elif not self.rebinding_skill:
                            if hasattr(self, 'skill1_key_rect') and self.skill1_key_rect.collidepoint(event.pos):
                                self.rebinding_skill = 'skill_1'
                                print("Nhấn phím mới cho Skill 1")
                            elif hasattr(self, 'skill2_key_rect') and self.skill2_key_rect.collidepoint(event.pos):
                                self.rebinding_skill = 'skill_2'
                                print("Nhấn phím mới cho Skill 2")
                            elif hasattr(self, 'skill3_key_rect') and self.skill3_key_rect.collidepoint(event.pos):
                                self.rebinding_skill = 'skill_3'
                                print("Nhấn phím mới cho Skill 3")
                    elif self.game_over:
                        if not self.game_over_rects:
                            self.create_gameover_menu()

                        for index, (text_surface, text_rect) in enumerate(self.game_over_rects):
                            button_rect = self.btnBig_surf.get_rect(center=text_rect.center)
                            if button_rect.collidepoint(event.pos):
                                option = self.game_over_options[index]
                                if option == "Replay":
                                    self.reset_game()
                                elif option == "Exit":
                                    self.running = False
                                elif option == "Home":
                                    self.set_menu_state('home')
                                    self.game_over = False
                                break  
                    elif self.menu_state == 'none':
                        if self.btnPause_rect.collidepoint(event.pos):
                            self.set_menu_state('paused')               

            if self.menu_state == 'none' and not self.game_over:
                if hasattr(self, 'player') and not self.player.is_dead:
                    if not self.rebinding_skill: # Không nhận input game khi đang rebind
                        self.input()
                    self.survival_time += dt
                    self.bow_timer()
                    self.all_sprites.update(dt)
                    self.player_collision()
                    self.bullet_collision()
                    self.skill_collision()
                elif hasattr(self, 'player') and self.player.is_dead:
                    self.all_sprites.update(dt) # Chỉ update animation chết

            # Draw
            self.display_surface.fill("black")
            if self.menu_state == 'home':
                self.draw_home_menu()
            elif self.menu_state == 'introduction':
                self.draw_introduction_screen()
            elif self.menu_state == 'paused':
                if hasattr(self, 'player'): self.all_sprites.draw(self.player.rect.center)
                if hasattr(self, 'player'): self.player.draw_info_bar(self.display_surface)
                self.display_surface.blit(self.blur_overlay, (0, 0))
                self.draw_pause_menu()
            elif self.menu_state == 'settings':
                if self.previous_menu_state == 'paused':
                    if hasattr(self, 'player'): self.all_sprites.draw(self.player.rect.center)
                    if hasattr(self, 'player'): self.player.draw_info_bar(self.display_surface)
                    self.display_surface.blit(self.blur_overlay, (0, 0))
                if self.previous_menu_state == 'home':
                    imgBg_rect = self.imgBg.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
                    self.display_surface.blit(self.imgBg, imgBg_rect)
                self.draw_settings_menu()
            elif self.game_over:
                self.draw_gameover_menu()
            elif self.menu_state == 'none':
                if hasattr(self, 'player'):
                    self.all_sprites.draw(self.player.rect.center)
                    self.player.draw_info_bar(self.display_surface)
                    self.draw_notification()
                    # Hiển thị thời gian sống sót
                    minutes = int(self.survival_time // 60)
                    seconds = int(self.survival_time % 60)
                    time_text = self.font.render(f"{minutes:02d}:{seconds:02d}", True, 'white')
                    time_rect = time_text.get_rect(topright=(WINDOW_WIDTH - 10, 10))
                    self.display_surface.blit(time_text, time_rect)
                    # Vẽ nút pause nhỏ
                    self.display_surface.blit(self.btnPause_surf, self.btnPause_rect)

            py.display.update()

if __name__ == "__main__":
    game = Game()
    game.run()
