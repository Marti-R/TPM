import pygame


class ExperimentScreen:
    def __init__(self, parent, size, position, marker_distribution, marker_height,
                 image_location, font, background_color=(0, 0, 0), mirrored=True):
        assert isinstance(parent, pygame.Surface), \
            'Parent must be a Pygame surface.'
        assert isinstance(size, tuple) and len(size) == 2 and all(i > 0 for i in size), \
            'Size must be a int-tuple of length 2 with all values greater than 0.'
        assert isinstance(position, tuple) and len(position) == 2, \
            'Position must be a int-tuple of length 2.'
        assert isinstance(background_color, tuple) and len(background_color) == 3 and \
               all(0 <= i < 256 for i in background_color), \
            'The background color must be a int-tuple of length 3 (RGB).'
        assert isinstance(marker_distribution, tuple) and len(marker_distribution) == 3 and \
               all(i > 0 for i in marker_distribution), \
            'The marker distribution must be a int-tuple of length 3 (left of screen, on screen, right of screen).'
        assert isinstance(marker_height, int) and marker_height > 0, \
            'The marker height must be an integer above 0.'
        assert isinstance(image_location, list) and len(image_location) > 0 and \
               all(isinstance(location, str) for location in image_location), \
            'The image location must be a list of strings, which show the possible images for the markers.'
        assert isinstance(mirrored, bool), \
            'The mirrored flag must be a boolean deciding whether the markers are mirrored at the middle of the screen.'

        self.parent = parent
        self.surface = pygame.Surface(size)
        self.surface.fill(COLOR_BACKGROUND)
        experiment_text = "Experiment"
        experiment_render = font.render(experiment_text, 0, (255, 255, 255))
        self.surface.blit(experiment_render,
                          ((size[0] - experiment_render.get_width()) / 2,
                           (size[1] - experiment_render.get_height()) / 2))

        self.rectangle = self.surface.get_rect().move(position)
        self.background_color = background_color
        self.marker_height = marker_height
        self.image_location = image_location
        self.mirrored = mirrored
        self.markers = deque(maxlen=sum(marker_distribution))

        _surf = [None] * sum(marker_distribution)
        _rect = [None] * sum(marker_distribution)

        for i in range(sum(marker_distribution)):
            loaded_image = pygame.image.load(image_location[rdm.randint(0, len(image_location) - 1)])
            zoom_factor = marker_height / loaded_image.get_height()
            if self.mirrored:
                _surf[i] = [pygame.transform.rotozoom(loaded_image, 0, zoom_factor),
                            pygame.transform.flip(pygame.transform.rotozoom(loaded_image, 180, zoom_factor),
                                                  True, False)]
            else:
                _surf[i] = pygame.transform.rotozoom(loaded_image, 0, zoom_factor)

        self.location_pointer = _surf[marker_distribution[0]][0].get_width() / 2
        self.space = parent.get_width() / marker_distribution[1]
        self.left_spawn = -(marker_distribution[0] * self.space)
        self.right_spawn = parent.get_width() + marker_distribution[2] * self.space

        for i in range(sum(marker_distribution)):
            if self.mirrored:
                _rect[i] = [_surf[i][0].get_rect(), _surf[i][1].get_rect()]
                _rect[i][0].center = [(-marker_distribution[0] + i) * self.space
                                      + self.location_pointer, parent.get_height() * 1 / 4]
                _rect[i][1].center = [(-marker_distribution[0] + i) * self.space
                                      + self.location_pointer, parent.get_height() * 3 / 4]
            else:
                _rect[i] = _surf[i][0].get_rect()
                _rect[i].center = [(-marker_distribution[0] + i) * self.space
                                   + self.location_pointer, parent.get_height() * 2 / 4]

            wobble_x_abs = int(self.space / 3)
            wobble_x_random = rdm.randint(-wobble_x_abs, wobble_x_abs)

            if self.mirrored:
                wobble_y_abs = int(parent.get_height() / 4 - _rect[i][0].height / 2)
                wobble_y_random = rdm.randint(-wobble_y_abs, wobble_y_abs)
                _rect[i] = [_rect[i][0].move(wobble_x_random, wobble_y_random),
                            _rect[i][1].move(wobble_x_random, -wobble_y_random)]
                self.markers.append([[_surf[i][0], _rect[i][0]], [_surf[i][1], _rect[i][1]]])

            else:
                wobble_y_abs = int((parent.get_width() / 2))
                wobble_y_random = rdm.randint(-wobble_y_abs, wobble_y_abs)
                _rect[i] = _rect[i].move(wobble_x_random, wobble_y_random)
                self.markers.append([_surf[i], _rect[i]])
        print("init")
        self.move(0)

    def move(self, delta):
        self.surface.fill(self.background_color)
        self.location_pointer += delta

        if self.location_pointer < 0 or self.location_pointer > self.space:
            if self.location_pointer < 0:
                spawn = self.right_spawn
            else:
                spawn = self.left_spawn

            loaded_image = pygame.image.load(self.image_location[rdm.randint(0, len(IMAGE_LIST) - 1)])
            zoom_factor = self.marker_height / loaded_image.get_height()
            if self.mirrored:
                _surf = [pygame.transform.rotozoom(loaded_image, 0, zoom_factor),
                         pygame.transform.flip(pygame.transform.rotozoom(loaded_image, 180, zoom_factor),
                                               True, False)]

                _rect = [_surf[0].get_rect(),
                         _surf[1].get_rect()]
                _rect[0].center = [spawn, self.parent.get_height() * 1 / 4]
                _rect[1].center = [spawn, self.parent.get_height() * 3 / 4]
                wobble_y_abs = int(self.parent.get_height() / 4 - _rect[0].height / 2)
                wobble_y_random = rdm.randint(-wobble_y_abs, wobble_y_abs)
            else:
                _surf = pygame.transform.rotozoom(loaded_image, 0, zoom_factor)
                _rect = _surf.get_rect()
                _rect.center = [spawn, self.parent.get_height() * 2 / 4]
                wobble_y_abs = int(self.parent.get_height() / 2)
                wobble_y_random = rdm.randint(-wobble_y_abs, wobble_y_abs)

            wobble_x_abs = int(self.space / 3)
            wobble_x_random = rdm.randint(-wobble_x_abs, wobble_x_abs)

            if self.mirrored:
                _rect = (_rect[0].move(wobble_x_random, wobble_y_random),
                         _rect[1].move(wobble_x_random, -wobble_y_random))
                new_marker = [[_surf[0], _rect[0]], [_surf[1], _rect[1]]]
            else:
                _rect = _rect.move(wobble_x_random, wobble_y_random)
                new_marker = [_surf, _rect]

            if self.location_pointer < 0:
                self.markers.append(new_marker)
                print("append right")
            else:
                self.markers.appendleft(new_marker)
                print("append left")

            self.location_pointer = self.location_pointer % self.space

        for i in range(0, len(self.markers)):
            if self.mirrored:
                self.markers[i][0][1] = self.markers[i][0][1].move(delta, 0)
                self.markers[i][1][1] = self.markers[i][1][1].move(delta, 0)
                self.surface.blit(*self.markers[i][0])
                self.surface.blit(*self.markers[i][1])
            else:
                self.markers[i][1] = self.markers[i][1].move(delta, 0)
                self.surface.blit(*self.markers[i])

    def blit_to_parent(self):
        self.parent.blit(self.surface, self.rectangle)
