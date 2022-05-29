import pygame

from constants import *


def draw_bottle(screen, bottle_offset, bottle_size):
    line_offset = 14
    pygame.draw.rect(screen, BOT_BLUE, [bottle_offset[0] - line_offset, bottle_offset[1] - line_offset,
                                        bottle_size[0] + line_offset * 2,
                                        bottle_size[1] + line_offset * 2], 2, 15)
    line_offset = 12
    pygame.draw.rect(screen, BLACK, [bottle_offset[0] - line_offset, bottle_offset[1] - line_offset,
                                     bottle_size[0] + line_offset * 2,
                                     bottle_size[1] + line_offset * 2], 2, 15)
    line_offset = 10
    pygame.draw.rect(screen, GREEN, [bottle_offset[0] - line_offset, bottle_offset[1] - line_offset,
                                     bottle_size[0] + line_offset * 2,
                                     bottle_size[1] + line_offset * 2], 6, 15)
    line_offset = 10
    pygame.draw.rect(screen, WHITE, [bottle_offset[0] - line_offset, bottle_offset[1] - line_offset,
                                     bottle_size[0] + line_offset * 2,
                                     bottle_size[1] + line_offset * 2], 2, 15)
    line_offset = 4
    pygame.draw.rect(screen, BLACK, [bottle_offset[0] - line_offset, bottle_offset[1] - line_offset,
                                     bottle_size[0] + line_offset * 2,
                                     bottle_size[1] + line_offset * 2], 4, 5)
    line_offset = 2
    pygame.draw.rect(screen, BLACK, [bottle_offset[0] - line_offset, bottle_offset[1] - line_offset,
                                     bottle_size[0] + line_offset * 2,
                                     bottle_size[1] + line_offset * 2], 2)
    line_offset = 3
    pygame.draw.rect(screen, BOT_BLUE, [bottle_offset[0] - line_offset, bottle_offset[1] - line_offset,
                                        bottle_size[0] + line_offset * 2,
                                        bottle_size[1] + line_offset * 2], 2, 5)


def neck(screen, bottle_offset, bottle_size):
    neck_surf = screen.subsurface([bottle_offset[0] + bottle_size[0] / 5,
                                   bottle_offset[1] - 70,
                                   3 * bottle_size[0] / 5,
                                   70])

    # neck_surf.fill(BLACK)

    curv1 = neck_surf.subsurface([+15, neck_surf.get_height() - 40, 30, 40])
    curv1.fill(BLACK)
    x_offset = -35
    y_offset = -5
    line_offset = 0
    pygame.draw.rect(curv1, BLACK, [x_offset + line_offset, y_offset + line_offset, 55 - 2 * line_offset,
                                    -y_offset + 40 - 2 * line_offset], 10, border_bottom_right_radius=10,
                     border_top_right_radius=15)
    line_offset = 1
    pygame.draw.rect(curv1, BOT_BLUE, [x_offset + line_offset, y_offset + line_offset, 55 - 2 * line_offset,
                                       -y_offset + 40 - 2 * line_offset], 2, border_bottom_right_radius=10,
                     border_top_right_radius=22)
    line_offset = 4
    pygame.draw.rect(curv1, GREEN, [x_offset + line_offset, y_offset + line_offset, 55 - 2 * line_offset,
                                    -y_offset + 40 - 2 * line_offset], 6, border_bottom_right_radius=10,
                     border_top_right_radius=20)
    line_offset = 8
    pygame.draw.rect(curv1, WHITE, [x_offset + line_offset, y_offset + line_offset, 55 - 2 * line_offset,
                                    -y_offset + 40 - 2 * line_offset], 2, border_bottom_right_radius=7,
                     border_top_right_radius=15)
    line_offset = 12
    pygame.draw.rect(curv1, BOT_BLUE, [x_offset + line_offset, y_offset + line_offset, 55 - 2 * line_offset,
                                       -y_offset + 40 - 2 * line_offset], 2, border_bottom_right_radius=5,
                     border_top_right_radius=12)

    x_offset = 0
    y_offset = 0
    curv2 = neck_surf.subsurface([5, 0, 30, 40])
    curv2.fill(BLACK)
    line_offset = 0
    pygame.draw.rect(curv2, BOT_BLUE, [x_offset + line_offset, y_offset + line_offset, 40, 45], 2,
                     border_bottom_left_radius=23)
    line_offset = 6
    pygame.draw.rect(curv2, GREEN, [x_offset + line_offset, y_offset - line_offset, 40, 45 + line_offset], 4,
                     border_bottom_left_radius=27)
    line_offset = 4
    pygame.draw.rect(curv2, WHITE, [x_offset + line_offset, y_offset - line_offset, 40, 45 + line_offset], 2,
                     border_bottom_left_radius=26)
    line_offset = 10
    pygame.draw.rect(curv2, BLACK, [x_offset + line_offset, y_offset - line_offset, 40, 45 + line_offset], 2,
                     border_bottom_left_radius=30)
    line_offset = 12
    pygame.draw.rect(curv2, BOT_BLUE, [x_offset + line_offset, y_offset - line_offset + 2, 40, 45 + line_offset], 2,
                     border_bottom_left_radius=32)


def draw_bg(screen, screen_width, screen_height, bg_cube_size):
    for i in range(screen_width // bg_cube_size):
        for j in range(screen_height // bg_cube_size):
            color = GREEN if (i + j) % 2 == 0 else BLACK
            pygame.draw.rect(screen, color,
                             [i * bg_cube_size, j * bg_cube_size, (i + 1) * bg_cube_size, (j + 1) * bg_cube_size])
