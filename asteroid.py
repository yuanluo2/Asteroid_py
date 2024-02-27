"""
    A big thanks to youtuber GrandmaCan's awesome video: https://www.youtube.com/watch?v=61eX0bFAsYs 
    I learned from it and write this project.
"""
import pygame   # version: 2.1.2
import random
import os

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 600
SCREEN_TITLE = 'Asteroid'

GAME_FPS = 60

HEALTH_BAR_WIDTH = 100
HEALTH_BAR_HEIGHT = 10

PLAYER_INIT_LIFE = 100
PLAYER_INIT_LIFE_NUM = 3
PLAYER_INIT_SPEED = 8

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_BLUE = (0, 0, 255)

# init.
pygame.init()
pygame.mixer.init()

# game screen.
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(SCREEN_TITLE)

# clock, used to control the frame.
game_clock = pygame.time.Clock()

# score.
game_score = 0

# is running ?
game_running = True

# show welcome page ?
show_welcome = True

# font, this supports Chinese.
font_name = os.path.join('simfang.ttf')

# sprite groups.
resource_sprites = pygame.sprite.Group()
bullet_sprites = pygame.sprite.Group()
stone_sprites = pygame.sprite.Group()
prop_sprites = pygame.sprite.Group()


def get_image(path):
    """
    get the imageture resource by the given path.
    set_colorkey() is used to make the black area transparent.
    """
    image = pygame.image.load(path).convert()
    image.set_colorkey(COLOR_BLACK)
    return image


# background imageture.
background_image = get_image(os.path.join('img', 'background.png'))

# player ship imageture
player_image = get_image(os.path.join('img', 'player.png'))

# mini player ship imageture, shown as left lives.
player_mini_image = pygame.transform.scale(player_image, (25, 19))
player_mini_image.set_colorkey(COLOR_BLACK)

# set game icon.
pygame.display.set_icon(player_mini_image)

# bullet imageture.
bullet_image = get_image(os.path.join('img', 'bullet.png'))

# stone imageture.
stone_images = [get_image(os.path.join('img', f'rock{i}.png')) for i in range(7)]

# props.
prop_images = {}

prop_images['heal'] = get_image(os.path.join('img', 'shield.png'))
prop_images['multi_bullets'] = get_image(os.path.join('img', 'gun.png'))

# explosion animations.
explosion_animation_large = []    # bullet hits the stone.
explosion_animation_small = []    # stone hits the player.
explosion_animation_player = []   # player's life down to 0.

for i in range(9):
    image = get_image(os.path.join('img', f'expl{i}.png'))

    explosion_animation_large.append(pygame.transform.scale(image, (75, 75)))
    explosion_animation_small.append(pygame.transform.scale(image, (30, 30)))

    player_expl_image = get_image(os.path.join('img', f'player_expl{i}.png'))
    explosion_animation_player.append(player_expl_image)


# background music.
pygame.mixer.music.load(os.path.join('sound', 'background.ogg'))
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1)

# shooting sound.
shoot_sound = pygame.mixer.Sound(os.path.join('sound', 'shoot.wav'))

# heal sound.
heal_sound = pygame.mixer.Sound(os.path.join('sound', 'pow0.wav'))

# multi bullets sound.
multi_bullets_sound = pygame.mixer.Sound(os.path.join('sound', 'pow1.wav'))

# player's life down to 0.
player_exploded_sound = pygame.mixer.Sound(os.path.join('sound', 'rumble.ogg'))

# bullet hits the stone.
stone_exploded_sounds = [pygame.mixer.Sound(os.path.join('sound', f'expl{i}.wav')) for i in range(2)]


class Stone(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.image_original = random.choice(stone_images)
        self.image = self.image_original.copy()

        self.rotate_degree = 0
        self.total_rotate_degree = 0
        self.rect = self.image.get_rect()

        self.rect.x = 0
        self.rect.y = 0

        self.radius = self.rect.width * 0.4

        self.speed_x = 0
        self.speed_y = 0

        self.reset_pos()

    def reset_pos(self):
        self.rotate_degree = random.randrange(-3, 3)
        self.rect.x = random.randrange(0, SCREEN_WIDTH)
        self.rect.y = random.randrange(-200, -80)
        self.speed_x = random.randrange(-3, 3)
        self.speed_y = random.randrange(2, 10)

    def rotate(self):
        original_center = self.rect.center

        self.total_rotate_degree += self.rotate_degree
        self.total_rotate_degree = self.total_rotate_degree % 360
        self.image = pygame.transform.rotate(self.image_original, self.total_rotate_degree)

        self.rect = self.image.get_rect()
        self.rect.center = original_center   # reset center point.

    def update(self):
        self.rotate()

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # out of screen.
        if self.rect.top > SCREEN_HEIGHT \
        or self.rect.left > SCREEN_WIDTH \
        or self.rect.right < 0:
            self.reset_pos()
        

class Bullet(pygame.sprite.Sprite):
    def __init__(self, centerx, y):
        super().__init__()

        self.image = bullet_image
        self.rect = self.image.get_rect()
        self.rect.centerx = centerx
        self.rect.y = y

        self.speed = -10

    def update(self):
        self.rect.y += self.speed

        if self.rect.bottom < 0:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, animation_list):
        super().__init__()

        self.animation_list = animation_list
        
        self.image = self.animation_list[0]
        self.rect = self.image.get_rect()
        self.rect.center = center

        self.frame = 0
        self.frame_rate = 50
        self.last_update_time = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()

        if now - self.last_update_time > self.frame_rate:
            self.last_update_time = now
            self.frame += 1

            if self.frame == len(self.animation_list):
                self.kill()
            else:
                original_center = self.rect.center

                self.image = self.animation_list[self.frame]

                self.rect = self.image.get_rect()
                self.rect.center = original_center   # reset center point.


class Prop(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()

        self.type = random.choice([
            'heal',
            'multi_bullets'
        ])

        self.image = prop_images[self.type]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speed = 3

    def update(self):
        self.rect.y += self.speed

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.image = pygame.transform.scale(player_image, (50, 38))
        self.radius = 20

        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH / 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        
        self.speed = PLAYER_INIT_SPEED
        self.life = PLAYER_INIT_LIFE
        self.life_num = PLAYER_INIT_LIFE_NUM
        
        self.is_hidden = False
        self.hide_time = 0

        self.bullet_level = 1
        self.bullet_update_time = 0

    def update(self):
        now = pygame.time.get_ticks()

        if self.bullet_level > 1 and now - self.bullet_update_time > 5000:
            self.bullet_level = 1

        if self.is_hidden and now - self.hide_time > 1000:
            self.is_hidden = False
            self.rect.centerx = SCREEN_WIDTH / 2
            self.rect.bottom = SCREEN_HEIGHT - 10
            self.life = PLAYER_INIT_LIFE

        key_pressed = pygame.key.get_pressed()

        if key_pressed[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if key_pressed[pygame.K_RIGHT]:
            self.rect.x += self.speed

        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

    def shoot(self):
        if not self.is_hidden:
            if self.bullet_level == 1:
                bullet = Bullet(self.rect.centerx, self.rect.top)
                resource_sprites.add(bullet)
                bullet_sprites.add(bullet)
                shoot_sound.play()
            elif self.bullet_level == 2:
                bullet_1 = Bullet(self.rect.left, self.rect.top)
                bullet_2 = Bullet(self.rect.right, self.rect.top)

                resource_sprites.add(bullet_1)
                resource_sprites.add(bullet_2)

                bullet_sprites.add(bullet_1)
                bullet_sprites.add(bullet_2)
                
                shoot_sound.play()
            else:
                bullet_1 = Bullet(self.rect.left, self.rect.top)
                bullet_2 = Bullet(self.rect.centerx, self.rect.top)
                bullet_3 = Bullet(self.rect.right, self.rect.top)

                resource_sprites.add(bullet_1)
                resource_sprites.add(bullet_2)
                resource_sprites.add(bullet_3)

                bullet_sprites.add(bullet_1)
                bullet_sprites.add(bullet_2)
                bullet_sprites.add(bullet_3)
                
                shoot_sound.play()

    def short_time_hide(self):
        self.is_hidden = True
        self.hide_time = pygame.time.get_ticks()
        self.rect.center = (SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2)

    def multi_bullets(self):
        self.bullet_level += 1
        self.bullet_update_time = pygame.time.get_ticks()


def draw_text(surface, text, text_size, centerx, top):
    font = pygame.font.Font(font_name, text_size)

    text_surface = font.render(text, True, COLOR_WHITE)
    text_rect = text_surface.get_rect()
    text_rect.centerx = centerx
    text_rect.top = top
    surface.blit(text_surface, text_rect)


def create_new_stone():
    s = Stone()
    resource_sprites.add(s)
    stone_sprites.add(s)


def draw_health_bar(surface, life, x, y):
    if life < 0:
        life = 0

    fill_width = life / 100 * HEALTH_BAR_WIDTH
    outline_bar = pygame.Rect(x, y, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT)
    inner_bar = pygame.Rect(x, y, fill_width, HEALTH_BAR_HEIGHT)

    pygame.draw.rect(surface, COLOR_GREEN, inner_bar)
    pygame.draw.rect(surface, COLOR_WHITE, outline_bar, 2)


def draw_lives(surface, life_num, image):
    for i in range(life_num):
        img_rect = image.get_rect()
        img_rect.x = SCREEN_WIDTH - 30 - 30 * i
        img_rect.y = 10
        surface.blit(image, img_rect)


def draw_welcome_page():
    global game_running
    global show_welcome

    screen.blit(background_image, (0, 0))
    draw_text(screen, '太 空 大 战', 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 5)
    draw_text(screen, '左右键控制移动, 空格键发射子弹, Esc键暂停', 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 5)
    draw_text(screen, '按下任意键开始游戏', 18, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4)
    pygame.display.update()

    while game_running:
        game_clock.tick(GAME_FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False
                return
            elif event.type == pygame.KEYUP:
                show_welcome = False
                return

def game_pause():
    global game_running

    while game_running:
        game_clock.tick(GAME_FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return


if __name__ == '__main__':
    while game_running:
        if show_welcome:
            draw_welcome_page()

            game_score = 0
            resource_sprites = pygame.sprite.Group()
            bullet_sprites = pygame.sprite.Group()
            stone_sprites = pygame.sprite.Group()
            prop_sprites = pygame.sprite.Group()

            player = Player()

            resource_sprites.add(player)
            for i in range(10):
                create_new_stone()

        game_clock.tick(GAME_FPS)

        # event loop.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.shoot()
                elif event.key == pygame.K_ESCAPE:
                    game_pause()

        # game update.
        resource_sprites.update()

        # check stones and bullets collide.
        hits = pygame.sprite.groupcollide(stone_sprites, bullet_sprites, True, True)
        for hit in hits:
            random.choice(stone_exploded_sounds).play()
            game_score += int(hit.radius)

            if random.random() > 0.95:
                p = Prop(hit.rect.center)
                resource_sprites.add(p)
                prop_sprites.add(p)

            create_new_stone()
            expl = Explosion(hit.rect.center, explosion_animation_large)
            resource_sprites.add(expl)

        # check stones and player collide.
        hits = pygame.sprite.spritecollide(player, stone_sprites, True, pygame.sprite.collide_circle)
        for hit in hits:
            player.life -= hit.radius

            random.choice(stone_exploded_sounds).play()
            create_new_stone()
            expl = Explosion(hit.rect.center, explosion_animation_large)
            resource_sprites.add(expl)

            if player.life <= 0:
                player.life_num -= 1
                player_exploded = Explosion(player.rect.center, explosion_animation_player)
                
                resource_sprites.add(player_exploded)
                player_exploded_sound.play()
                player.short_time_hide()

        # check props and player collide.
        hits = pygame.sprite.spritecollide(player, prop_sprites, True)
        for hit in hits:
            if hit.type == 'heal':
                heal_sound.play()
                player.life += 5

                if player.life > PLAYER_INIT_LIFE:
                    player.life = PLAYER_INIT_LIFE

            elif hit.type == 'multi_bullets':
                multi_bullets_sound.play()
                player.multi_bullets()

        # complete the player exploded animation.
        if player.life_num <= 0 and not player_exploded.alive():
            show_welcome = True

        # render.
        screen.blit(background_image, (0, 0))
        resource_sprites.draw(screen)

        draw_text(screen, str(game_score), 18, SCREEN_WIDTH / 2, 10)
        draw_health_bar(screen, player.life, 5, 10)
        draw_lives(screen, player.life_num, player_mini_image)
        pygame.display.update()

    pygame.quit()
