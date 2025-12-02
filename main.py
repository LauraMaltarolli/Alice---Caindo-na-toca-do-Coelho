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
FASE_3_COLOR_END = (120, 20, 80)     # Fundo escuro para túnel
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (180, 180, 180)
DIM_GRAY = (80, 80, 80) # Cor adicional para profundidade
RED = (211, 47, 47)      # Obstáculo real (Perigo)
BLUE = (33, 150, 243)     # Obstáculo falso (Seguro)
PLAYER_COLOR_NORMAL = (173, 216, 230) # Alice azul claro
PLAYER_COLOR_SHRINK = (100, 200, 100)  # Alice verde ao encolher
PLAYER_COLOR_GROW = (255, 100, 100)    # Alice rosa ao crescer
GREEN = (76, 175, 80)     # Item "Beba-me" (Encolher)
PURPLE = (156, 39, 176)   # Item "Coma-me" (Crescer)
YELLOW = (255, 255, 0)    # Para partículas/destaques

# Posição Y da Alice (primeiro quarto/terço da tela)
PLAYER_START_Y = SCREEN_HEIGHT * 0.25

# --- Classe para Efeitos de Partículas ---
class Particle(pygame.sprite.Sprite):
    """Cria uma explosão de partículas em um ponto. 100% procedural."""
    def __init__(self, center, color, min_speed=1, max_speed=5, size=5, num_particles=10):
        super().__init__()
        self.particles = []
        for _ in range(num_particles):
            self.particles.append({
                'pos': list(center),
                'speed': [random.uniform(-max_speed, max_speed), random.uniform(-max_speed, max_speed)],
                'color': color,
                'radius': random.randint(min_speed, size)
            })

    def update(self):
        for p in self.particles:
            p['pos'][0] += p['speed'][0]
            p['pos'][1] += p['speed'][1]
            p['radius'] -= 0.1 # Partículas encolhem e desaparecem
            if p['radius'] <= 0:
                self.particles.remove(p)
        if not self.particles:
            self.kill() # Remove o sprite de partículas quando todas sumirem

    def draw(self, surface):
        for p in self.particles:
            if p['radius'] > 0:
                pygame.draw.circle(surface, p['color'], (int(p['pos'][0]), int(p['pos'][1])), int(p['radius']))

# --- Classe do Jogador ("Alice") ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # Carrega sprites originais
        alice_raw = pygame.image.load("assets/alice.png").convert_alpha()

        # ===== TAMANHOS =====
        self.size_normal = 50
        self.size_small = 30
        self.size_big = 80

        # ===== REDIMENSIONAMENTO =====
        self.sprite_normal = pygame.transform.smoothscale(
            alice_raw,
            self._scale_keep_ratio(alice_raw, self.size_normal)
        )
        self.sprite_small = pygame.transform.smoothscale(
            alice_raw,
            self._scale_keep_ratio(alice_raw, self.size_small)
        )
        self.sprite_big = pygame.transform.smoothscale(
            alice_raw,
            self._scale_keep_ratio(alice_raw, self.size_big)
        )

        # Começa com o sprite normal
        self.image = self.sprite_normal
        self.rect = self.image.get_rect()

        # Posição inicial
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.centery = PLAYER_START_Y

        # Movimento
        self.speed = 7

        # Efeitos
        self.effect = None
        self.effect_timer = 0
        self.effect_duration = 5000
        self.score_multiplier = 1

    # =============== MANUTENÇÃO DO ASPECT RATIO ===============
    def _scale_keep_ratio(self, img, target_height):
        """Redimensiona mantendo proporção original."""
        width = img.get_width()
        height = img.get_height()

        scale_factor = target_height / height
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

        return (new_width, new_height)

    # ========================== ATUALIZAÇÃO ==========================
    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

        # Limites da tela
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)

        # Timer de efeitos
        if self.effect:
            now = pygame.time.get_ticks()
            if now - self.effect_timer > self.effect_duration:
                self.reset_size()

        # Atualiza sprite visual
        self._update_sprite()

    # ========================== TROCA DE SPRITES ==========================
    def _update_sprite(self):
        center = self.rect.center

        if self.effect == "shrink":
            self.image = self.sprite_small
        elif self.effect == "grow":
            self.image = self.sprite_big
        else:
            self.image = self.sprite_normal

        self.rect = self.image.get_rect(center=center)

    # ========================== POWER UPS ==========================
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

# --- Classe dos Obstáculos e Itens ---
class TunnelObject(pygame.sprite.Sprite):
    def __init__(self, obj_type, speed):
        super().__init__()
        self.obj_type = obj_type
        self.speed = speed
        
        # ========= DEFINIÇÕES DOS TAMANHOS PROPORCIONAIS ========= #
        if self.obj_type == 'danger':
            width = random.randint(40, 100)
            height = random.randint(15, 30)
            image_path = "assets/obstaculo.png"

        elif self.obj_type == 'shrink':
            width = height = 28
            image_path = "assets/beba_me.png"  # diminui Alice

        elif self.obj_type == 'grow':
            width = height = 32
            image_path = "assets/coma_me.png"  # aumenta Alice

        # ========= CARREGAR A IMAGEM ========= #
        original_img = pygame.image.load(image_path).convert_alpha()

        # ========= ESCALAR A IMAGEM PARA O TAMANHO DEFINIDO ========= #
        self.image = pygame.transform.smoothscale(original_img, (width, height))

        # ========= DEFINIR RECT ========= #
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - width)
        self.rect.y = SCREEN_HEIGHT + random.randint(20, 150)

    def update(self):
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()

# --- Classe dos Elementos de Fundo (Parallax Starfield) ---
class BackgroundElement(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        # Partícula/Estrela simples
        size = random.randint(1, 4)
        self.image = pygame.Surface((size, size))
        # Cores variadas para ilusão de profundidade
        self.image.fill(random.choice([WHITE, LIGHT_GRAY, DIM_GRAY])) 
        self.rect = self.image.get_rect()
            
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(0, SCREEN_HEIGHT)
        
        self.speed = random.uniform(1, 6) # Velocidades variadas para parallax

    def update(self):
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.rect.y = SCREEN_HEIGHT + random.randint(0, 50)
            self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
            self.speed = random.uniform(1, 6) # Reinicia velocidade

# --- Classe Principal do Jogo ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.font_main = pygame.font.Font(pygame.font.match_font('arial'), 48)
        self.font_small = pygame.font.Font(pygame.font.match_font('arial'), 24)
        self.font_tiny = pygame.font.Font(pygame.font.match_font('arial'), 18)
        
        self.running = True
        self.game_state = 'START' # Estados: START, PLAYING, GAME_OVER
        
        self.score = 0
        self.high_score = 0
        self.game_speed = 0 # Velocidade inicial para objetos caindo
        self.load_high_score()
        
        # Eventos customizados
        self.SPAWN_OBJECT_EVENT = pygame.USEREVENT + 1
        self.SCREEN_SHAKE_EVENT = pygame.USEREVENT + 2
        self.shake_duration = 0
        
    def load_high_score(self):
        """Carrega o high score do arquivo."""
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE, 'r') as f:
                    self.high_score = int(f.read())
            except ValueError:
                self.high_score = 0
        else:
            self.high_score = 0

    def save_high_score(self):
        """Salva o high score se for maior que o anterior."""
        if self.score > self.high_score:
            self.high_score = self.score
            with open(HIGH_SCORE_FILE, 'w') as f:
                f.write(str(self.high_score))

    def get_current_phase(self):
        s = self.score
        if s < 2500:
            return 1
        elif s < 8000:
            return 2
        else:
            return 3

    def new_game(self):
        """Reseta tudo para um novo jogo."""
        self.score = 0
        self.game_speed = 4 # Velocidade inicial dos objetos
        self.shake_duration = 0
        
        # Limpa todos os grupos
        self.all_sprites = pygame.sprite.Group()
        self.tunnel_objects = pygame.sprite.Group() # Obstáculos e itens
        self.background_elements = pygame.sprite.Group() # Estrelas e objetos de Alice
        self.particles = pygame.sprite.Group() # Efeitos de partículas

        # Cria o jogador
        self.player = Player()
        self.all_sprites.add(self.player)
        
        # Cria elementos de fundo
        for _ in range(100): # Mais elementos para um túnel denso
            bg_elem = BackgroundElement()
            self.all_sprites.add(bg_elem)
            self.background_elements.add(bg_elem)
            
        # Inicia o timer de spawn de objetos
        pygame.time.set_timer(self.SPAWN_OBJECT_EVENT, 1200) # Primeiro spawn em 1.2 seg
        
        self.game_state = 'PLAYING'

    def run(self):
        """Loop principal que gerencia os estados do jogo."""
        while self.running:
            self.clock.tick(FPS)
            
            if self.game_state == 'START':
                self.show_start_screen()
            elif self.game_state == 'PLAYING':
                self.run_game_loop()
            elif self.game_state == 'GAME_OVER':
                self.show_game_over_screen()
        
        pygame.quit()

    def run_game_loop(self):
        """O loop do jogo em si (quando está jogando)."""
        # --- Eventos ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == self.SPAWN_OBJECT_EVENT:

                fase = self.get_current_phase()

                # ===============================
                # CONFIGURAÇÃO POR FASE
                # ===============================

                if fase == 1:
                    spawn_interval = random.randint(800, 1000)
                    chance_obstaculo = 0.60
                    chance_shrink = 0.30
                    chance_grow = 0.10

                elif fase == 2:
                    spawn_interval = random.randint(450, 700)
                    chance_obstaculo = 0.75
                    chance_shrink = 0.20
                    chance_grow = 0.05

                else:  # FASE 3
                    spawn_interval = random.randint(200, 450)
                    chance_obstaculo = 0.90
                    chance_shrink = 0.08
                    chance_grow = 0.02

                # NORMALIZA
                total = chance_obstaculo + chance_shrink + chance_grow
                chance_obstaculo /= total
                chance_shrink /= total
                chance_grow /= total

                # ===============================
                # SORTEIA O OBJETO
                # ===============================
                r = random.random()

                if r < chance_obstaculo:
                    obj_type = 'danger'
                elif r < chance_obstaculo + chance_shrink:
                    obj_type = 'shrink'
                else:
                    obj_type = 'grow'

                # CRIA
                new_obj = TunnelObject(obj_type, self.game_speed)
                self.all_sprites.add(new_obj)
                self.tunnel_objects.add(new_obj)

                # REAGENDA
                pygame.time.set_timer(self.SPAWN_OBJECT_EVENT, spawn_interval)

            
            if event.type == self.SCREEN_SHAKE_EVENT:
                self.shake_duration = 0 # Encerra o shake

        # --- Atualização (Update) ---
        self.all_sprites.update() # Atualiza todos os sprites
        self.particles.update() # Atualiza apenas as partículas
        
        # Aumenta a velocidade do jogo gradualmente
        self.game_speed += 0.001
        
        # Aumenta o score com base na velocidade do jogo e multiplicador
        self.score += int(1 * self.player.score_multiplier * (self.game_speed / 4))
            
        # --- Verificação de Colisões ---
        hits = pygame.sprite.spritecollide(self.player, self.tunnel_objects, False)
        for hit in hits:
            if hit.obj_type == 'danger':
                # Game Over!
                self.particles.add(Particle(self.player.rect.center, RED, size=8, num_particles=30))
                self.shake_screen(300) # Tremer a tela por 300ms
                self.game_state = 'GAME_OVER'
                self.save_high_score()
            
            elif hit.obj_type == 'shrink':
                self.player.shrink()
                self.particles.add(Particle(hit.rect.center, GREEN, min_speed=1, max_speed=4, size=6, num_particles=15))
                hit.kill()
            
            elif hit.obj_type == 'grow':
                self.player.grow()
                self.particles.add(Particle(hit.rect.center, PURPLE, min_speed=1, max_speed=4, size=6, num_particles=15))
                hit.kill()

        # --- Desenho (Render) ---
        self.screen.fill(self.get_background_color())
        
        # Desenha em camadas: fundo, objetos, jogador, partículas
        self.background_elements.draw(self.screen)
        self.tunnel_objects.draw(self.screen)
        self.all_sprites.draw(self.screen) # O player está aqui
        for p in self.particles:
            p.draw(self.screen) # Desenha partículas por cima
        
        # Desenha HUD
        self.draw_text(f"Score: {self.score}", self.font_small, WHITE, SCREEN_WIDTH / 2, 10)
        self.draw_text(f"High Score: {self.high_score}", self.font_tiny, LIGHT_GRAY, SCREEN_WIDTH / 2, 40)
        self.draw_text(f"Fase: {self.get_current_phase()}", self.font_small, YELLOW, SCREEN_WIDTH / 2, 90)

        if self.player.effect:
            powerup_text = f"Efeito: {self.player.effect.upper()} ({int((self.player.effect_duration - (pygame.time.get_ticks() - self.player.effect_timer)) / 1000) + 1}s)"
            color = PLAYER_COLOR_GROW if self.player.effect == 'grow' else PLAYER_COLOR_SHRINK
            self.draw_text(powerup_text, self.font_tiny, color, SCREEN_WIDTH / 2, 65)

        # Aplica o shake na tela
        offset_x, offset_y = 0, 0
        if self.shake_duration > 0:
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            self.shake_duration -= self.clock.get_time()
        
        final_surface = self.screen.copy() # Copia o que foi desenhado
        self.screen.fill(BLACK) # Limpa a tela real
        self.screen.blit(final_surface, (offset_x, offset_y)) # Desenha com offset

        pygame.display.flip()
        

    def show_start_screen(self):
        """Mostra a tela de início."""
        # Animação básica na tela de início (estrelas de fundo)
        start_elements = pygame.sprite.Group()
        for _ in range(70):
            start_elements.add(BackgroundElement())
            
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                if event.type == pygame.KEYUP:
                    waiting = False
            
            start_elements.update()
            
            self.screen.fill(BLACK)
            start_elements.draw(self.screen)
            
            self.draw_text(GAME_TITLE, self.font_main, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
            self.draw_text("Caindo na Toca do Coelho", self.font_small, PLAYER_COLOR_NORMAL, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4 + 60)
            self.draw_text("Desvie dos obstáculos", self.font_small, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 30)
            self.draw_text("Pegue a poção para encolher e fuja das pizzas", self.font_tiny, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 10)
            self.draw_text("Use as Setas <- e -> para mover a Alice", self.font_small, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.7)
            
            # Efeito de piscar no texto
            if int(pygame.time.get_ticks() / 500) % 2 == 0:
                self.draw_text("Pressione qualquer tecla para começar", self.font_small, YELLOW, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.85)
            
            pygame.display.flip()
        
        self.new_game() # Começa o jogo

    def show_game_over_screen(self):
        """Mostra a tela de Game Over."""
        self.screen.fill(BLACK)
        self.draw_text("GAME OVER", self.font_main, RED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
        
        if self.score > self.high_score: # Mensagem de novo recorde
             self.draw_text("NOVO RECORDE!", self.font_small, GREEN, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40)
             self.draw_text(f"Score Final: {self.score}", self.font_small, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        else:
            self.draw_text(f"Score Final: {self.score}", self.font_small, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
            self.draw_text(f"Seu Melhor: {self.high_score}", self.font_tiny, LIGHT_GRAY, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)
            
        self.draw_text("Pressione 'R' para reiniciar  |  'M' para menu", self.font_small, YELLOW, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.8)
        pygame.display.flip()
        
        # Espera o jogador pressionar 'R'
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_r:
                        waiting = False
                        self.new_game()
                    if event.key == pygame.K_m:
                        waiting = False
                        self.game_state = 'START'

    def lerp_color(self, color1, color2, t):
        """Interpolação linear de cor (t = 0 → cor1, t = 1 → cor2)."""
        return (
            int(color1[0] + (color2[0] - color1[0]) * t),
            int(color1[1] + (color2[1] - color1[1]) * t),
            int(color1[2] + (color2[2] - color1[2]) * t)
        )

    def get_background_color(self):
        """Retorna a cor de fundo conforme a fase."""
        s = self.score

        # ----- FASE 1 -----
        if s < 2500:
            t = s / 2500
            return self.lerp_color(FASE_1_COLOR, FASE_1_COLOR_END, t)

        # ----- FASE 2 -----
        if s < 8000:
            t = (s - 2500) / (8000 - 2500)
            return self.lerp_color(FASE_2_COLOR, FASE_2_COLOR_END, t)

        # ----- FASE 3 -----
        t = min((s - 8000) / 3000, 1)
        return self.lerp_color(FASE_3_COLOR, FASE_3_COLOR_END, t)

    def draw_text(self, text, font, color, x, y):
        """Função helper para desenhar texto na tela."""
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)

    def shake_screen(self, duration):
        """Ativa o efeito de tremor na tela."""
        self.shake_duration = duration
        pygame.time.set_timer(self.SCREEN_SHAKE_EVENT, duration, 1) # Dispara uma vez

# --- Bloco de Inicialização ---
if __name__ == "__main__":
    game = Game()
    game.run()