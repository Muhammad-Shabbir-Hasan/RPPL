#! /usr/bin/env python3

# Robot Planning Python Library (RPPL)
# Copyright (c) 2021 Alexander J. LaValle. All rights reserved.
# This software is distributed under the simplified BSD license.

import pygame, time, random
from pygame.locals import *
import networkx as nx
from networkx import shortest_path
from math import *
from rppl_util import *
from rppl_globals import *


show_rrt_progress = True
bidirectional = False
length = 60

links = [1000/length for i in range(length)]
base = [xmax/2,ymax/2]
config = [-2*pi/length for i in range(length)]
stepsize = 0.01
numobst = 0  #number of obstacles
goal = [2*pi/length for i in range(length)]
bias = 2

Open = True
stepping = True
restart = True


def transform_robot(l, b, q):
    cp = b
    cangle = 0.0
    tl = [b]
    for i in range(len(l)):
        npx = cp[0] + l[i] * cos(cangle + q[i])
        npy = cp[1] + l[i] * sin(cangle + q[i])
        cp = [npx,npy]
        tl.append(cp)
        cangle += q[i]
    return tl

def config_distance(q, r):
    d = 0.0
    for i in range(len(q)):
        d += sqr(min(abs(q[i] - r[i]), 2.0 * pi - abs(q[i] - r[i])))
    return sqrt(d)

def add_next_node(q,closest,t):
    newconfig = []
    c = t.nodes[closest]['config']
    d = config_distance(q,c)
    #if d == 0:
    #    d = 1.0E-20
    diff = stepsize / d
    for i in range(len(q)):
        if abs(q[i] - c[i]) < pi:
            newconfig.append(fix_angle(c[i] + (q[i] - c[i]) * diff))
        else:
            newconfig.append(fix_angle(c[i] - (q[i] - c[i]) * diff))
        if i == 40:
            print(d,diff)
    return newconfig

def find_closest_node(rc,nodes):
    a = [config_distance(rc, nodes[0]['config']),0]
    for i in nodes:
        if i > 0:
            b = [config_distance(rc, nodes[i]['config']),i]
            if a[0] > b[0]:
                a = [config_distance(rc, nodes[i]['config']),i]
    return a[1]

def step_to_config(t,q):
    stepping = True
    while stepping:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                quit()
        if show_rrt_progress:
            screen.fill(black)
            draw_arm(transform_robot(links, base, I.nodes[len(I.nodes)-1]['config']),screen,white)
            if bidirectional:
                draw_arm(transform_robot(links, base, G.nodes[len(G.nodes)-1]['config']),screen,red)
            pygame.display.update()
        closest = find_closest_node(q,t.nodes)
        t.add_node(len(t.nodes),config=add_next_node(q,closest,t))
        if safe_segments(transform_robot(links, base, t.nodes[len(t.nodes)-1]['config']),obstacles):
            t.add_edge(len(t.nodes)-1,closest)
            if config_distance(t.nodes[len(t.nodes)-1]['config'],q) <= stepsize:
                stepping = False
        else:
            t.remove_node(len(t.nodes)-1)
            stepping = False

while Open:
    if restart:
        I = nx.Graph()
        G = nx.Graph()
        I.add_node(0, config=config)
        G.add_node(0, config=goal)
        pygame.init()
        screen = pygame.display.set_mode([xmax,ymax])
        screen.fill(black)
        obstacles = create_random_discs(numobst,base)
        draw_discs(obstacles,screen)
        draw_arm(transform_robot(links, base, I.nodes[len(I.nodes)-1]['config']),screen,white)
        pygame.display.update()
        time.sleep(0.5)
        pstat = 0
        restart = False
        pygame.display.set_caption('RRT Line Segment Robot')
        t = time.time()
        i = 0
        
    if bidirectional:
        while config_distance(I.nodes[len(I.nodes)-1]['config'],G.nodes[len(G.nodes)-1]['config']) > stepsize:
            rc = [random.uniform(0.0, 2 * pi) for i in range(length)]
            step_to_config(I,rc)
            step_to_config(G,I.nodes[len(I.nodes)-1]['config'])
            if config_distance(I.nodes[len(I.nodes)-1]['config'],G.nodes[len(G.nodes)-1]['config']) > stepsize:
                rc = [random.uniform(0.0, 2 * pi) for i in range(length)]
                step_to_config(G,rc)
                step_to_config(I,G.nodes[len(G.nodes)-1]['config'])

    else:
        while config_distance(I.nodes[len(I.nodes)-1]['config'], goal) > stepsize:
            if i % bias == 0:
                rc = goal
            else:
                rc = [random.uniform(0.0, 2 * pi) for i in range(length)]
            step_to_config(I,rc)
            i += 1

    print('time elapsed: ' + str(time.time() - t) + ' seconds')
    path = shortest_path(I, source=0, target=len(I.nodes)-1)
    for s in path:
        time.sleep(0.01)
        screen.fill(black)
        draw_discs(obstacles,screen)
        draw_arm(transform_robot(links, base, I.nodes[s]['config']),screen,white)
        pygame.display.update()

    path = shortest_path(G, source=len(G.nodes)-1, target=0)
    for s in path:
        time.sleep(0.01)
        screen.fill(black)
        draw_discs(obstacles,screen)
        draw_arm(transform_robot(links, base, G.nodes[s]['config']),screen,white)
        pygame.display.update()

    while not restart:
        time.sleep(0.05)
        pygame.display.update()
        mpos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                Open = False
                restart = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                restart = True