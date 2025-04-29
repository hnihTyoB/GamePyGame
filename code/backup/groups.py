from settings import *

class AllSprite(py.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = py.display.get_surface()
        self.offset = py.Vector2()
        
    def draw(self, target_pos):
        self.offset.x = - (target_pos[0] - WINDOW_WIDTH / 2)
        self.offset.y = - (target_pos[1] - WINDOW_HEIGHT / 2)

        ground_sprites = [sprite for sprite in self if hasattr(sprite, 'ground')]
        object_sprites = [sprite for sprite in self if not hasattr(sprite, 'ground')]
        for player in [ground_sprites, object_sprites]:
            for sprite in sorted(player, key=lambda sprite: sprite.rect.centery):
                offset_pos = sprite.rect.topleft + self.offset
                self.display_surface.blit(sprite.image, offset_pos)
