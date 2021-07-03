import json
import os
import pygame
import random

from json.decoder import JSONDecodeError

import consts


class Application:
    _KEY_MAP = {
        pygame.K_UP: (0, -1),
        pygame.K_DOWN: (0, 1),
        pygame.K_LEFT: (-1, 0),
        pygame.K_RIGHT: (1, 0),
    }

    def __init__(self):
        pygame.init()
        pygame.mixer.init()  # для звука
        self.screen = pygame.display.set_mode(
            (consts.WINDOW_WIDTH, consts.WINDOW_HEIGHT)
        )
        pygame.display.set_caption(consts.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.snake = Snake()
        self.apple = Apple(
            self.snake.head.rect.x,
            self.snake.head.rect.y,
        )
        self.apple.place(self.snake)
        self.score = Score()

    def run(self):
        while True:
            self.clock.tick(consts.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in self._KEY_MAP:
                        self.snake.head.change_dir(
                            self._KEY_MAP[event.key]
                        )
            self.snake.update()
            self.snake.check_collision()
            if (
                self.snake.head.rect.x == self.apple.rect.x and
                self.snake.head.rect.y == self.apple.rect.y 
            ):
                self.score.update()
                self.snake.append()
                self.apple.place(self.snake)
            self.screen.fill(consts.BLACK)
            self.score.draw(self.screen)
            self.snake.draw(self.screen)
            self.apple.draw(self.screen)
            pygame.display.flip()


class StaticSquare(pygame.sprite.Sprite):
    def __init__(self, x_pos=0, y_pos=0, color=consts.WHITE):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface(
            (
                consts.CELL_SIZE - consts.CELL_BORDER,
                consts.CELL_SIZE - consts.CELL_BORDER)
            )
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (x_pos, y_pos)

    def change_color(self, new_color):
        self.image.fill(new_color)

    def change_pos(self, new_x, new_y):
        self.rect.x, self.rect.y = new_x, new_y

    def __str__(self):
        return f'({self.rect.x}, {self.rect.y})'


class DynamicSquare(StaticSquare):
    def __init__(self, x_pos, y_pos, dir, color=consts.GREEN):
        super().__init__(x_pos, y_pos, color)
        self.direction = dir

    def update(self):
        x_dir, y_dir = self.direction
        self.change_pos(
            (self.rect.x + consts.CELL_SIZE * x_dir) % consts.WINDOW_WIDTH,
            (self.rect.y + consts.CELL_SIZE * y_dir) % consts.WINDOW_HEIGHT,
        )

    def change_dir(self, new_dir):
        x_dir, y_dir = self.direction
        x_new_dir, y_new_dir = new_dir
        if x_dir * x_new_dir + y_dir * y_new_dir != 0:
            return
        self.direction = new_dir

    def __str__(self):
        return f'({self.rect.x}, {self.rect.y}) <{self.direction}>'


class Snake:
    def __init__(
        self,
        start_x=consts.WINDOW_WIDTH / 2,
        start_y=consts.WINDOW_HEIGHT / 2,
        start_dir=consts.START_DIR,
        start_len=5,
    ):
        self._snake = []
        self._sprites = pygame.sprite.Group()
        self._collision = False
        x_pos, y_pos = start_x, start_y
        x_dir, y_dir = start_dir
        for _ in range(start_len):
            square = DynamicSquare(x_pos, y_pos, dir=start_dir)
            x_pos = (x_pos - consts.CELL_SIZE * x_dir) % consts.WINDOW_WIDTH
            y_pos = (y_pos - consts.CELL_SIZE * y_dir) % consts.WINDOW_HEIGHT
            self._snake.append(square)

    def update(self):
        self._sprites.empty()
        self._move_tail_to_head()
        for square in self._snake:
            self._sprites.add(square)

    def draw(self, screen):
        self._sprites.draw(screen)

    def append(self):
        if self._collision:
            return
        tail = self.tail
        x_dir, y_dir = tail.direction
        x_pos = (tail.rect.x + x_dir * consts.CELL_SIZE) % consts.WINDOW_WIDTH
        y_pos = (tail.rect.y + y_dir * consts.CELL_SIZE) % consts.WINDOW_HEIGHT
        add_square = DynamicSquare(x_pos, y_pos, (x_dir, y_dir))
        self._snake.append(add_square)

    def check_collision(self):
        head_x = self.head.rect.x
        head_y = self.head.rect.y
        for square in self._snake[1:]:
            if (
                square.rect.x == head_x and
                square.rect.y == head_y
            ):
                self._collision = True
                self._fill_red()
                return

    def has_square_pos(self, x, y):
        for square in self._snake:
            if (
                x == square.rect.x and
                y == square.rect.y
            ):
                return True
        return False

    @property
    def head(self):
        return self._snake[0]

    @property
    def tail(self):
        return self._snake[-1]

    def _move_tail_to_head(self):
        if self._collision:
            return
        head = self.head
        tail = self.tail
        tail.rect.x = head.rect.x
        tail.rect.y = head.rect.y
        tail.direction = head.direction
        tail.update()
        self._snake.insert(0, tail)
        self._snake.pop()

    def _fill_red(self):
        for square in self._snake:
            square.change_color(consts.RED)


class Apple(StaticSquare):
    def __init__(self, start_x=0, start_y=0):
        super().__init__(color=consts.RED)
        self._sprites = pygame.sprite.Group()
        self._sprites.add(self)
        self._start_pos = (
            start_x,
            start_y,
        )

    def place(self, snake):
        x_steps = consts.WINDOW_WIDTH // (2 * consts.CELL_SIZE) - 1
        y_steps = consts.WINDOW_HEIGHT // (2 * consts.CELL_SIZE) - 1

        x, y = start_x, start_y = self._start_pos

        yet_another_try = True
        while yet_another_try:
            yet_another_try = False
            x_off = random.randint(-x_steps, x_steps)
            y_off = random.randint(-y_steps, y_steps)

            x = (start_x + x_off * consts.CELL_SIZE) % consts.WINDOW_WIDTH
            y = (start_y + y_off * consts.CELL_SIZE) % consts.WINDOW_HEIGHT

            if snake.has_square_pos(x, y):
                yet_another_try = True
        self.change_pos(x, y)

    def draw(self, screen):
        self._sprites.draw(screen)


class Score:
    def __init__(self):
        self._cur_score = 0
        data = None
        if os.path.exists(consts.MAX_SCORE_PATH):
            with open(consts.MAX_SCORE_PATH, 'r') as max_score_file:
                try:
                    data = json.load(max_score_file)
                except JSONDecodeError:
                    pass
        self._cached_data = data or {}
        self._max_score = self._cached_data.get('max_score', 0)
        self.font = pygame.font.SysFont('freesansbold', 25)

    def draw(self, screen):
        x_pos = consts.SCORE_TEXT_X_POS
        y_pos = consts.SCORE_TEXT_Y_POS
        step = 25
        for raw_text in [
            f'Score: {self._cur_score}',
            f'Max: {self._max_score}',
        ]:
            text = self.font.render(
                raw_text, True, (255, 255, 255)
            )
            screen.blit(
                text, (x_pos, y_pos),
            )
            y_pos += step
        pygame.display.flip()

    def update(self):
        self._cur_score += 1
        if self._cur_score > self._max_score:
            self._max_score = self._cur_score
            self._cached_data['max_score'] = self._max_score
            with open(consts.MAX_SCORE_PATH, 'w+') as max_score_file:
                print(self._cached_data)
                json.dump(self._cached_data, max_score_file)


def main():
    app = Application()
    app.run()


if __name__ == '__main__':
    main()
