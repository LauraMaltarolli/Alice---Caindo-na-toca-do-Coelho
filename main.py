import pygame
import random
import os
import math

# --- Constantes do Jogo ---
GAME_TITLE = "Alice no Túnel das Maravilhas"
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FPS = 60

# Arquivo para salvar a pontuação máxima
HIGH_SCORE_FILE = "highscore.txt"

# Cores
FASE_1_COLOR = (20, 0, 40)
FASE_1_COLOR_END = (40, 0, 70)

FASE_2_COLOR = (0, 10, 40)
FASE_2_COLOR_END = (0, 40, 90)

FASE_3_COLOR = (60, 0, 40)
FASE_3_COLOR_END = (120, 20, 80)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (180, 180, 180)
DIM_GRAY = (80, 80, 80)

RED = (211, 47, 47)   # Obstáculo real
BLUE = (33, 150, 243) # Obstáculo falso

PLAYER_COLOR_NORMAL = (173, 216, 230)
PLAYER_COLOR_SHRINK = (100, 200, 100)
PLAYER_COLOR_GROW = (255, 100, 100)

GREEN = (76, 175, 80)   # Beba-me
PURPLE = (156, 39, 176) # Coma-me
YELLOW = (255, 255, 0)

PLAYER_START_Y = SCREEN_HEIGHT * 0.25


# -------------------------------------------------------
#   Classe de Partículas
# -------------------------------------------------------
class Particle(pygame.sprite.Sprite):
    """Cria uma explosão de partículas 100% procedural."""

    def __init__(self, center, color, min_speed=1, max_speed=5, size=5, num_particles=10):
        super().__init__()
        self.particles = []

        for _ in range(num_particles):
            self.particles.append({
                'pos': list(center),
                'speed': [
                    random.uniform(-max_speed, max_speed),
                    random.uniform(-max_speed, max_speed)
                ],
                'color': color,
                'radius': random.randint(min_speed, size)
            })

    def update(self):
        for p in self.particles:
            p['pos'][0] += p['speed'][0]
            p['pos'][1] += p['speed'][1]
            p['radius'] -= 0.1

            if p['radius'] <= 0:
                self.particles.remove(p)

        if not self.particles:
            self.kill()

    def draw(self, surface):
        for p in self.particles:
            if p['radius'] > 0:
                pygame.draw.circle(surface, p['color'], (int(p['pos'][0]), int(p['pos'][1])), int(p['radius']))


# -------------------------------------------------------
#   Jogador (Alice)
# -------------------------------------------------------
class Player(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()

        # Carrega o sprite base
        alice_raw = pygame.image.load("assets/alice.png").convert_alpha()

        # Tamanhos
        self.size_normal = 50
        self.size_small = 30
        self.size_big = 80

        # Redimensiona mantendo proporção
        self.sprite_normal = pygame.transform.smoothscale(alice_raw, self._scale_keep_ratio(alice_raw, self.size_normal))
        self.sprite_small = pygame.transform.smoothscale(alice_raw, self._scale_keep_ratio(alice_raw, self.size_small))
        self.sprite_big = pygame.transform.smoothscale(alice_raw, self._scale_keep_ratio(alice_raw, self.size_big))

        self.image = self.sprite_normal
        self.rect = self.image.get_rect()

        # Posição inicial
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.centery = PLAYER_START_Y

        self.speed = 7
        self.effect = None
        self.effect_timer = 0
        self.effect_duration = 5000
        self.score_multiplier = 1

    # Redimensionamento mantendo proporção
    def _scale_keep_ratio(self, img, target_height):
        width, height = img.get_width(), img.get_height()
        scale_factor = target_height / height
        return int(width * scale_factor), int(height * scale_factor)

    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

        # Limites
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)

        # Timer de efeitos
        if self.effect:
            now = pygame.time.get_ticks()
            if now - self.effect_timer > self.effect_duration:
                self.reset_size()

        self._update_sprite()

    def _update_sprite(self):
        center = self.rect.center

        if self.effect == "shrink":
            self.image = self.sprite_small
        elif self.effect == "grow":
            self.image = self.sprite_big
        else:
            self.image = self.sprite_normal

        self.rect = self.image.get_rect(center=center)

    # Power-ups
    def shrink(self):
        self.effect = "shrink"
        self.effect_timer = pygame.time.get_ticks()
        self.score_multiplier = 1

    def grow(self):
        self.effect = "grow"
        self.effect_timer = pygame.time.get_ticks()
        self.score_multiplier = 2

    def reset_size(self):
        self.effect = None
        self.effect_timer = 0
        self.score_multiplier = 1


# -------------------------------------------------------
#   Objetos do Túnel
# -------------------------------------------------------
class TunnelObject(pygame.sprite.Sprite):

    def __init__(self, obj_type, speed):
        super().__init__()

        self.obj_type = obj_type
        self.speed = speed

        # Tipos
        if obj_type == "danger":
            width = random.randint(40, 100)
            height = random.randint(15, 30)
            img_path = "assets/obstaculo.png"

        elif obj_type == "shrink":
            width = height = 28
            img_path = "assets/beba_me.png"

        elif obj_type == "grow":
            width = height = 32
            img_path = "assets/coma_me.png"

        img = pygame.image.load(img_path).convert_alpha()
        self.image = pygame.transform.smoothscale(img, (width, height))
        self.rect = self.image.get_rect()

        self.rect.x = random.randint(0, SCREEN_WIDTH - width)
        self.rect.y = SCREEN_HEIGHT + random.randint(20, 150)

    def update(self):
        self.rect.y -= self.speed

        if self.rect.bottom < 0:
            self.kill()


# -------------------------------------------------------
#   Fundo (Estrelas / Parallax)
# -------------------------------------------------------
class BackgroundElement(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()

        size = random.randint(1, 4)
        self.image = pygame.Surface((size, size))
        self.image.fill(random.choice([WHITE, LIGHT_GRAY, DIM_GRAY]))

        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH)
        self.rect.y = random.randint(0, SCREEN_HEIGHT)

        self.speed = random.uniform(1, 6)

    def update(self):
        self.rect.y -= self.speed

        if self.rect.bottom < 0:
            self.rect.y = SCREEN_HEIGHT
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.speed = random.uniform(1, 6)


# -------------------------------------------------------
#   Classe Principal do Jogo
# -------------------------------------------------------
class Game:

    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)

        self.clock = pygame.time.Clock()

        self.font_main = pygame.font.Font(pygame.font.match_font("arial"), 48)
        self.font_small = pygame.font.Font(pygame.font.match_font("arial"), 24)
        self.font_tiny = pygame.font.Font(pygame.font.match_font("arial"), 18)

        self.running = True
        self.game_state = "START"  # START, PLAYING, GAME_OVER

        self.score = 0
        self.high_score = 0
        self.game_speed = 0

        self.load_high_score()

        # Eventos
        self.SPAWN_OBJECT_EVENT = pygame.USEREVENT + 1
        self.SCREEN_SHAKE_EVENT = pygame.USEREVENT + 2

        self.shake_duration = 0

    # High score
    def load_high_score(self):
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE, "r") as f:
                    self.high_score = int(f.read())
            except:
                self.high_score = 0
        else:
            self.high_score = 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open(HIGH_SCORE_FILE, "w") as f:
                f.write(str(self.high_score))

    # Fase baseada no score
    def get_current_phase(self):
        if self.score < 2500:
            return 1
        elif self.score < 8000:
            return 2
        return 3

    # Novo jogo
    def new_game(self):
        self.score = 0
        self.game_speed = 4
        self.shake_duration = 0

        self.all_sprites = pygame.sprite.Group()
        self.tunnel_objects = pygame.sprite.Group()
        self.background_elements = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()

        # Cria jogador
        self.player = Player()
        self.all_sprites.add(self.player)

        # Fundo
        for _ in range(100):
            bg = BackgroundElement()
            self.all_sprites.add(bg)
            self.background_elements.add(bg)

        pygame.time.set_timer(self.SPAWN_OBJECT_EVENT, 1200)
        self.game_state = "PLAYING"

    # Loop principal
    def run(self):
        while self.running:
            self.clock.tick(FPS)

            if self.game_state == "START":
                self.show_start_screen()
            elif self.game_state == "PLAYING":
                self.run_game_loop()
            elif self.game_state == "GAME_OVER":
                self.show_game_over_screen()

        pygame.quit()

    # Loop do jogo
    def run_game_loop(self):

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == self.SPAWN_OBJECT_EVENT:
                self.spawn_objects()

            if event.type == self.SCREEN_SHAKE_EVENT:
                self.shake_duration = 0

        # Update
        self.all_sprites.update()
        self.particles.update()

        # Velocidade aumenta
        self.game_speed += 0.001

        # Score aumenta
        self.score += int(1 * self.player.score_multiplier * (self.game_speed / 4))

        # Colisões
        self.check_collisions()

        # Draw
        self.draw_game()

    # Spawns por fase
    def spawn_objects(self):

        fase = self.get_current_phase()

        if fase == 1:
            spawn_interval = random.randint(800, 1000)
            chance_obst = 0.60
            chance_shr = 0.30
            chance_gro = 0.10

        elif fase == 2:
            spawn_interval = random.randint(450, 700)
            chance_obst = 0.75
            chance_shr = 0.20
            chance_gro = 0.05

        else:
            spawn_interval = random.randint(200, 450)
            chance_obst = 0.90
            chance_shr = 0.08
            chance_gro = 0.02

        total = chance_obst + chance_shr + chance_gro
        chance_obst /= total
        chance_shr /= total
        chance_gro /= total

        r = random.random()

        if r < chance_obst:
            obj_type = "danger"
        elif r < chance_obst + chance_shr:
            obj_type = "shrink"
        else:
            obj_type = "grow"

        new_obj = TunnelObject(obj_type, self.game_speed)
        self.all_sprites.add(new_obj)
        self.tunnel_objects.add(new_obj)

        pygame.time.set_timer(self.SPAWN_OBJECT_EVENT, spawn_interval)

    # Colisões
    def check_collisions(self):

        hits = pygame.sprite.spritecollide(self.player, self.tunnel_objects, False)

        for hit in hits:

            if hit.obj_type == "danger":
                self.particles.add(Particle(self.player.rect.center, RED, size=8, num_particles=30))
                self.shake_screen(300)
                self.game_state = "GAME_OVER"
                self.save_high_score()

            elif hit.obj_type == "shrink":
                self.player.shrink()
                self.particles.add(Particle(hit.rect.center, GREEN, size=6, num_particles=15))
                hit.kill()

            elif hit.obj_type == "grow":
                self.player.grow()
                self.particles.add(Particle(hit.rect.center, PURPLE, size=6, num_particles=15))
                hit.kill()

    # Desenho do jogo
    def draw_game(self):
        self.screen.fill(self.get_background_color())

        self.background_elements.draw(self.screen)
        self.tunnel_objects.draw(self.screen)
        self.all_sprites.draw(self.screen)

        for p in self.particles:
            p.draw(self.screen)

        # HUD
        self.draw_text(f"Score: {self.score}", self.font_small, WHITE, SCREEN_WIDTH / 2, 10)
        self.draw_text(f"High Score: {self.high_score}", self.font_tiny, LIGHT_GRAY, SCREEN_WIDTH / 2, 40)
        self.draw_text(f"Fase: {self.get_current_phase()}", self.font_small, YELLOW, SCREEN_WIDTH / 2, 90)

        # Power-up ativo
        if self.player.effect:
            remaining = int((self.player.effect_duration - (pygame.time.get_ticks() - self.player.effect_timer)) / 1000) + 1
            color = PLAYER_COLOR_GROW if self.player.effect == "grow" else PLAYER_COLOR_SHRINK
            self.draw_text(f"Efeito: {self.player.effect.upper()} ({remaining}s)", self.font_tiny, color, SCREEN_WIDTH / 2, 65)

        # Shake
        offset_x = offset_y = 0

        if self.shake_duration > 0:
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            self.shake_duration -= self.clock.get_time()

        final_surface = self.screen.copy()

        self.screen.fill(BLACK)
        self.screen.blit(final_surface, (offset_x, offset_y))

        pygame.display.flip()

    # Tela inicial
    def show_start_screen(self):

        elements = pygame.sprite.Group()
        for _ in range(70):
            elements.add(BackgroundElement())

        waiting = True

        while waiting:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                if event.type == pygame.KEYUP:
                    waiting = False

            elements.update()

            self.screen.fill(BLACK)
            elements.draw(self.screen)

            self.draw_text(GAME_TITLE, self.font_main, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
            self.draw_text("Caindo na Toca do Coelho", self.font_small, PLAYER_COLOR_NORMAL, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4 + 60)
            self.draw_text("Desvie do VERMELHO. Atravesse o AZUL.", self.font_small, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 30)
            self.draw_text("Pegue VERDE para encolher, ROXO para crescer (x2 score!)",
                           self.font_tiny, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 10)
            self.draw_text("Use <- e -> para mover a Alice", self.font_small, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.7)

            if int(pygame.time.get_ticks() / 500) % 2 == 0:
                self.draw_text("Pressione qualquer tecla para começar", self.font_small, YELLOW, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.85)

            pygame.display.flip()

        self.new_game()

    # Tela de game over
    def show_game_over_screen(self):
        self.screen.fill(BLACK)

        self.draw_text("GAME OVER", self.font_main, RED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)

        if self.score > self.high_score:
            self.draw_text("NOVO RECORDE!", self.font_small, GREEN, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40)

        self.draw_text(f"Score Final: {self.score}", self.font_small, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.draw_text(f"Seu Melhor: {self.high_score}", self.font_tiny, LIGHT_GRAY, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)
        self.draw_text("Pressione 'R' para tentar novamente", self.font_small, YELLOW, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.8)

        pygame.display.flip()

        waiting = True
        while waiting:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                if event.type == pygame.KEYUP and event.key == pygame.K_r:
                    waiting = False

        self.new_game()

    # Gradiente de fundo
    def lerp_color(self, c1, c2, t):
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t)
        )

    def get_background_color(self):
        s = self.score

        if s < 2500:
            return self.lerp_color(FASE_1_COLOR, FASE_1_COLOR_END, s / 2500)

        if s < 8000:
            return self.lerp_color(FASE_2_COLOR, FASE_2_COLOR_END, (s - 2500) / 5500)

        return self.lerp_color(FASE_3_COLOR, FASE_3_COLOR_END, min((s - 8000) / 3000, 1))

    # Texto
    def draw_text(self, text, font, color, x, y):
        surface = font.render(text, True, color)
        rect = surface.get_rect(midtop=(x, y))
        self.screen.blit(surface, rect)

    # Shake
    def shake_screen(self, duration):
        self.shake_duration = duration
        pygame.time.set_timer(self.SCREEN_SHAKE_EVENT, duration, 1)


# -------------------------------------------------------
#   Inicialização
# -------------------------------------------------------
if __name__ == "__main__":
    game = Game()
    game.run()
