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
        self.health_bar = HealthBar(self, game)
    
    def draw_health_bar(self, surface):
        self.health_bar.update_health()
        self.health_bar.draw(surface)

    def load_images(self):
        self.frames = {'left': [], 'right': [], 'up': [], 'down': [], 'die': []} # Thêm 'die' vào đây
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
            self.game.running = False

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
        self.player.health = self.max_health
        self.health_frame_surf = py.image.load(join('images', 'player', 'hp.png')).convert_alpha()
        self.health_width = 119
        self.health_height = 9
        self.x = WINDOW_WIDTH / 2 - self.health_frame_surf.get_width() / 2
        self.y = WINDOW_HEIGHT / 2 - 118
        self.current_health_width = self.health_width
        self.health_ratio = self.player.health / self.max_health
        #Thanh máu phụ
        self.delayed_health = self.player.health
        self.delayed_health_width = self.health_width
        self.delay_speed = 1
        self.create_health_surface()
        self.delayed_health_surf = py.Surface((self.delayed_health_width, self.health_height), py.SRCALPHA) # Tạo surface cho thanh máu cam
        self.delayed_health_surf.fill('orange')
        # EXP Bar
        self.max_exp = 100  # EXP cần để lên cấp 2
        self.current_exp = 0
        self.exp_width = 104
        self.exp_height = 4
        self.current_exp_width = 0
        self.exp_surf = py.Surface((self.current_exp_width, self.exp_height), py.SRCALPHA)
        self.exp_surf.fill('#1BD1FF')
        self.level = 1
        self.max_level = 11
        self.font = py.font.Font(None, 26)
        self.damage_cooldown = 1000

    def create_health_surface(self):
        self.health_surf = py.Surface((self.current_health_width, self.health_height), py.SRCALPHA)
        self.health_surf.fill('red')

    def update_health(self):
        self.health_ratio = self.player.health / self.max_health
        self.current_health_width = int(self.health_width * self.health_ratio)
        self.create_health_surface()
        #Cập nhật thanh máu phụ
        if self.delayed_health > self.player.health:
            self.delayed_health -= self.delay_speed
            self.delayed_health_width = int(self.health_width * (self.delayed_health / self.max_health))
            self.delayed_health_surf = py.Surface((self.delayed_health_width, self.health_height), py.SRCALPHA) # Tạo lại surface cho thanh máu cam
            self.delayed_health_surf.fill('orange')
            if self.delayed_health < self.player.health:
                self.delayed_health = self.player.health

    def create_exp_surface(self):
        self.exp_surf = py.Surface((self.current_exp_width, self.exp_height), py.SRCALPHA)
        self.exp_surf.fill('#1BD1FF')

    def update_exp(self, exp_gain=0):
        if self.level < self.max_level:
            self.current_exp += exp_gain
            if self.current_exp >= self.max_exp:
                self.level_up()
            self.current_exp_width = int(self.exp_width * (self.current_exp / self.max_exp))
            self.create_exp_surface()

    def level_up(self):
        if self.level < self.max_level:
            self.level += 1
            self.current_exp = 0
            self.max_exp = int(100 * (1.2)**(self.level - 1))
            self.update_game_difficulty()
            self.update_max_health()

    def update_max_health(self):
        health_ratio = self.player.health / self.max_health #tính tỉ lệ máu hiện tại
        self.max_health = int(1000 * (1.1)**(self.level - 1))
        self.player.health = int(self.max_health * health_ratio) #cập nhật lại máu theo tỉ lệ
        self.delayed_health = self.player.health
    
    def update_game_difficulty(self):
        self.game.enemy_create = int(1500 * (0.95)**(self.level - 1))
        self.game.bow_cooldown = int(1000 * (0.95)**(self.level - 1))
        py.time.set_timer(self.game.enemy_event, self.game.enemy_create)

        self.player.speed = int(300 * (1.05)**(self.level - 1))
        for enemy in self.game.enemy_sprites:
            enemy.speed = int(250 * (1.06)**(self.level - 1))
        self.damage_cooldown = int(1000 * (0.95)**(self.level - 1))

    def draw(self, surface):
        surface.blit(self.health_frame_surf, (self.x, self.y))
        # Vẽ thanh máu cam
        delayed_health_rect = py.Rect(self.x + 38, self.y + 7, self.delayed_health_width, self.health_height)
        surface.blit(self.delayed_health_surf, delayed_health_rect)
        # Vẽ thanh máu đỏ
        health_rect = py.Rect(self.x + 38, self.y + 7, self.current_health_width, self.health_height)
        surface.blit(self.health_surf, health_rect)
        # Vẽ EXP Bar
        exp_rect = py.Rect(self.x + 38, self.y + 7 + self.health_height + 9, self.current_exp_width, self.exp_height)
        surface.blit(self.exp_surf, exp_rect)
        # Vẽ Level
        level_text = self.font.render(f"{self.level}", True, 'white')
        level_rect = level_text.get_rect(center=(self.x + 17, self.y + 18)) # Căn giữa
        surface.blit(level_text, level_rect)