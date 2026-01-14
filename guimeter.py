import tkinter as tk
from math import sin, cos, pi

# ---------------- Utilities ----------------

def colour_choice(colour):
    blued   = {'f':'#02fdf6','b':'#0031a7','g':'#0d4fdb','s':'#18a1ff'}
    oranged = {'f':'#fee737','b':'#7b0106','g':'#5E0B0B','s':'#fa0e20'}
    greend  = {'f':'#00F23C','b':'#002504','g':'#005914','s':'#84aea7'}
    purpled = {'f':'#F9F9FD','b':'#1D1739','g':'#3F1E4B','s':'#9493A1'}

    if colour == 'purple':
        d = purpled
    elif colour == 'blue':
        d = blued
    elif colour == 'green':
        d = greend
    else:
        d = oranged

    return d['b'], d['f'], d['g'], d['s']


def tk_arc(canvas, c, r, style, start, extent, outline, fill):
    return canvas.create_arc(
        [c[0]-r, c[1]-r, c[0]+r, c[1]+r],
        style=style, start=start, extent=extent,
        outline=outline, fill=fill
    )


def tk_tick(canvas, c, ri, length, angle, fill, width=1, tags=None):
    r = angle * pi / 180.0
    x0 = c[0] + ri * cos(r)
    y0 = c[1] + ri * sin(r)
    x1 = c[0] + (ri + length) * cos(r)
    y1 = c[1] + (ri + length) * sin(r)
    return canvas.create_line(x0, y0, x1, y1, fill=fill, width=width, tags=tags)


def tk_delta(canvas, angle, c, ro, e, fill):
    r = angle * pi / 180.0
    x0 = c[0] + ro * cos(r)
    y0 = c[1] + ro * sin(r)

    x1 = x0 + 2*e * sin(r)
    y1 = y0 - 2*e * cos(r)
    x2 = x0 - 2*e * sin(r)
    y2 = y0 + 2*e * cos(r)
    x3 = c[0] + (ro - 3*e) * cos(r)
    y3 = c[1] + (ro - 3*e) * sin(r)

    return canvas.create_polygon(x1,y1,x2,y2,x3,y3, fill=fill)


def tk_text(canvas, text, c, ro, angle, size, fill, tags=''):
    r = angle * pi / 180.0
    x = c[0] + ro * cos(r)
    y = c[1] + ro * sin(r)
    return canvas.create_text(x, y, text=text,
                              font=('Arial', size, 'italic'),
                              fill=fill, tags=tags)

# ---------------- Gauge Class ----------------

class Gauge(tk.Canvas):
    def __init__(self, master, size=300, colour='blue',
                 vmin=0, vmax=100, **kw):
        super().__init__(master, width=size, height=size,
                         bg='#111111', highlightthickness=0, **kw)

        self.size = size
        self.c = (size//2, size//2)
        self.r = size//2 - 10

        self.vmin = vmin
        self.vmax = vmax
        self.start = 135
        self.extent = 270

        self.bd, self.fd, self.gd, self.sd = colour_choice(colour)

        self._draw_static()
        self.value_text = None

    def _draw_static(self):
        # Bezel
        tk_arc(self, self.c, self.r, tk.PIESLICE,
               self.start-10, self.extent+20,
               outline=self.bd, fill=self.bd)

        tk_arc(self, self.c, self.r-12, tk.PIESLICE,
               self.start, self.extent,
               outline=self.gd, fill=self.gd)

        # Cleanup center
        self.create_oval(self.c[0]-self.r+40, self.c[1]-self.r+40,
                         self.c[0]+self.r-40, self.c[1]+self.r-40,
                         fill='#111111', outline='')

        # Ticks
        for i in range(0, 101, 5):
            angle = self.start + (i/100)*self.extent
            if i % 10 == 0:
                tk_tick(self, self.c, self.r-55, 18, angle,
                        self.sd, width=3)
                tk_text(self, str(i), self.c,
                        self.r-80, angle, 10, self.fd)
                tk_delta(self, angle, self.c, self.r-45, 4, self.fd)
            else:
                tk_tick(self, self.c, self.r-50, 10, angle,
                        self.fd, width=1)

    def set_value(self, value):
        self.delete('pointer')
        self.delete('value')

        value = max(self.vmin, min(self.vmax, value))
        angle = self.start + ((value-self.vmin) /
                               (self.vmax-self.vmin)) * self.extent

        # Pointer
        tk_tick(self, self.c, 0, self.r-60,
                angle, self.fd, width=4, tags='pointer')

        # Value text
        self.create_text(self.c[0], self.c[1]+40,
                         text=f'{int(value)}',
                         font=('Arial', 24, 'bold'),
                         fill=self.fd, tags='value')

# ---------------- Demo ----------------

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Tkinter Gauge Demo")

    gauge = Gauge(root, size=320, colour='blue')
    gauge.pack(padx=10, pady=10)

    def on_slide(v):
        gauge.set_value(float(v))

    slider = tk.Scale(root, from_=0, to=100,
                      orient='horizontal',
                      command=on_slide, length=300)
    slider.pack()

    slider.set(50)
    root.mainloop()
