import pygame
from pygame.locals import *
import math
import random

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Elemental Magic Defense")

corridor_img = pygame.image.load('counterspell/corridor.png').convert()

aspect_ratio = corridor_img.get_height() / corridor_img.get_width()
corridor_img = pygame.transform.scale(corridor_img, (WIDTH, int(WIDTH * aspect_ratio)))

def load_high_score():
    try:
        with open('counterspell/highscore.txt', 'r') as file:
            return int(file.read())
    except FileNotFoundError:
        return 0
    except ValueError:
        return 0

def save_high_score(score):
    with open('counterspell/highscore.txt', 'w') as file:
        file.write(str(score))

high_score = load_high_score()
# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
ORANGE = (255, 140, 0)  # Fire
ICE_BLUE = (135, 206, 235)  # Ice
GREEN = (0, 255, 0)  # Wind     
class Text:
    #everything in this game needs to be comic sans 
    def __init__ (self,pos,text,color,size,font = "Comic Sans MS"):
        self.pos = pos
        self.text = text
        self.color = color
        self.size = size
        self.font = font
    def draw(self):
        screen.blit(pygame.font.SysFont(self.font,self.size).render(self.text,True,self.color),self.pos)
class ScrollingBackground:
    def __init__(self):
        self.img = corridor_img
        self.scroll_speed = 2
        self.img_height = self.img.get_height()
        self.scroll = 0
        
    def update(self):
        self.scroll = (self.scroll + self.scroll_speed) % self.img_height
        
    def draw(self, screen):
        # Draw the first image
        screen.blit(self.img, (0, self.scroll - self.img_height))
        # Draw the second image
        screen.blit(self.img, (0, self.scroll))
        # Draw the third image (to prevent gaps during scrolling)
        screen.blit(self.img, (0, self.scroll + self.img_height))

class SpellType:
    FIRE = "fire"
    ICE = "ice"
    WIND = "wind"

class Enemy:
    enemy_images = []
    
    @classmethod
    def load_images(cls):
        if not cls.enemy_images:  # Only load if not already loaded
            for i in range(1, 9):  # Load images 1 through 8
                
                image = pygame.image.load(f'counterspell/{i}.png').convert_alpha()
                # Scale image to appropriate size (adjust size as needed)
                image = pygame.transform.scale(image, (40, 40))
                cls.enemy_images.append(image)
                
            

    def __init__(self):
        if not Enemy.enemy_images:
            Enemy.load_images()
        self.enemy_type = random.randint(1, 8)
        self.image = random.choice(Enemy.enemy_images)
        self.size = 30
        self.x = random.randint(0, WIDTH - self.size - 100)
        self.y = -self.size
        self.base_speed = random.uniform(0.7, player.score / 200)
        self.speed = self.base_speed
        self.health = 100
        self.color = RED
        self.frozen_timer = 0
        self.burning = False
        self.burn_timer = 0
        self.pushed_by_wind = 0
    def move(self):
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            self.speed = 0
        else:
            self.speed = self.base_speed

        if self.pushed_by_wind > 0:
            self.y -= self.pushed_by_wind
            self.pushed_by_wind = max(0, self.pushed_by_wind - 0.2)
        
        self.y += self.speed

        if self.burning and self.burn_timer % 20 == 0:  # Apply burn damage every 20 frames
            self.health -= 5

        if self.burn_timer > 0:
            self.burn_timer -= 1
            if self.burn_timer <= 0:
                self.burning = False

    def draw(self):
        
        screen.blit(self.image, (self.x, self.y))
        
        # Draw status effects
        if self.burning:
            pygame.draw.rect(screen, ORANGE, (self.x, self.y - 8, self.size, 3))
        if self.frozen_timer > 0:
            pygame.draw.rect(screen, ICE_BLUE, (self.x, self.y - 5, self.size, 3))
        
        health_bar_length = self.size
        health_bar_height = 3
        health_bar_x = self.x
        health_bar_y = self.y - 12
        health_ratio = self.health / 100
        pygame.draw.rect(screen, (0, 0, 0), 
                        (health_bar_x - 1, health_bar_y - 1, 
                         health_bar_length + 2, health_bar_height + 2))
        # Draw red background
        pygame.draw.rect(screen, RED, 
                        (health_bar_x, health_bar_y, 
                         health_bar_length, health_bar_height))
        # Draw green health
        pygame.draw.rect(screen, (0, 255, 0), 
                        (health_bar_x, health_bar_y, 
                         health_bar_length * health_ratio, health_bar_height))
    def is_hit(self, spell):
        # Calculate center points
        enemy_center_x = self.x + self.size / 2
        enemy_center_y = self.y + self.size / 2
        
        # Calculate distance between centers
        distance = math.sqrt(
            (enemy_center_x - spell.x) ** 2 + 
            (enemy_center_y - spell.y) ** 2
        )
        
        # Check if distance is less than combined radii
        return distance < (self.size / 2 + spell.size / 2)

    def is_off_screen(self):
        return self.y > HEIGHT

class Player:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.speed = 5
        self.size = 30
        self.spells = []
        self.cooldown = 0
        self.max_cooldown = 20
        self.score = 0
        self.health = 100
        self.current_spell = SpellType.FIRE  # Default spell
        self.image = pygame.image.load('counterspell/hero.png').convert_alpha()

        self.size = self.image.get_height()
    def _calculate_triangle_points(self):
        center_x = self.x + self.size / 2
        center_y = self.y + self.size / 2
        return [
            (center_x, self.y),
            (self.x, self.y + self.size),
            (self.x + self.size, self.y + self.size)
        ]

    def draw(self):
        # Draw player
        if self.image:
            # Draw hero image
            screen.blit(self.image, (self.x, self.y))
        health_bar_length = 100
        health_bar_height = 10
        health_bar_x = self.x - 35
        health_bar_y = self.y - 20
        health_ratio = self.health / 100

        pygame.draw.rect(screen, (0, 0, 0), 
                        (health_bar_x - 1, health_bar_y - 1, 
                         health_bar_length + 2, health_bar_height + 2))
        pygame.draw.rect(screen, RED, 
                        (health_bar_x, health_bar_y, 
                         health_bar_length, health_bar_height))
        # Draw green health
        pygame.draw.rect(screen, (0, 255, 0), 
                        (health_bar_x, health_bar_y, 
                         health_bar_length * health_ratio, health_bar_height))
        # Draw current spell type indicator
        spell_colors = {
            SpellType.FIRE: ORANGE,
            SpellType.ICE: ICE_BLUE,
            SpellType.WIND: GREEN
        }
        pygame.draw.circle(screen, spell_colors[self.current_spell], 
                         (self.x + self.size + 20, self.y + self.size//2), 10)

    def move(self, dx, dy):
        if dx != 0 and dy != 0:
            length = math.sqrt(dx * dx + dy * dy)
            dx = dx / length
            dy = dy / length

        new_x = self.x + dx * self.speed
        if 0 <= new_x <= WIDTH - self.size:
            self.x = new_x

    def shoot(self):
        if self.cooldown <= 0:
            spell_x = self.x + self.size/2
            spell_y = self.y
            self.spells.append(Spell(spell_x, spell_y, self.current_spell))
            self.cooldown = self.max_cooldown

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1
        
        for spell in self.spells[:]:
            spell.update()
            if spell.is_off_screen():
                self.spells.remove(spell)

    def cycle_spell(self):
        if self.current_spell == SpellType.FIRE and high_score >= 100:
            self.current_spell = SpellType.ICE
        elif self.current_spell == SpellType.ICE and high_score >= 200:
            self.current_spell = SpellType.WIND
        elif self.current_spell == SpellType.WIND:
            self.current_spell = SpellType.FIRE

class Spell:
    def __init__(self, x, y, spell_type):
        self.x = x
        self.y = y
        self.spell_type = spell_type
        self.speed = 7
        self.size = 10
        
        # Set properties based on spell type
        if spell_type == SpellType.FIRE:
            self.color = ORANGE
            self.damage = 30
            self.size = 30 
            
        elif spell_type == SpellType.ICE:
            self.color = ICE_BLUE
            self.damage = 20
            self.size = 30
        elif spell_type == SpellType.WIND:
            self.color = GREEN
            self.damage = 15
            self.size = 30
        
        self.effect = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.effect, (*self.color[:3], 128), 
                         (self.size, self.size), self.size)
    def update(self):
        self.y -= self.speed

    def draw(self):
        screen.blit(self.effect, (self.x - self.size, self.y - self.size))
        
        # Draw the spell core
        core_size = self.size // 2
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), core_size)
        
        # Add additional visual effects based on spell type
        if self.spell_type == SpellType.FIRE:
            # Add flame particles
            for _ in range(3):
                particle_x = self.x + random.randint(-self.size//2, self.size//2)
                particle_y = self.y + random.randint(-self.size//2, self.size//2)
                particle_size = random.randint(3, 8)
                pygame.draw.circle(screen, ORANGE, (int(particle_x), int(particle_y)), particle_size)
        
        elif self.spell_type == SpellType.ICE:
            # Add ice crystal effects
            for i in range(4):
                angle = i * (math.pi / 2)
                crystal_x = self.x + math.cos(angle) * (self.size//2)
                crystal_y = self.y + math.sin(angle) * (self.size//2)
                pygame.draw.circle(screen, WHITE, (int(crystal_x), int(crystal_y)), 4)
        
        elif self.spell_type == SpellType.WIND:
            # Add swirl effects
            for i in range(3):
                curve = math.sin(pygame.time.get_ticks() * 0.01 + i * 2) * 10
                offset_x = i * 10 - 10
                pygame.draw.circle(screen, WHITE, 
                                 (int(self.x + offset_x), int(self.y + curve)), 3)

    def apply_effect(self, enemy):
        if self.spell_type == SpellType.FIRE:
            enemy.burning = True
            enemy.burn_timer = 100  # Burn for 100 frames
        elif self.spell_type == SpellType.ICE:
            enemy.frozen_timer = 60  # Freeze for 60 frames
        elif self.spell_type == SpellType.WIND:
            enemy.pushed_by_wind = 4  # Push enemy up

    def is_off_screen(self):
        return self.y < 0
def draw_game_over():
    global high_score
    
    # Update high score if current score is higher
    if player.score > high_score:
        high_score = player.score
        save_high_score(high_score)
    
    font = pygame.font.Font(None, 74)
    text = font.render('Game Over', True, RED)
    text_rect = text.get_rect(center=(WIDTH/2, HEIGHT/2 - 50))
    screen.blit(text, text_rect)
    
    score_font = pygame.font.Font(None, 36)
    score_text = font.render(f'Final Score: {player.score}', True, BLUE)
    score_rect = score_text.get_rect(center=(WIDTH/2, HEIGHT/2 + 20))
    screen.blit(score_text, score_rect)
    
    # Add high score display
    high_score_text = score_font.render(f'High Score: {high_score}', True, BLUE)
    high_score_rect = high_score_text.get_rect(center=(WIDTH/2, HEIGHT/2 + 70))
    screen.blit(high_score_text, high_score_rect)
    
    if player.score >= high_score:
        new_record_text = score_font.render('New Record!', True, (255, 215, 0))  # Gold color
        new_record_rect = new_record_text.get_rect(center=(WIDTH/2, HEIGHT/2 + 120))
        screen.blit(new_record_text, new_record_rect)
    
    restart_text = score_font.render('Press R to Restart', True, BLUE)
    restart_rect = restart_text.get_rect(center=(WIDTH/2, HEIGHT/2 + 170))
    screen.blit(restart_text, restart_rect)
def draw_score():
    font = pygame.font.Font(None, 36)
    # Current score
    score_text = font.render(f'Score: {player.score}', True, BLUE)
    screen.blit(score_text, (10, 10))
    
    # High score
    high_score_text = font.render(f'High Score: {high_score}', True, BLUE)
    screen.blit(high_score_text, (10, 50))

# Create player
background = ScrollingBackground()

player = Player(WIDTH//2 - 15, HEIGHT - 100, BLUE)

# Enemy spawn settings
enemies = []
enemy_spawn_timer = 0
enemy_spawn_delay = 60

# Game loop
running = True
clock = pygame.time.Clock()
game_over = False


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over:
                player.shoot()
            if event.key == pygame.K_TAB and not game_over: 
                player.cycle_spell()
            if event.key == pygame.K_r and game_over:
                player = Player(WIDTH//2 - 15, HEIGHT - 100, BLUE)
                enemies = []
                game_over = False

            

    if not game_over:
        keys = pygame.key.get_pressed()
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = 1
        player.move(dx, 0)

        enemy_spawn_timer += 1
        if enemy_spawn_timer >= enemy_spawn_delay:
            enemies.append(Enemy())
            enemy_spawn_timer = 0

        background.update()
        player.update()

        for enemy in enemies[:]:
            enemy.move()
            
            for spell in player.spells[:]:
                if enemy.is_hit(spell):
                    enemy.health -= spell.damage
                    spell.apply_effect(enemy)
                    player.spells.remove(spell)
                    if enemy.health <= 0:
                        enemies.remove(enemy)
                        player.score += 10
                        break
            
            if enemy.is_off_screen():
                enemies.remove(enemy)
                player.health -= 20
                if player.health <= 0:
                    game_over = True
        screen.fill(WHITE)
        
     
        player.draw()
        for enemy in enemies:
            enemy.draw()
        for spell in player.spells:
            spell.draw()

        draw_score()

    
    if game_over:
        background.draw(screen)
        draw_game_over()
        
    else:
        background.draw(screen)
        player.draw()
        for enemy in enemies:
            enemy.draw()
        for spell in player.spells:
            spell.draw()
        draw_score()
        
 

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

