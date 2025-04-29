from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprite

from random import randint, choice

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
        self.damaged_enemies = []

        #sound
        self.sound_shoot = py.mixer.Sound(join('audio', 'shoot.wav'))
        self.sound_shoot.set_volume(0.4)
        self.impact_sound = py.mixer.Sound(join('audio', 'impact.ogg'))
        self.music = py.mixer.Sound(join('audio', 'music.wav'))
        self.music.set_volume(0.3)
        self.music.play(loops=-1)

        #setup
        self.load_images()
        self.setup()

    def load_images(self):
        self.bullet_surf = py.image.load(join('images', 'weapon', 'arrow.png')).convert_alpha()    
        self.skill_surf = py.image.load(join('images', 'skill', '7.png')).convert_alpha()
        
        folders = list(walk(join('images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    suft = py.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(suft)

    def input(self):
        if self.bow and py.mouse.get_pressed()[0] and self.can_shoot:  # Kiểm tra đã vẽ cung tên chưa trước khi bắn
            self.sound_shoot.play()
            pos = self.bow.rect.center + self.bow.player_direction * 50
            Bullet(self.bullet_surf, pos, self.bow.player_direction, (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = py.time.get_ticks()
        #skill
        if self.bow and py.key.get_pressed()[py.K_r] and self.can_skill:
            self.sound_shoot.play()
            pos = self.bow.rect.center + self.bow.player_direction * 555
            Skill(self.skill_surf, pos, self.bow.player_direction, (self.all_sprites, self.skill_sprites))
            self.can_skill = False
            self.skill_time = py.time.get_ticks()

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
    
    def bullet_collision(self):
        if self.bullet_sprites and self.enemy_sprites:
            for bullet in self.bullet_sprites:
                for enemy in self.enemy_sprites:
                    if enemy.hitbox_rect.colliderect(bullet.rect):
                        self.impact_sound.play()
                        enemy.destroy()
                        bullet.kill()
                        break
    
    def skill_collision(self):
        for skill in self.skill_sprites:
            for enemy in self.enemy_sprites:
                collision_point = py.sprite.collide_mask(skill, enemy)
                if collision_point:
                    # skill.kill()
                    enemy.destroy()
        
    def player_collision(self):
        if py.sprite.spritecollide(self.player, self.enemy_sprites, False, py.sprite.collide_mask):
            current_time = py.time.get_ticks()
            colliding_enemies = py.sprite.spritecollide(self.player, self.enemy_sprites, False, py.sprite.collide_mask)
            damage = 0
            for enemy in colliding_enemies:
                if enemy not in self.damaged_enemies or current_time - self.damaged_enemies[enemy] >= self.player.health_bar.damage_cooldown: # Kiểm tra cooldown cho từng enemy
                    damage += 100
                    self.damaged_enemies[enemy] = current_time # Lưu thời gian gây sát thương cho từng enemy
            self.player.health -= damage
            if self.player.health <= 0:
                self.player.is_dead = True
                self.player.death_time = py.time.get_ticks()
        else:
            self.damaged_enemies = {} 
            
    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000
            # Event loop
            for event in py.event.get():
                if event.type == py.QUIT:
                    self.running = False
                if event.type == self.enemy_event:
                    Enemy(choice(self.spam_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)

            # Update
            self.bow_timer()
            self.skill_timer()
            self.input()
            self.all_sprites.update(dt)
            self.player_collision()
            self.bullet_collision()
            self.skill_collision()

            # Draw
            self.display_surface.fill("black")
            self.all_sprites.draw(self.player.rect.center)
            self.player.draw_health_bar(self.display_surface)  # Vẽ health bar
            
            for skill in self.skill_sprites:
                py.draw.rect(self.display_surface, (255, 0, 0), skill.rect, 2)  # Vẽ hitbox của skill

            for enemy in self.enemy_sprites:
                py.draw.rect(self.display_surface, (0, 255, 0), enemy.rect, 2)  # Vẽ hitbox của enemy

            py.display.update()

if __name__ == "__main__":
    game = Game()
    game.run()
