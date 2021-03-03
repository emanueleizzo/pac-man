import pygame
import time
import copy
import math
import os.path
import numpy as np
import pandas as pd
from settings import *
from pygame.math import Vector2 as vec

class Player:
    # Costruttore
    def __init__(self, app):
        self.app = app
        self.grid_pos = copy.deepcopy(PLAYER_START_POS)
        self.starting_pos = copy.deepcopy(PLAYER_START_POS)
        self.pix_pos = self.get_pix_pos()
        self.direction = vec(1, 0)
        self.stored_direction = None
        self.able_to_move = True
        self.current_score = 0
        self.eaten_dots = 0
        self.speed = 1
        self.lives = 3
        self.counter = 1
        self.states = np.empty((0, 20), dtype=float)
        self.moves = np.empty((0, 4), dtype=float)

    # Update
    def update(self):
        # Se il player può muoversi, allora effettua un moviemnto
        if self.able_to_move:
            self.pix_pos += self.direction*self.speed
        # Se si trova al  centro della casella, e pertanto può cambiare  la sua direzione
        if self.time_to_move():
            # Cambia la direzione
            if self.stored_direction != None:
                self.direction = self.stored_direction
            # Controlla se può continuare a muoversi
            self.able_to_move = self.can_move()
            # Aggiunge una riga alla matrice delle mosse effettuate
            self.add_move()
        # Controlla se ha preso uno dei due corridoi che porta dall'altra parte della mappa
        if self.grid_pos == vec(28, 14) and self.stored_direction == vec(1, 0):
            self.grid_pos = vec(0, 14)
            self.pix_pos[0] = (self.grid_pos[0]-1)*self.app.cell_width+TOP_BOTTOM_BUFFER
        if self.grid_pos == vec(-1, 14) and self.stored_direction == vec(-1, 0):
            self.grid_pos = vec(27, 14)
            self.pix_pos[0] = (self.grid_pos[0]-1)*self.app.cell_width+TOP_BOTTOM_BUFFER
        # Calcola la posizione del fantasma nella griglia
        self.grid_pos[0] = (self.pix_pos[0]-TOP_BOTTOM_BUFFER +
                            self.app.cell_width//2)//self.app.cell_width+1
        self.grid_pos[1] = (self.pix_pos[1]-TOP_BOTTOM_BUFFER +
                            self.app.cell_height//2)//self.app.cell_height+1
        # Se si trova su un dot, allora chiama la funzione per mangiare il dot
        if self.on_dot():
            self.eat_dot()
        # Se si trova su un pellet, allora chiama la funzione per mangiare un pellet
        if self.on_pellet():
            self.eat_pellet()

    # Funzione che disegna il player sullo schermo
    # La seconda draw disegna le vite di cui dispone il player
    def draw(self):
        pygame.draw.circle(self.app.screen, PLAYER_COLOUR, (int(self.pix_pos.x), int(self.pix_pos.y)), self.app.cell_width//2-2)
        for x in range(self.lives):
            pygame.draw.circle(self.app.screen, PLAYER_COLOUR, (30 + 20*x, HEIGHT - 15), 7)
        
    # Verifica se il player si trova si un dot
    # (ossia se si trova al centro della casella dove si trova il dot)
    def on_dot(self):
        if self.grid_pos in self.app.dots:
            if int(self.pix_pos.x+TOP_BOTTOM_BUFFER//2) % self.app.cell_width == 0:
                if self.direction == vec(1, 0) or self.direction == vec(-1, 0):
                    return True
            if int(self.pix_pos.y+TOP_BOTTOM_BUFFER//2) % self.app.cell_height == 0:
                if self.direction == vec(0, 1) or self.direction == vec(0, -1):
                    return True
        return False

    # Verifica se il player si trova si un pellet
    # (ossia se si trova al centro della casella dove si trova il pellet)
    def on_pellet(self):
        if self.grid_pos in self.app.pellets:
            if int(self.pix_pos.x+TOP_BOTTOM_BUFFER//2) % self.app.cell_width == 0:
                if self.direction == vec(1, 0) or self.direction == vec(-1, 0):
                    return True
            if int(self.pix_pos.y+TOP_BOTTOM_BUFFER//2) % self.app.cell_height == 0:
                if self.direction == vec(0, 1) or self.direction == vec(0, -1):
                    return True
        return False

    # Mangia il dot su cui si trova
    # (rimuove il pellet dall'array e incrementa il numero di dot mangiati)
    def eat_dot(self):
        self.app.dots.remove(self.grid_pos)
        self.current_score += DOT_PTS
        self.eaten_dots += 1

    # Mangia il pellet su cui si trova (rimuove il pellet dall'array e incrementa il numero di dot mangiati)
    # Inoltre setta tutti i fantasmi sullo stato di "Frightened"
    def eat_pellet(self):
        initial_time = time.clock()
        self.app.pellets.remove(self.grid_pos)
        self.current_score += PELLET_PTS
        self.eaten_dots += 1
        # Per ogni fantasma vado a settare il suo stato in "Frightened", a cambiargli colore e a decrementare la sua velocita` 
        for enemy in self.app.enemies:
            # Controllo se il fantasma è nello stato di "Chase"
            if enemy.state == "Chase":
                enemy.state = "Frightened"
                # Se si trova all'esterno della zona di spawn, allora inverto la sua direzione
                if enemy.outside:
                    enemy.direction *= -1
                enemy.modifier = 0.75
                # Alloco alcune variabili all'interno dell'oggetto del fantasma
                enemy.colour = BLUE
                enemy.initial_time = initial_time
                enemy.counter = 0

    # Mangia il fantasma concui si incrocia, e setta il fantasma nello stato di "Eaten"
    # Inoltre incrementa il numero di fantasmi mangiati e calcola il percorso per arrivare alla zona di spawn
    def eat_enemy(self, enemy):
        self.current_score += VULNERABLE_GHOST_PTS*self.counter
        self.counter += 1
        enemy.state = "Eaten"
        enemy.colour = enemy.set_colour()
        enemy.modifier = 1

    # Salva la direzione appena ricevuta
    def move(self, direction):
        self.stored_direction = direction

########## HELPER FUNCTIONS ##########

    # Calcola la posizione in cui deve disegnare il player
    def get_pix_pos(self):
        return vec((self.grid_pos[0]*self.app.cell_width)+TOP_BOTTOM_BUFFER//2+self.app.cell_width//2,
                   (self.grid_pos[1]*self.app.cell_height) +
                   TOP_BOTTOM_BUFFER//2+self.app.cell_height//2)

        print(self.grid_pos, self.pix_pos)

    # Controlla se il player può muoversi
    # (controlla se si trova al centro della casella della griglia)
    def time_to_move(self):
        if int(self.pix_pos.x+TOP_BOTTOM_BUFFER//2) % self.app.cell_width == 0:
            if self.direction == vec(1, 0) or self.direction == vec(-1, 0) or self.direction == vec(0, 0):
                return True
        if int(self.pix_pos.y+TOP_BOTTOM_BUFFER//2) % self.app.cell_height == 0:
            if self.direction == vec(0, 1) or self.direction == vec(0, -1) or self.direction == vec(0, 0):
                return True

    # Controlla se il fantasma può continuare a muoversi in una certa direzione
    def can_move(self):
        if vec(self.grid_pos+self.direction) in self.app.walls:
            return False
        return True
        
########## DATASET CREATION FUNCTIONS ##########
    
    # Aggiunge una riga alla matrice delle mosse
    def add_move(self):
        enemies = self.app.enemies
        nearest_dot = self.nearest_dot()
        row = np.array([[self.grid_pos.x, self.grid_pos.y, 
                         enemies[0].grid_pos.x, enemies[0].grid_pos.y, self.is_not_frightened(0),
                         enemies[1].grid_pos.x, enemies[1].grid_pos.y, self.is_not_frightened(1),
                         enemies[2].grid_pos.x, enemies[2].grid_pos.y, self.is_not_frightened(2),
                         enemies[3].grid_pos.x, enemies[3].grid_pos.y, self.is_not_frightened(3),
                         self.check_wall(vec(-1, 0)), self.check_wall(vec(0, -1)), self.check_wall(vec(1, 0)), self.check_wall(vec(0, 1)),
                         nearest_dot.x, nearest_dot.y]])
        self.states = np.append(self.states, row, axis=0)
        row = np.array([self.convert_direction()])
        self.moves = np.append(self.moves, row, axis=0)
        
    # Restituisce 0 se il fantasma X è nello stato di frightened, 1 altrimenti
    def is_not_frightened(self, idx):
        enemy = self.app.enemies[idx]
        if enemy.state == "Frightened":
            return 0
        else:
            return 1
        
    # Restituisce 1 se la casella accanto al player (scelta tramite direction) non è un muro, 0 altrimenti
    def check_wall(self, direction):
        cell = self.grid_pos + direction
        if cell not in self.app.walls:
            return 1
        else:
            return 0

    # Restituisce la posizione del dot più vicino al player
    def nearest_dot(self):
        nearest_dot = self.app.dots[0]
        for i, dot in enumerate(self.app.dots):
            if ((nearest_dot.x-self.grid_pos.x)**2+(nearest_dot.y-self.grid_pos.y)**2) > ((dot.x-self.grid_pos.x)**2+(dot.y-self.grid_pos.y)**2):
                n_dot = dot
        return nearest_dot

    # Restituisce un array in cui il valore 1 rappresenta la direzione del player
    # ([1, 0, 0, 0]=Sù, [0, 1, 0, 0]=Sinistra, [0, 0, 1, 0]=Giù, [0, 0, 0, 1]=Destra)
    def convert_direction(self):
        if self.direction == vec(0, -1): return [1, 0, 0, 0]
        elif self.direction == vec(-1, 0): return [0, 1, 0, 0]
        elif self.direction == vec(0, 1): return [0, 0, 1, 0]
        elif self.direction == vec(1, 0): return [0, 0, 0, 1]

    # Prende una porzione della matrice proporzionale al numero di dot raccolti
    def reduce_matrix(self):
        total_dots = self.app.total_dots
        portion = math.floor(len(self.states)*(self.eaten_dots/total_dots))
        self.states = self.states[:portion+1]
        self.moves = self.moves[:portion+1]
        
    # Salva sul file le mosse effettuate
    def write_on_file(self):
        if os.path.isfile("moves.csv"):
            file = open("moves.csv", "a+")
        else:
            file = open("moves.csv", "a+")
            file.write("player_x,player_y,clyde_x,clyde_y,clyde_s,pinky_x,pinky_y,pinky_s,inky_x,inky_y,inky_s,blinky_x,blinky_y,blinky_s,wall_up,wall_left,wall_down,wall_right,nearest_dot_x,nearest_dot_y,up,left,down,right")
            file.flush()
        for i in range(len(self.states)):
            string = ""
            row = np.concatenate((self.states[i], self.moves[i]))
            for i, element in enumerate(row):
                string = string+str(element)
                if i < 23:
                    string += ","
                else:
                    string += "\n"
            file.write(string)
            file.flush()
        file.close()