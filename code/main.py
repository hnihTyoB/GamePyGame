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
        py.display.set_caption("Free Fire Fake")
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

        #skill timer
        self.can_skill = True
        self.skill_time = 0
        self.skill_cooldown = 500

        #enemy timer
        self.enemy_create = 1500
        self.enemy_event = py.event.custom_type()
        py.time.set_timer(self.enemy_event, self.enemy_create)
        self.spam_positions = []
        self.damaged_enemies = {}

        #sound
        self.sound_shoot = py.mixer.Sound(join('audio', 'shoot.wav'))
        self.sound_shoot.set_volume(0.3)
        self.impact_sound = py.mixer.Sound(join('audio', 'impact.ogg'))
        self.impact_sound.set_volume(0.3)
        self.music = py.mixer.Sound(join('audio', 'music.wav'))
        self.music.set_volume(0.3)
        self.music.play(loops=-1)
        #  Lưu trữ âm lượng hiện tại  
        self.music_volume = self.music.get_volume() # Lấy âm lượng ban đầu
        self.sfx_volume = self.sound_shoot.get_volume()  

        # Tạo font chữ
        self.font = py.font.Font(None, 45)
        self.title_font = py.font.Font(None, 55) 
        self.label_font = py.font.Font(None, 40)

        # notification
        self.notification_font = py.font.Font(None, 22)
        self.notification_text = None
        self.notification_start_time = 0
        self.notification_duration = 1500

        # Tạo các dòng chữ
        self.menu_options = ["Continue", "Setting", "Home"]
        self.menu_rects = []
        self.create_pause_menu()

        # Keybindings
        self.keybindings = {
            'skill_1': py.K_q,
            'skill_2': py.K_e,
            'skill_3': py.K_r
        }
        self.load_keybindings() # Tải keybindings đã lưu (nếu có)
        self.rebinding_skill = None # None, 'skill_1', 'skill_2', 'skill_3'

        # Thời gian cooldown cho từng skill
        self.skill_cooldowns = {
            'skill_1': 5000,
            'skill_2': 8000,
            'skill_3': 12000
        }
        # Thời điểm cuối cùng mỗi skill được sử dụng
        self.skill_last_used = {
            'skill_1': 0,
            'skill_2': 0,
            'skill_3': 0
        }

        #setup
        self.load_images()
        self.setup()

        #pause
        self.menu_state = 'none'
        self.enemy_timer_active = True

        # Game Over
        self.game_over = False
        self.start_time = 0
        self.enemies_killed = 0
        self.high_score = 0
        self.new_record = False
        self.load_high_score()
        self.game_over_options = ["Replay", "Exit", "Home"]
        self.game_over_rects = []
        self.create_gameover_menu()
        self.survival_time = 0      

    def load_images(self):
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
                    suft = py.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(suft)
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
        self.btnBig_surf = py.image.load(join('images', 'setting', 'S_button.png')).convert_alpha()
        self.btnSmall_surf = py.image.load(join('images', 'setting', 'button_small.png')).convert_alpha()
        #skill - Chưa dùng đến
        self.skill1_setting = py.image.load(join('images', 'infobar', 'skill1.jpeg')).convert_alpha()
        self.skill2_setting = py.image.load(join('images', 'infobar', 'skill2.jpeg')).convert_alpha()
        self.skill3_setting = py.image.load(join('images', 'infobar', 'skill3.jpeg')).convert_alpha()
        #info bar
        self.info_bar_surf = py.image.load(join('images', 'infobar', 'info_bar.png')).convert_alpha()
        self.btnLevelup_surf = py.image.load(join('images', 'infobar', 'button_levelup.png')).convert_alpha()
        #level up
        self.levelup_surf = py.image.load(join('images', 'infobar', 'button_levelup.png')).convert_alpha()

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
            if current_time - self.shoot_time >= self.bow_cooldown:
                self.can_shoot = True

    def skill_timer(self):
        if not self.can_skill:
            current_time = py.time.get_ticks()
            if current_time - self.skill_time >= self.skill_cooldown:
                self.can_skill = True      
     
    def setup(self):
        map = load_pygame(join('data', 'maps', 'world.tmx'))
        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)
        
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites)) 
        
        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), py.Surface((obj.width, obj.height)), self.collision_sprites) 

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                # Tạo self.bow trước khi tạo self.player
                self.bow = Bow(None, self.all_sprites) # Truyền None vào vì player chưa được tạo
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites, self.bow, self)
                self.bow.set_player(self.player) #set player cho bow
            else: #Enemy
                self.spam_positions.append((obj.x, obj.y))
        self.start_time = py.time.get_ticks()  #Thời gian bắt đầu game
        self.reset_game()
    
    def reset_game(self):
        self.start_time = py.time.get_ticks()
        self.enemies_killed = 0
        self.game_over = False
        self.new_record = False
        self.survival_time = 0
        self.player.health = self.player.health_bar.max_health
        self.player.is_dead = False
        self.player.bow_killed = False
        self.player.death_time = 0
        self.player.health_bar.delayed_health = self.player.health
        self.player.health_bar.delayed_health_width = self.player.health_bar.current_health_width
        # Xóa tất cả các đối tượng trong game
        for sprite in self.all_sprites:
            sprite.kill()
        for sprite in self.enemy_sprites:
            sprite.kill()
        for sprite in self.bullet_sprites:
            sprite.kill()
        for sprite in self.skill_sprites:
            sprite.kill()
        # Tạo lại các đối tượng cần thiết
        map = load_pygame(join('data', 'maps', 'world.tmx'))
        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)
        
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites)) 
        
        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), py.Surface((obj.width, obj.height)), self.collision_sprites) 

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                # Tạo self.bow trước khi tạo self.player
                self.bow = Bow(None, self.all_sprites) # Truyền None vào vì player chưa được tạo
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites, self.bow, self)
                self.bow.set_player(self.player) #set player cho bow
            else: #Enemy
                self.spam_positions.append((obj.x, obj.y))
        py.mixer.unpause()

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

    def draw_notification(self):
        if self.notification_text:
            current_time = py.time.get_ticks()
            if current_time < self.notification_start_time + self.notification_duration:
                notification_surf = self.notification_font.render(self.notification_text, True, 'white')

                info_bar_x = self.player.info_bar.x
                info_bar_y = self.player.info_bar.y
                info_bar_width = self.player.info_bar.health_frame_surf.get_width()

                notification_rect = notification_surf.get_rect(midbottom=(info_bar_x + info_bar_width / 2 + 56, info_bar_y))

                bg_rect = notification_rect.inflate(10, 5)
                bg_surf = py.Surface(bg_rect.size, py.SRCALPHA)
                bg_surf.fill((0, 0, 0, 150))
                self.display_surface.blit(bg_surf, bg_rect)

                self.display_surface.blit(notification_surf, notification_rect)
            else:
                self.notification_text = None

    def set_menu_state(self, new_state):
        # Chỉ thay đổi trạng thái nếu không phải game over
        if not self.game_over:
            old_state = self.menu_state
            self.menu_state = new_state

            # Xử lý pause/unpause game logic và âm thanh
            is_paused_now = (new_state == 'paused' or new_state == 'settings')
            was_paused_before = (old_state == 'paused' or old_state == 'settings')

            if is_paused_now and not was_paused_before: # Chuyển từ chạy sang pause/settings
                if self.enemy_timer_active:
                    py.time.set_timer(self.enemy_event, 0) # Dừng timer enemy
                    self.enemy_timer_active = False
                py.mixer.pause() # Tạm dừng tất cả âm thanh (bao gồm cả nhạc nền nếu đang chạy)
            elif not is_paused_now and was_paused_before: # Chuyển từ pause/settings sang chạy
                if not self.enemy_timer_active:
                    py.time.set_timer(self.enemy_event, self.enemy_create) # Khởi động lại timer enemy
                    self.enemy_timer_active = True
                py.mixer.unpause() # Tiếp tục tất cả âm thanh

    def create_pause_menu(self):
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
        x_offset = -200
        for option in self.game_over_options:
            text_surface = self.font.render(option, True, 'white')
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH / 2 + x_offset, WINDOW_HEIGHT / 2 + 270))
            self.game_over_rects.append((text_surface, text_rect))
            x_offset += 190

    def draw_gameover_menu(self):
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
            if self.player.is_dead and not self.game_over:
                if current_ticks - self.player.death_time >= self.player.death_duration:
                    self.game_over = True
                    # Tính thời gian sống sót tại thời điểm chết
                    self.survival_time = (self.player.death_time - self.start_time) / 1000
                    self.check_new_record()

            for event in py.event.get():
                if event.type == py.QUIT:
                    self.running = False
                # Chỉ tạo enemy nếu game đang chạy
                if event.type == self.enemy_event and self.menu_state == 'none' and not self.game_over:
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
                            # Nếu đang rebind, ESC đã được xử lý ở trên để hủy rebind
                            # Nếu không rebind, ESC sẽ quay lại menu pause
                            if not self.rebinding_skill:
                                self.set_menu_state('paused')

                if event.type == py.MOUSEBUTTONDOWN:
                    if self.game_over:
                        for index, (text_surface, text_rect) in enumerate(self.game_over_rects):
                            button_rect = py.Rect(0, 0, 133, 56)
                            button_rect.center = text_rect.center
                            if button_rect.collidepoint(event.pos):
                                option = self.game_over_options[index]
                                if option == "Replay":
                                    self.reset_game()
                                    self.set_menu_state('none')
                                elif option == "Exit":
                                    self.running = False
                                elif option == "Home":
                                    print("Chức năng Home chưa được cài đặt")
                                break
                    elif self.menu_state == 'none':
                        if self.btnPause_rect.collidepoint(event.pos):
                            self.set_menu_state('paused')
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
                                    print("Chức năng Home chưa được cài đặt")
                                break
                    elif self.menu_state == 'settings':
                        # Click trong menu settings
                        if self.btnBack_rect.collidepoint(event.pos):
                            self.set_menu_state('paused') # Quay lại menu pause
                         # Xử lý click Music Volume Controls
                        elif self.btnMusicDecrease_rect.collidepoint(event.pos):
                            self.music_volume = max(0.0, self.music_volume - 0.1)
                            self.music.set_volume(self.music_volume)
                        elif self.btnMusicIncrease_rect.collidepoint(event.pos):
                            self.music_volume = min(1.0, self.music_volume + 0.1)
                            self.music.set_volume(self.music_volume)
                        # Xử lý click SFX Volume Controls
                        elif self.btnSfxDecrease_rect.collidepoint(event.pos):
                            self.sfx_volume = max(0.0, self.sfx_volume - 0.1)
                            self.sound_shoot.set_volume(self.sfx_volume)
                            self.impact_sound.set_volume(self.sfx_volume)
                        elif self.btnSfxIncrease_rect.collidepoint(event.pos):
                            self.sfx_volume = min(1.0, self.sfx_volume + 0.1)
                            self.sound_shoot.set_volume(self.sfx_volume)
                            self.impact_sound.set_volume(self.sfx_volume)
                        # Click nút đổi phím (chỉ khi không đang rebind skill khác)
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

            if self.menu_state == 'none' and not self.game_over and not self.player.is_dead:
                # Chỉ nhận input game khi không có menu nào hiển thị VÀ không đang rebind
                if not self.rebinding_skill:
                    self.input() 
                self.survival_time += dt
                self.bow_timer()
                # self.skill_timer()
                self.all_sprites.update(dt)
                self.player_collision()
                self.bullet_collision()
                self.skill_collision()
            elif self.player.is_dead and not self.game_over:
                self.all_sprites.update(dt)
            elif self.menu_state != 'none':
                pass

            # Draw
            self.display_surface.fill("black")
            if not self.game_over:
                self.all_sprites.draw(self.player.rect.center)
                # self.player.draw_health_bar(self.display_surface)
                self.player.draw_info_bar(self.display_surface)
                self.draw_notification()

                if self.menu_state == 'none':
                    # Hiển thị thời gian sống sót
                    minutes = int(self.survival_time // 60)
                    seconds = int(self.survival_time % 60)
                    time_text = self.font.render(f"{minutes:02d}:{seconds:02d}", True, 'white')
                    time_rect = time_text.get_rect(topright=(WINDOW_WIDTH - 10, 10))
                    self.display_surface.blit(time_text, time_rect)
                    # Vẽ nút pause nhỏ
                    self.display_surface.blit(self.btnPause_surf, self.btnPause_rect)
                elif self.menu_state == 'paused':
                    self.draw_pause_menu()
                elif self.menu_state == 'settings':
                    self.draw_settings_menu()
            else:
                self.draw_gameover_menu()

            py.display.update()

if __name__ == "__main__":
    game = Game()
    game.run()
