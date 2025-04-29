from settings import *
from math import atan2, degrees

class Sprite(py.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = py.mask.from_surface(self.image)
        self.ground = True

class CollisionSprite(py.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

class Bow(py.sprite.Sprite):
    def __init__(self, player, groups):
        self.player = player
        self.distance = 50
        self.player_direction = py.Vector2(1, 0)
    
        super().__init__(groups)
        self.bow_suft = py.image.load(join('images', 'weapon', 'bow.png')).convert_alpha()
        self.image = self.bow_suft
        #self.rect = self.image.get_rect(center=self.player.rect.center + self.player_direction * self.distance)
        self.rect = self.image.get_rect()
    
    def set_player(self, player):
        self.player = player
        self.rect = self.image.get_rect(center=self.player.rect.center + self.player_direction * self.distance)
    
    def get_direction(self):
        mouse_pos = py.mouse.get_pos()
        player_pos = py.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        self.player_direction = (mouse_pos - player_pos).normalize()     

    def rotate_bow(self):
        angle = degrees(atan2(self.player_direction.x, self.player_direction.y))
        self.image = py.transform.rotozoom(self.bow_suft, angle, 1)

    def update(self, _):
        self.get_direction()
        self.rotate_bow()
        self.rect.center = self.player.rect.center + self.player_direction * self.distance

class Bullet(py.sprite.Sprite):
    def __init__(self, surf, pos, direction, groups):
        super().__init__(groups)
        self.original_image = surf
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.mask = py.mask.from_surface(self.image)
        self.spam_time = py.time.get_ticks()
        self.lifetime = 1000
        self.direction = direction
        self.speed = 1200
        self.rotate()

    def rotate(self):
        angle = degrees(atan2(self.direction.x, self.direction.y))
        self.image = py.transform.rotozoom(self.original_image, angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt

        if py.time.get_ticks() - self.spam_time >= self.lifetime:
            self.kill()

class Enemy(py.sprite.Sprite):
    def __init__(self, pos, frames, groups, player, collision_sprites):
        super().__init__(groups)
        self.player = player

        self.frames, self.frame_index = frames, 0
        self.image = self.frames[self.frame_index]
        self.mask = py.mask.from_surface(self.image)
        self.animation_speed = 6

        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-20, -40)
        self.collision_sprites = collision_sprites
        self.direction = py.Vector2()
        self.speed = 250

        #timer
        self.death_time = 0
        self.death_duration = 400
    
    def animate(self, dt):
        self.frame_index = self.frame_index + self.animation_speed * dt if self.direction else 0
        self.image = self.frames[int(self.frame_index) % len(self.frames)]
    
    def move(self, dt):
        player_pos = py.Vector2(self.player.rect.center)
        enemy_pos = py.Vector2(self.rect.center)
        self.direction = (player_pos - enemy_pos).normalize() if player_pos != enemy_pos else self.direction
        
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
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
                else:  # direction == 'vertical'
                    if self.direction.y > 0:  # Đi xuống
                        self.hitbox_rect.bottom = sprite.rect.top
                    if self.direction.y < 0:  # Đi lên
                        self.hitbox_rect.top = sprite.rect.bottom

    def destroy(self):
        if self.death_time == 0:  # Chỉ phá hủy 1 lần
            self.death_time = py.time.get_ticks()
            self.player.health_bar.update_exp(20)

            surf = py.mask.from_surface(self.frames[0]).to_surface()
            surf.set_colorkey('black')
            self.image = surf
            self.hitbox_rect = py.Rect(0, 0, 0, 0)
            self.collision_sprites.remove(self)


    def death_timer(self):
        if py.time.get_ticks() - self.death_time >= self.death_duration:
            self.kill()

    def update(self, dt):
        if self.death_time == 0:
            self.move(dt)
            self.animate(dt)
        else:
            self.death_timer()
            if self.hitbox_rect.width != 0:
                self.hitbox_rect = py.Rect(0,0,0,0)
                self.collision_sprites.remove(self)

class Skill(py.sprite.Sprite):
    def __init__(self, surf, pos, direction, groups):
        super().__init__(groups)
        self.original_image = surf
        self.direction = direction.normalize()
        self.image = self.original_image
        self.rect = self.image.get_rect(center=pos)

        self.mask = py.mask.from_surface(self.image)  # Tạo mask từ hình ảnh
        self.spam_time = py.time.get_ticks()
        self.lifetime = 1000

        self.rotate()

    def rotate(self):
        angle = degrees(atan2(self.direction.x, self.direction.y)) - 90
        self.image = py.transform.rotozoom(self.original_image, angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = py.mask.from_surface(self.image)

    def update(self, dt):
        # Kiểm tra xem skill đã hết thời gian sống chưa
        if py.time.get_ticks() - self.spam_time >= self.lifetime:
            self.kill()
