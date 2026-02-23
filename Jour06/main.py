# -*- coding: utf-8 -*-
"""
</> JOUR 6 | Jeu de Plateforme 2D avec Physique
Jeu : Ninja D : Traversée des Régions Légendaires
Langage : Python
Bibliothèque : Pygame
"""

import pygame
import json
import random
import math
import os
import sys

# --- Initialisation de Pygame ---
pygame.init()
pygame.font.init()

# --- Constantes du Jeu ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
GAME_TITLE = "Ninja D : Traversée des Régions Légendaires"

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
NINJA_COLOR = (60, 60, 60)
SAMURAI_COLOR = (150, 40, 40)
GROUND_COLOR = (100, 80, 60)
SKY_COLOR = (135, 206, 235)
COIN_COLOR = (255, 223, 0)
PARTICLE_DUST_COLOR = (188, 143, 143)
PARTICLE_EXPLOSION_COLOR = (255, 100, 0)
YELLOW = (255, 255, 0)

# Constantes de Physique
GRAVITY = 0.5
FRICTION = 0.15
BOUNCE_FACTOR = 0.2  # Léger rebond

# Propriétés du Joueur
PLAYER_ACCEL = 0.8
PLAYER_JUMP_STRENGTH = -12
PLAYER_MAX_JUMPS = 3
PLAYER_HEALTH = 3
PLAYER_ATTACK_COOLDOWN = 300 # ms
PLAYER_KUNAI_COOLDOWN = 500 # ms
PLAYER_SWORD_RANGE = 50
PLAYER_SWORD_DURATION = 100 # ms

# Propriétés des Ennemis
SAMURAI_SPEED = 1.5
SAMURAI_CHASE_RADIUS = 300
SAMURAI_PATROL_DISTANCE = 100

# Fichier pour le High Score
HIGHSCORE_FILE = "highscore_ninja_d.txt"

# --- Contenu du fichier de map JSON (intégré pour la portabilité) ---
# '1' = Sol, '2' = Point de départ, '3' = Ennemi Samouraï, '4' = Pièce
MAP_JSON_DATA = """
{
    "tilewidth": 32,
    "tileheight": 32,
    "width": 100,
    "height": 24,
    "layers": [
        {
            "name": "level1",
            "data": [
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,4,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,4,4,4,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
            ]
        }
    ]
}
"""

# --- Classes du jeu ---

class PhysicsEntity(pygame.sprite.Sprite):
    """Classe de base pour toutes les entités avec physique."""
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        
        self.on_ground = False

    def apply_physics(self, tiles):
        """Applique la gravité, la friction et gère les collisions."""
        # Mouvement horizontal
        self.acc.x += self.vel.x * -FRICTION
        self.vel.x += self.acc.x
        self.pos.x += self.vel.x
        self.rect.x = round(self.pos.x)
        self.check_collision_x(tiles)

        # Mouvement vertical
        self.acc.y = GRAVITY
        self.vel.y += self.acc.y
        self.pos.y += self.vel.y
        self.rect.y = round(self.pos.y)
        self.on_ground = False # Supposons que nous sommes en l'air
        self.check_collision_y(tiles)
        
        # Réinitialiser l'accélération pour le prochain frame
        self.acc.x = 0

    def check_collision_x(self, tiles):
        """Vérifie et résout les collisions sur l'axe X."""
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel.x > 0: # Se déplace vers la droite
                    self.rect.right = tile.rect.left
                    self.vel.x *= -BOUNCE_FACTOR
                elif self.vel.x < 0: # Se déplace vers la gauche
                    self.rect.left = tile.rect.right
                    self.vel.x *= -BOUNCE_FACTOR
                self.pos.x = self.rect.x

    def check_collision_y(self, tiles):
        """Vérifie et résout les collisions sur l'axe Y."""
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel.y > 0: # Tombe
                    self.rect.bottom = tile.rect.top
                    self.on_ground = True
                    # Crée des particules de poussière à l'atterrissage si on bouge vite
                    if abs(self.vel.y) > 2:
                        game.create_particles(self.rect.midbottom, 5, PARTICLE_DUST_COLOR, -3, 2)
                    self.vel.y = 0
                elif self.vel.y < 0: # Saute contre un plafond
                    self.rect.top = tile.rect.bottom
                    self.vel.y *= -BOUNCE_FACTOR
                self.pos.y = self.rect.y


class Player(PhysicsEntity):
    def __init__(self, x, y):
        super().__init__(x, y, 24, 48, NINJA_COLOR)
        self.start_pos = (x, y)
        self.jumps_left = PLAYER_MAX_JUMPS
        self.health = PLAYER_HEALTH
        self.score = 0
        self.direction = 1 # 1 for right, -1 for left
        
        self.last_sword_attack = 0
        self.is_attacking_sword = False
        self.sword_attack_timer = 0
        
        self.last_kunai_attack = 0

    def update(self, keys, tiles):
        self.handle_input(keys)
        self.apply_physics(tiles)

        # Gérer la durée de l'attaque à l'épée
        if self.is_attacking_sword:
            if pygame.time.get_ticks() - self.sword_attack_timer > PLAYER_SWORD_DURATION:
                self.is_attacking_sword = False
        
        # Le joueur tombe hors du monde
        if self.rect.top > SCREEN_HEIGHT:
            self.take_damage()

    def handle_input(self, keys):
        if keys[pygame.K_LEFT]:
            self.acc.x = -PLAYER_ACCEL
            self.direction = -1
        if keys[pygame.K_RIGHT]:
            self.acc.x = PLAYER_ACCEL
            self.direction = 1
        
        # Gérer le saut
        if self.on_ground:
            self.jumps_left = PLAYER_MAX_JUMPS

    def jump(self):
        if self.jumps_left > 0:
            self.vel.y = PLAYER_JUMP_STRENGTH
            self.jumps_left -= 1
            # Créer des particules de saut
            game.create_particles(self.rect.midbottom, 8, WHITE, -5, 5)

    def sword_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_sword_attack > PLAYER_ATTACK_COOLDOWN:
            self.last_sword_attack = now
            self.is_attacking_sword = True
            self.sword_attack_timer = now
            
            # Créer une hitbox pour l'épée
            sword_rect = pygame.Rect(0,0, PLAYER_SWORD_RANGE, self.rect.height)
            if self.direction == 1:
                sword_rect.left = self.rect.right
            else:
                sword_rect.right = self.rect.left
            sword_rect.top = self.rect.top
            
            # Vérifier la collision avec les ennemis
            for enemy in game.enemies:
                if sword_rect.colliderect(enemy.rect):
                    enemy.die()
                    self.score += 50
    
    def kunai_attack(self):
        now = pygame.time.get_ticks()
        if now - self.last_kunai_attack > PLAYER_KUNAI_COOLDOWN:
            self.last_kunai_attack = now
            kunai_x = self.rect.right if self.direction == 1 else self.rect.left
            kunai = Kunai(kunai_x, self.rect.centery, self.direction)
            game.all_sprites.add(kunai)
            game.projectiles.add(kunai)

    def collect(self, item):
        self.score += item.value
        item.kill()

    def take_damage(self):
        self.health -= 1
        game.create_particles(self.rect.center, 20, RED, -10, 10, lifespan=40)
        if self.health <= 0:
            # Game Over logic handled in main game loop
            pass
        else:
            # Respawn at start position
            self.pos.x, self.pos.y = self.start_pos
            self.vel.x, self.vel.y = 0, 0
            self.rect.topleft = (self.pos.x, self.pos.y)


class Samurai(PhysicsEntity):
    def __init__(self, x, y):
        super().__init__(x, y, 30, 50, SAMURAI_COLOR)
        self.start_x = x
        self.state = "patrol" # "patrol" ou "chase"
        self.direction = 1

    def update(self, tiles):
        self.ai()
        self.apply_physics(tiles)
        
        # Collision avec le joueur
        if self.rect.colliderect(game.player.rect):
            # Simple AABB collision pour l'instant
            game.player.take_damage()

    def ai(self):
        # Utiliser la position du joueur depuis l'objet game
        player = game.player
        dist_to_player = self.pos.distance_to(player.pos)
        
        if dist_to_player < SAMURAI_CHASE_RADIUS:
            self.state = "chase"
        else:
            self.state = "patrol"

        if self.state == "patrol":
            if self.pos.x > self.start_x + SAMURAI_PATROL_DISTANCE:
                self.direction = -1
            elif self.pos.x < self.start_x - SAMURAI_PATROL_DISTANCE:
                self.direction = 1
            self.vel.x = SAMURAI_SPEED * self.direction
        
        elif self.state == "chase":
            if player.pos.x < self.pos.x:
                self.direction = -1
            else:
                self.direction = 1
            self.vel.x = SAMURAI_SPEED * self.direction * 1.5 # Plus rapide en poursuite

    def die(self):
        game.create_particles(self.rect.center, 30, PARTICLE_EXPLOSION_COLOR, -8, 8, lifespan=60)
        self.kill()


class Kunai(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((20, 5))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.speed = 15

    def update(self):
        self.rect.x += self.speed * self.direction
        
        # Supprimer s'il sort de l'écran
        if not (-100 < self.rect.x < game.level_width + 100):
            self.kill()
        
        # Collision avec les ennemis
        hit_enemies = pygame.sprite.spritecollide(self, game.enemies, False)
        for enemy in hit_enemies:
            enemy.die()
            game.player.score += 50
            self.kill()
            
        # Collision avec les murs
        if pygame.sprite.spritecollide(self, game.tiles, False):
            self.kill()


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        super().__init__()
        self.image = pygame.Surface([size, size])
        self.image.fill(GROUND_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))


class Collectible(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        super().__init__()
        self.image = pygame.Surface([size // 2, size // 2])
        self.image.fill(COIN_COLOR)
        self.rect = self.image.get_rect(center=(x + size//2, y + size//2))
        self.value = 10


class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, vel_x, vel_y, lifespan):
        super().__init__()
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vel_x, vel_y)
        self.lifespan = lifespan
        self.color = color
        self.size = random.randint(2, 5)
        
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(self.color)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.pos += self.vel
        self.rect.center = self.pos
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()


class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)
    
    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        y = -target.rect.centery + int(SCREEN_HEIGHT / 2)

        # Limiter le défilement aux bords du niveau
        x = min(0, x)  # Bord gauche
        y = min(0, y)  # Bord haut
        x = max(-(self.width - SCREEN_WIDTH), x)  # Bord droit
        y = max(-(self.height - SCREEN_HEIGHT), y) # Bord bas
        
        self.camera = pygame.Rect(x, y, self.width, self.height)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = "playing" # "playing", "game_over"

        self.font_big = pygame.font.SysFont("Consolas", 72)
        self.font_medium = pygame.font.SysFont("Consolas", 36)
        self.font_small = pygame.font.SysFont("Consolas", 24)
        
        self.load_highscore()
        self.setup_level()

    def load_highscore(self):
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                self.highscore = int(f.read())
        except (FileNotFoundError, ValueError):
            self.highscore = 0
            
    def save_highscore(self):
        if self.player.score > self.highscore:
            self.highscore = self.player.score
            with open(HIGHSCORE_FILE, 'w') as f:
                f.write(str(self.highscore))

    def setup_level(self):
        self.all_sprites = pygame.sprite.Group()
        self.tiles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()

        # Charger la map depuis le JSON intégré
        map_data = json.loads(MAP_JSON_DATA)
        layer = map_data['layers'][0]['data']
        w, h = map_data['width'], map_data['height']
        tw, th = map_data['tilewidth'], map_data['tileheight']
        
        self.level_width = w * tw
        self.level_height = h * th

        for row in range(h):
            for col in range(w):
                tile_id = layer[row * w + col]
                x, y = col * tw, row * th
                if tile_id == 1: # Sol
                    tile = Tile(x, y, tw)
                    self.all_sprites.add(tile)
                    self.tiles.add(tile)
                elif tile_id == 2: # Joueur
                    self.player = Player(x, y)
                elif tile_id == 3: # Ennemi
                    samurai = Samurai(x, y)
                    self.all_sprites.add(samurai)
                    self.enemies.add(samurai)
                elif tile_id == 4: # Pièce
                    coin = Collectible(x, y, tw)
                    self.all_sprites.add(coin)
                    self.collectibles.add(coin)

        self.all_sprites.add(self.player)
        self.camera = Camera(self.level_width, self.level_height)

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if self.game_state == "playing":
                    if event.key == pygame.K_UP:
                        self.player.jump()
                    if event.key == pygame.K_x:
                        self.player.sword_attack()
                    if event.key == pygame.K_c:
                        self.player.kunai_attack()
                elif self.game_state == "game_over":
                    if event.key == pygame.K_r:
                        self.reset_game()
                    if event.key == pygame.K_q:
                        self.running = False


    def update(self):
        if self.game_state == "playing":
            keys = pygame.key.get_pressed()
            
            # Mettre à jour chaque groupe séparément
            self.player.update(keys, self.tiles)
            
            # Mettre à jour les ennemis
            for enemy in self.enemies:
                enemy.update(self.tiles)
            
            # Mettre à jour les projectiles et particules
            self.projectiles.update()
            self.particles.update()

            self.camera.update(self.player)
            
            # Collisions joueur / collectibles
            collected_items = pygame.sprite.spritecollide(self.player, self.collectibles, True)
            for item in collected_items:
                self.player.collect(item)
            
            # Vérifier la condition de fin de partie
            if self.player.health <= 0:
                self.game_state = "game_over"
                self.save_highscore()

    def draw(self):
        self.screen.fill(SKY_COLOR)
        
        # Dessiner tous les sprites en utilisant la caméra
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        
        # Dessiner les projectiles et particules
        for sprite in self.projectiles:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.particles:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        
        # Dessiner la hitbox de l'épée pour le debug/feedback
        if self.player.is_attacking_sword:
            sword_rect = pygame.Rect(0,0, PLAYER_SWORD_RANGE, self.player.rect.height)
            if self.player.direction == 1:
                sword_rect.left = self.player.rect.right
            else:
                sword_rect.right = self.player.rect.left
            sword_rect.top = self.player.rect.top
            
            # Dessiner le rectangle de l'épée par rapport à la caméra
            temp_surface = pygame.Surface(sword_rect.size, pygame.SRCALPHA)
            temp_surface.fill((255, 255, 255, 100))
            self.screen.blit(temp_surface, self.camera.apply_rect(sword_rect))

        self.draw_hud()

        if self.game_state == "game_over":
            self.draw_game_over_screen()

        pygame.display.flip()
        
    def draw_hud(self):
        score_text = self.font_medium.render(f"Score: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        lives_text = self.font_medium.render(f"Vies: {self.player.health}", True, WHITE)
        self.screen.blit(lives_text, (SCREEN_WIDTH - lives_text.get_width() - 10, 10))
        
        # Instructions
        instructions = self.font_small.render("X: Épée  C: Kunaï  Haut: Sauter", True, WHITE)
        self.screen.blit(instructions, (SCREEN_WIDTH // 2 - instructions.get_width() // 2, 10))

    def draw_game_over_screen(self):
        # Fond semi-transparent
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title_text = self.font_big.render("FIN DE LA PARTIE", True, RED)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 4))

        score_text = self.font_medium.render(f"Votre Score: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        
        highscore_text = self.font_medium.render(f"High Score: {self.highscore}", True, COIN_COLOR)
        self.screen.blit(highscore_text, (SCREEN_WIDTH // 2 - highscore_text.get_width() // 2, SCREEN_HEIGHT // 2))

        restart_text = self.font_small.render("Appuyez sur 'R' pour recommencer", True, WHITE)
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT * 3 / 4))
        
        quit_text = self.font_small.render("Appuyez sur 'Q' pour quitter", True, WHITE)
        self.screen.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, SCREEN_HEIGHT * 3 / 4 + 40))

    def create_particles(self, position, count, color, min_vel, max_vel, lifespan=20):
        for _ in range(count):
            vel_x = random.uniform(min_vel, max_vel)
            vel_y = random.uniform(min_vel, max_vel)
            p = Particle(position[0], position[1], color, vel_x, vel_y, lifespan)
            self.all_sprites.add(p)
            self.particles.add(p)
            
    def reset_game(self):
        self.save_highscore()
        self.setup_level()
        self.game_state = "playing"

# --- Point d'entrée principal ---
if __name__ == "__main__":
    print("Lancement de 'Ninja D : Traversée des Régions Légendaires'...")
    print("Contrôles : Flèches pour bouger/sauter, X pour l'épée, C pour le kunaï.")
    print('"Nous créons qui nous sommes avec nos pensées"')
    
    # Instance globale du jeu accessible depuis partout
    global game
    game = Game()
    game.run()
