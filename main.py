import pyglet
from pyglet.gl import *
import cv2
import numpy as np

# --- Constants ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
ROOM_SIZE = 10

class MainWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_minimum_size(320, 240)
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            raise IOError("Cannot open webcam")

        self.setup_gl()

        self.texture = None
        self.rotation_x = 0
        self.rotation_y = 0

        pyglet.clock.schedule_interval(self.update, 1/60.0)

    def setup_gl(self):
        """Set up OpenGL."""
        glEnable(GL_DEPTH_TEST)
        # glEnable(GL_TEXTURE_2D) # This will be enabled when the texture is bound
        glClearColor(0.1, 0.1, 0.1, 1.0)

    def on_draw(self):
        """Drawing event."""
        self.clear()
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65, self.width / self.height, 0.1, 100)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, -2, -ROOM_SIZE * 1.5)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)

        self.update_texture()
        if self.texture:
            glEnable(self.texture.target)
            glBindTexture(self.texture.target, self.texture.id)

        self.draw_room()

        if self.texture:
            glDisable(self.texture.target)

    def update(self, dt):
        """Update logic."""
        self.rotation_y += dt * 10

    def update_texture(self):
        """Capture frame from webcam and update texture."""
        ret, frame = self.camera.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            image_data = pyglet.image.ImageData(
                frame_rgb.shape[1], frame_rgb.shape[0], 
                'RGB', frame_rgb.tobytes(), pitch=-frame_rgb.shape[1] * 3
            )
            
            if self.texture is None:
                self.texture = image_data.get_texture(rectangle=True)
                glTexParameteri(self.texture.target, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(self.texture.target, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            else:
                self.texture.blit_into(image_data, 0, 0, 0)

    def draw_room(self):
        """Draw the 3D room."""
        s = ROOM_SIZE / 2.0
        
        glBegin(GL_QUADS)

        # Floor
        glColor3f(0.5, 0.5, 0.5)
        glVertex3f(-s, -s, -s); glVertex3f(s, -s, -s); glVertex3f(s, -s, s); glVertex3f(-s, -s, s)

        # Ceiling
        glColor3f(0.8, 0.8, 0.8)
        glVertex3f(-s, s, -s); glVertex3f(s, s, -s); glVertex3f(s, s, s); glVertex3f(-s, s, s)
        
        # Back wall (webcam)
        glColor3f(1.0, 1.0, 1.0)
        if self.texture:
            w = self.texture.width
            h = self.texture.height
            glTexCoord2f(0, 0); glVertex3f(-s, -s, -s)
            glTexCoord2f(w, 0); glVertex3f(s, -s, -s)
            glTexCoord2f(w, h); glVertex3f(s, s, -s)
            glTexCoord2f(0, h); glVertex3f(-s, s, -s)
        else:
            glVertex3f(-s, -s, -s); glVertex3f(s, -s, -s); glVertex3f(s, s, -s); glVertex3f(-s, s, -s)

        # Right wall
        glColor3f(0.6, 0.6, 0.6)
        glVertex3f(s, -s, -s); glVertex3f(s, -s, s); glVertex3f(s, s, s); glVertex3f(s, s, -s)
        
        # Left wall
        glColor3f(0.6, 0.6, 0.6)
        glVertex3f(-s, -s, -s); glVertex3f(-s, -s, s); glVertex3f(-s, s, s); glVertex3f(-s, s, -s)

        glEnd()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Handle mouse drag to rotate the room."""
        if buttons & pyglet.window.mouse.LEFT:
            self.rotation_y += dx * 0.5
            self.rotation_x -= dy * 0.5

    def on_close(self):
        self.camera.release()
        self.close()

if __name__ == '__main__':
    window = MainWindow(width=WINDOW_WIDTH, height=WINDOW_HEIGHT, caption='3D Webcam Room', resizable=True)
    pyglet.app.run()
