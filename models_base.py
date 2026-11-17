"""The first sample models: bus, lorry, trains of the normal railway, temperate houses, factory, station and stops."""

import math

from gfx3d import Model


def bus():
    m = Model()
    length, width = 9.0, 3.2
    x0, x1, y0, y1 = -length / 2, length / 2, -width / 2, width / 2
    m.box("dark", x0 + 0.1, x1 - 0.1, y0 + 0.15, y1 - 0.15, 0.45, 0.8)  # underside
    m.box("company", x0, x1, y0, y1, 0.8, 2.0)  # lower body
    m.box("glass", x0 + 0.08, x1 - 0.08, y0 + 0.08, y1 - 0.08, 2.0, 3.0)  # windows
    m.box("roof", x0, x1, y0, y1, 3.0, 3.3)
    m.box("roof", x0 + 0.5, x1 - 0.5, y0 + 0.4, y1 - 0.4, 3.3, 3.42)
    # Pillars between the windows, and the corners.
    for i in range(7):
        x = x0 + i * (length - 0.3) / 6
        for y in (y0, y1 - 0.12):
            m.box("company", x, x + 0.3, y, y + 0.12, 2.0, 3.0)
    for y in (y0, y1 - 0.3):
        m.box("company", x0, x0 + 0.12, y, y + 0.3, 2.0, 3.0)
        m.box("company", x1 - 0.12, x1, y, y + 0.3, 2.0, 3.0)
    m.box("company_dark", x0, x0 + 0.12, y0, y1, 2.0, 2.3)  # below the rear window
    # Bumpers and lights.
    m.box("dark", x1, x1 + 0.15, y0, y1, 0.7, 1.05)
    m.box("dark", x0 - 0.15, x0, y0, y1, 0.7, 1.05)
    for y in (y0 + 0.2, y1 - 0.7):
        m.box("light", x1, x1 + 0.06, y, y + 0.5, 1.2, 1.55)
    for x in (-2.7, 2.7):
        for y in (y0 + 0.2, y1 - 0.2):
            m.wheel(x, y, 0.62, 0.45)
    m.save("bus.glb")


def lorry():
    m = Model()
    length, width = 9.0, 3.1
    x0, x1, y0, y1 = -length / 2, length / 2, -width / 2, width / 2
    m.box("dark", x0, x1 - 0.1, y0 + 0.3, y1 - 0.3, 0.55, 1.0)  # chassis
    # Cab.
    m.box("company", x1 - 2.2, x1, y0, y1, 0.8, 1.9)
    m.box("glass", x1 - 2.1, x1 - 0.06, y0 + 0.06, y1 - 0.06, 1.9, 2.75)
    m.box("company", x1 - 2.2, x1, y0, y1, 2.75, 2.95)
    m.box("company", x1 - 2.2, x1 - 1.9, y0, y1, 1.9, 2.75)  # back of the cab
    for y in (y0, y1 - 0.14):
        m.box("company", x1 - 0.14, x1, y, y + 0.14, 1.9, 2.75)
    m.box("dark", x1, x1 + 0.15, y0, y1, 0.7, 1.05)
    for y in (y0 + 0.2, y1 - 0.7):
        m.box("light", x1, x1 + 0.06, y, y + 0.5, 1.2, 1.5)
    # Load.
    m.box("cargo", x0, x1 - 2.5, y0, y1, 1.0, 3.3)
    m.box("cargo_dark", x0 - 0.04, x0, y0 + 0.2, y1 - 0.2, 1.2, 3.1)  # doors
    for x in (-3.0, -1.6, 3.0):
        for y in (y0 + 0.2, y1 - 0.2):
            m.wheel(x, y, 0.62, 0.45)
    m.save("lorry.glb")


# Rail vehicles of the usual length are 8 long, half a tile; the models are a little shorter so that
# there is a gap between them. The rails are about 2.4 apart, the floor of a carriage is at about 1.


def rail_wheels(m, xs, radius=0.5):
    for x in xs:
        for y in (-1.2, 1.2):
            m.wheel(x, y, radius, 0.25)


def bogie(m, x):
    m.box("dark", x - 1.1, x + 1.1, -1.05, 1.05, 0.35, 0.8)
    rail_wheels(m, (x - 0.6, x + 0.6), 0.42)


def buffers(m, x0, x1, z=1.05):
    for x, d in ((x0, -0.35), (x1, 0.35)):
        m.box("dark", min(x, x + d), max(x, x + d), -1.5, 1.5, z - 0.25, z + 0.25)
        for y in (-1.0, 1.0):
            m.box("metal", min(x + d, x + 1.6 * d), max(x + d, x + 1.6 * d), y - 0.18, y + 0.18, z - 0.18, z + 0.18)


def steam_engine():
    """A tank engine: boiler in front, cab at the back, three coupled driving wheels."""
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("dark", x0, x1, -1.45, 1.45, 0.9, 1.25)  # running board
    m.box("dark", x0 + 0.3, x1 - 0.3, -0.8, 0.8, 0.45, 0.9)  # frame
    m.cylinder("company", -0.4, 3.0, 0, 2.05, 0.95, caps="boiler")
    m.cylinder("boiler", 3.0, 3.6, 0, 2.05, 1.0)  # smokebox
    for x in (0.4, 1.6):
        m.cylinder("brass", x - 0.08, x + 0.08, 0, 2.05, 0.98)  # bands
    m.chimney("boiler", 3.15, 0, 2.6, 3.9, 0.32)
    m.chimney("brass", 1.3, 0, 2.6, 3.35, 0.38)  # dome
    # Side tanks along the boiler.
    for y0, y1 in ((-1.4, -0.75), (0.75, 1.4)):
        m.box("company_dark", 0.0, 2.4, y0, y1, 1.25, 2.4)
    # Cab and coal bunker.
    m.box("company", -2.6, -0.4, -1.45, 1.45, 1.25, 3.1)
    m.box("glass", -1.6, -0.6, -1.5, 1.5, 2.2, 2.9)
    m.box("glass", -0.45, -0.35, -1.0, -0.4, 2.3, 2.9)
    m.box("glass", -0.45, -0.35, 0.4, 1.0, 2.3, 2.9)
    m.box("roof", -2.8, -0.2, -1.55, 1.55, 3.1, 3.35)
    m.box("company_dark", x0, -2.6, -1.3, 1.3, 1.25, 2.4)
    m.box("boiler", x0 + 0.1, -2.7, -1.1, 1.1, 2.4, 2.65)  # coal
    m.box("light", x1, x1 + 0.08, -0.25, 0.25, 2.5, 2.9)
    rail_wheels(m, (-2.9,), 0.45)
    rail_wheels(m, (-1.5, 0.0, 1.5), 0.68)
    rail_wheels(m, (3.0,), 0.45)
    # Rods joining the driving wheels.
    for y in (-1.36, 1.36):
        m.box("metal", -1.5, 1.5, y - 0.04, y + 0.04, 0.6, 0.72)
    buffers(m, x0, x1)
    m.save("steam_engine.glb")


def diesel_engine(electric=False):
    """A diesel with a cab at each end; with electric, a pantograph on the roof."""
    m = Model()
    x0, x1 = -3.8, 3.8
    m.box("dark", x0, x1, -1.4, 1.4, 0.85, 1.15)  # frame
    m.box("company", x0 + 0.1, x1 - 0.1, -1.45, 1.45, 1.15, 3.2)
    m.box("company_dark", x0 + 0.1, x1 - 0.1, -1.47, 1.47, 1.15, 1.6)  # stripe at the bottom
    m.box("roof", x0 + 0.3, x1 - 0.3, -1.25, 1.25, 3.2, 3.5)
    for x, d in ((x0 + 0.1, -1), (x1 - 0.1, 1)):
        m.box("glass", min(x, x + 0.06 * d), max(x, x + 0.06 * d), -1.2, 1.2, 2.3, 2.95)  # windscreen
        m.box("glass", min(x, x - 0.9 * d), max(x, x - 0.9 * d), -1.5, 1.5, 2.3, 2.9)  # side windows of the cab
        m.box("light", min(x, x + 0.08 * d), max(x, x + 0.08 * d), -1.0, -0.6, 1.5, 1.8)
        m.box("light", min(x, x + 0.08 * d), max(x, x + 0.08 * d), 0.6, 1.0, 1.5, 1.8)
    # Grilles along the engine room.
    for i in range(5):
        x = -1.9 + i * 0.85
        m.box("dark", x, x + 0.5, -1.5, 1.5, 2.4, 2.9)
    if electric:
        m.box("dark", -0.6, 0.6, -0.6, 0.6, 3.5, 3.65)
        m.quad("metal", (-0.5, -0.5, 3.65), (0.5, -0.5, 3.65), (0.1, -0.5, 4.6), (-0.1, -0.5, 4.6))
        m.quad("metal", (0.5, 0.5, 3.65), (-0.5, 0.5, 3.65), (-0.1, 0.5, 4.6), (0.1, 0.5, 4.6))
        m.box("metal", -0.12, 0.12, -0.9, 0.9, 4.55, 4.7)
    else:
        m.chimney("dark", 0.5, 0, 3.5, 3.8, 0.2)  # exhaust
    bogie(m, -2.4)
    bogie(m, 2.4)
    buffers(m, x0, x1)
    m.save("electric_engine.glb" if electric else "diesel_engine.glb")


def carriage(m, x0, x1, cab=False):
    """The body of a passenger carriage, with a row of windows."""
    m.box("dark", x0 + 0.2, x1 - 0.2, -1.3, 1.3, 0.85, 1.1)
    m.box("company", x0, x1, -1.45, 1.45, 1.1, 2.1)
    m.box("glass", x0 + 0.05, x1 - 0.05, -1.43, 1.43, 2.1, 2.8)
    m.box("company", x0, x1, -1.45, 1.45, 2.8, 3.1)
    # Pillars between the windows.
    count = 7
    for i in range(count + 1):
        x = x0 + i * (x1 - x0 - 0.25) / count
        m.box("company", x, x + 0.25, -1.45, 1.45, 2.1, 2.8)
    m.prism_roof("roof", "roof", x0, x1, -1.45, 1.45, 3.1, 3.55)
    if cab:
        m.box("glass", x1, x1 + 0.06, -1.1, 1.1, 2.15, 2.75)
        m.box("light", x1, x1 + 0.08, -1.0, -0.6, 1.4, 1.7)
        m.box("light", x1, x1 + 0.08, 0.6, 1.0, 1.4, 1.7)


def passenger_carriage():
    m = Model()
    carriage(m, -3.7, 3.7)
    bogie(m, -2.5)
    bogie(m, 2.5)
    buffers(m, -3.7, 3.7)
    m.save("passenger_carriage.glb")


def railcar():
    """A diesel railcar: a carriage with a driving cab at the front."""
    m = Model()
    carriage(m, -3.7, 3.7, cab=True)
    m.box("dark", -1.2, 1.2, -1.0, 1.0, 0.45, 0.85)  # engine below the floor
    bogie(m, -2.5)
    bogie(m, 2.5)
    buffers(m, -3.7, 3.7)
    m.save("railcar.glb")


def van(material, filename, doors="company_dark", vents=False):
    """A covered goods van with a curved roof and sliding doors."""
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("dark", x0, x1, -1.3, 1.3, 0.85, 1.1)
    m.box(material, x0 + 0.1, x1 - 0.1, -1.4, 1.4, 1.1, 3.0)
    m.prism_roof("roof", material, x0, x1, -1.5, 1.5, 3.0, 3.4)
    m.box(doors, -0.8, 0.8, -1.46, 1.46, 1.2, 2.85)
    if vents:
        for x in (-2.6, -1.8, 1.8, 2.6):
            m.box("dark", x - 0.25, x + 0.25, -1.45, 1.45, 2.4, 2.8)
    # The company's colour as a stripe.
    m.box("company", x0 + 0.1, x1 - 0.1, -1.42, 1.42, 1.1, 1.3)
    rail_wheels(m, (-2.2, 2.2))
    buffers(m, x0, x1)
    m.save(filename)


def open_wagon():
    """An open wagon with low sides, for coal, wood and steel."""
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("dark", x0, x1, -1.3, 1.3, 0.85, 1.1)
    m.box("rust", x0 + 0.1, x1 - 0.1, -1.4, 1.4, 1.1, 1.3)  # floor
    for y0, y1 in ((-1.4, -1.25), (1.25, 1.4)):
        m.box("company_dark", x0 + 0.1, x1 - 0.1, y0, y1, 1.3, 2.3)
    for xa, xb in ((x0 + 0.1, x0 + 0.25), (x1 - 0.25, x1 - 0.1)):
        m.box("company_dark", xa, xb, -1.25, 1.25, 1.3, 2.3)
    for x in (-2.0, 0.0, 2.0):
        for y in (-1.45, 1.4):
            m.box("dark", x - 0.1, x + 0.1, y, y + 0.05, 1.3, 2.3)  # ribs
    # The load: a heap that fills the wagon.
    m.box("load_coal", x0 + 0.25, x1 - 0.25, -1.25, 1.25, 1.3, 2.2)
    m.prism_roof("load_coal", "load_coal", x0 + 0.25, x1 - 0.25, -1.25, 1.25, 2.2, 2.7)
    rail_wheels(m, (-2.2, 2.2))
    buffers(m, x0, x1)
    m.save("open_wagon.glb")


def hopper():
    """A hopper wagon for grain and ore, with sloping ends and chutes below."""
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("dark", x0, x1, -1.2, 1.2, 0.85, 1.1)
    # Open at the top: sides, a floor below the load, and sloping ends.
    m.box("company_dark", x0 + 0.6, x1 - 0.6, -1.4, -1.25, 1.1, 2.9)
    m.box("company_dark", x0 + 0.6, x1 - 0.6, 1.25, 1.4, 1.1, 2.9)
    m.box("company_dark", x0 + 0.6, x1 - 0.6, -1.25, 1.25, 1.1, 1.5)
    # Sloping ends.
    for xa, xb in ((x0 + 0.1, x0 + 0.6), (x1 - 0.6, x1 - 0.1)):
        top_out, bottom_in = (xa, xb) if xa < 0 else (xb, xa)
        m.quad("company_dark", (top_out, -1.4, 2.9), (bottom_in, -1.4, 1.4), (bottom_in, 1.4, 1.4), (top_out, 1.4, 2.9))
        m.quad("company_dark", (top_out, 1.4, 2.9), (bottom_in, 1.4, 1.4), (bottom_in, -1.4, 1.4), (top_out, -1.4, 2.9))
    m.box("dark", x0 + 0.6, x1 - 0.6, -1.42, 1.42, 2.75, 2.95)  # top edge
    m.box("load_ore", x0 + 0.7, x1 - 0.7, -1.3, 1.3, 2.2, 2.9)  # the load
    m.prism_roof("load_ore", "load_ore", x0 + 0.7, x1 - 0.7, -1.3, 1.3, 2.9, 3.3)
    for x in (-1.0, 1.0):
        m.box("dark", x - 0.4, x + 0.4, -0.6, 0.6, 0.6, 1.1)  # chutes
    rail_wheels(m, (-2.6, 2.6))
    buffers(m, x0, x1)
    m.save("hopper.glb")


def tanker():
    """A tank wagon."""
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("dark", x0, x1, -1.2, 1.2, 0.85, 1.25)
    m.cylinder("boiler", x0 + 0.2, x1 - 0.2, 0, 2.2, 1.05, sides=16)
    m.cylinder("company", -0.15, 0.15, 0, 2.2, 1.08, sides=16)  # band in the company colour
    m.chimney("boiler", 0, 0, 3.0, 3.45, 0.4)  # filler
    for x in (-2.0, 2.0):
        m.box("dark", x - 0.1, x + 0.1, -1.15, 1.15, 1.2, 1.6)  # cradles
    rail_wheels(m, (-2.3, 2.3))
    buffers(m, x0, x1)
    m.save("tanker.glb")


# Buildings stand on a whole tile, 16 by 16, with the middle of the tile at the origin.
# Heights: one storey is about 3.3, which is how high the 2D game draws one floor.


def house():
    """A small house with a pitched roof; the walls take the colour of the house."""
    m = Model()
    m.box("company", -5, 5, -4, 4, 0, 4.6)
    m.box("concrete", -5.2, 5.2, -4.2, 4.2, 0, 0.4)
    m.prism_roof("tiles", "company", -5.6, 5.6, -4.7, 4.7, 4.6, 8.2)
    m.box("brick", 2.2, 3.2, -1.8, -0.8, 6.0, 9.0)  # chimney
    m.windows("glass", -5, 5, -4, 4, 0.6, 4.4, 2, 3, size=(1.1, 1.2))
    m.box("door", 4.98, 5.1, -0.6, 0.6, 0.3, 2.3)
    m.box("grass", -7, 7, -7, 7, 0, 0.05)
    m.save("house.glb")


def flats():
    """A block of flats of three storeys with a flat roof."""
    m = Model()
    m.box("company", -6, 6, -6, 6, 0, 10)
    m.box("concrete", -6.2, 6.2, -6.2, 6.2, 10, 10.6)
    m.box("metal", -2, 1, -1.5, 1.5, 10.6, 11.8)  # roof housing
    m.windows("glass", -6, 6, -6, 6, 0.4, 10, 3, 4, size=(1.6, 1.6))
    for z in (3.3, 6.6):
        m.box("concrete", -6.1, 6.1, -6.1, 6.1, z - 0.15, z + 0.15)
    m.save("flats.glb")


def office_tower():
    """A tall office tower with bands of windows."""
    m = Model()
    m.box("concrete", -5, 5, -5, 5, 0, 1.2)
    m.box("glass", -4.5, 4.5, -4.5, 4.5, 1.2, 26)
    for i in range(8):
        z = 1.2 + 3.1 * (i + 1)
        m.box("company", -4.7, 4.7, -4.7, 4.7, z - 0.5, z)
    for x in (-4.7, 4.1):
        for y in (-4.7, 4.1):
            m.box("company", x, x + 0.6, y, y + 0.6, 1.2, 26)
    m.box("concrete", -4.8, 4.8, -4.8, 4.8, 26, 26.6)
    m.box("metal", -1.5, 1.5, -1.5, 1.5, 26.6, 28.5)
    m.save("office_tower.glb")


def shops():
    """Shops on the ground floor with offices above, and an awning in the colour of the shop."""
    m = Model()
    m.box("brick", -6, 6, -5.5, 5.5, 0, 7)
    m.box("glass", -6.08, 6.08, -5.58, 5.58, 0.4, 2.8)  # shop windows
    m.box("brick", -6.1, 6.1, -5.6, 5.6, 2.8, 3.3)
    m.windows("glass", -6, 6, -5.5, 5.5, 3.3, 7, 1, 4, size=(1.3, 1.6))
    m.box("concrete", -6.2, 6.2, -5.7, 5.7, 7, 7.5)
    for (x0, x1, y0, y1) in ((6.1, 7.6, -5.5, 5.5), (-6, 6, -7.1, -5.6)):
        m.box("company", x0, x1, y0, y1, 2.9, 3.2)
    m.save("shops.glb")


def church():
    """A church with a nave and a tower with a spire."""
    m = Model()
    m.box("stone", -6, 4, -3.5, 3.5, 0, 6)
    m.prism_roof("slate", "stone", -6.3, 4.3, -4, 4, 6, 9.5)
    m.box("stone", 4, 7.5, -1.75, 1.75, 0, 14)
    m.pyramid("slate", 3.8, 7.7, -1.95, 1.95, 14, 21)
    for x in (-4.5, -2, 0.5, 3):
        for y in (-3.58, 3.5):
            m.box("glass", x - 0.4, x + 0.4, y, y + 0.08, 2, 5)
    m.box("door", 7.5, 7.6, -0.6, 0.6, 0, 2.6)
    m.box("grass", -7.5, 7.8, -7, 7, 0, 0.05)
    m.save("church.glb")


def factory_hall():
    """One tile of a factory hall with a sawtooth roof; several of them make the factory."""
    m = Model()
    m.box("brick", -8, 8, -8, 8, 0, 6)
    for i in range(4):
        y0 = -8 + i * 4
        m.quad("slate", (-8, y0, 6), (8, y0, 6), (8, y0 + 4, 8.5), (-8, y0 + 4, 8.5))
        m.quad("glass", (8, y0 + 4, 6), (-8, y0 + 4, 6), (-8, y0 + 4, 8.5), (8, y0 + 4, 8.5))
        m.triangle("brick", (8, y0, 6), (8, y0 + 4, 6), (8, y0 + 4, 8.5))
        m.triangle("brick", (-8, y0 + 4, 6), (-8, y0, 6), (-8, y0 + 4, 8.5))
    m.windows("glass", -8, 8, -8, 8, 1, 5, 1, 4, size=(2.2, 2.4))
    m.save("factory_hall.glb")


def factory_chimney():
    """A factory tile with a lower building and a tall chimney."""
    m = Model()
    m.box("brick", -8, 8, -8, 2, 0, 6)
    m.prism_roof("slate", "brick", -8, 8, -8, 2, 6, 8)
    m.box("concrete", -8, 8, 2, 8, 0, 0.2)
    m.box("brick", 3, 6, 3, 6, 0, 22)
    m.box("dark", 2.8, 6.2, 2.8, 6.2, 21, 22.2)
    m.box("company", 2.9, 6.1, 2.9, 6.1, 16, 17)
    m.windows("glass", -8, 8, -8, 2, 1, 5, 1, 4, size=(2.0, 2.4))
    m.save("factory_chimney.glb")


def platforms(m, building=False):
    """Two platforms along a track that runs front to back; the building side is on the right (negative y)."""
    m.box("platform", -8, 8, -8, -3, 0, 0.9)
    m.box("edge", -8, 8, -3.3, -3, 0.9, 0.95)
    m.box("platform", -8, 8, 3, 8, 0, 0.9)
    m.box("edge", -8, 8, 3, 3.3, 0.9, 0.95)
    if building:
        m.box("wall", -7, 7, -8, -4.4, 0.9, 5.4)
        m.box("company", -7.3, 7.3, -8.2, -4.1, 5.4, 6.0)
        m.box("glass", -6, 6, -4.48, -4.4, 1.6, 4.4)
        m.box("door", -0.8, 0.8, -4.45, -4.35, 0.9, 3.4)


def station_platform():
    m = Model()
    platforms(m)
    for x in (-5, 5):
        for y in (-5.5, 5.5):
            m.box("metal", x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0.9, 2.8)
            m.box("company", x - 0.5, x + 0.5, y - 0.05, y + 0.05, 2.3, 2.8)
    m.save("station_platform.glb")


def station_building():
    m = Model()
    platforms(m, building=True)
    m.box("company", -6, 6, 6.8, 7.0, 0.9, 1.0)
    m.save("station_building.glb")


def station_roof():
    m = Model()
    platforms(m)
    for x in (-6, 0, 6):
        for y in (-5.5, 5.5):
            m.box("company", x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0.9, 6.5)
    m.box("company", -8, 8, -8.2, 8.2, 6.5, 6.9)
    m.prism_roof("glass", "company", -8, 8, -8.2, 8.2, 6.9, 8.6)
    m.save("station_roof.glb")


def bus_stop(drive_through=False):
    """A bus shelter. A stop off the road has its front towards the road; one on the road has the road front to back."""
    m = Model()

    def shelter(x0, x1, y0, y1, open_side):
        m.box("concrete", x0, x1, y0, y1, 0, 0.3)
        m.box("company", x0, x1, y0, y1, 3.2, 3.5)
        for (px, py) in ((x0, y0), (x1 - 0.2, y0), (x0, y1 - 0.2), (x1 - 0.2, y1 - 0.2)):
            m.box("metal", px, px + 0.2, py, py + 0.2, 0.3, 3.2)
        if open_side != "back":
            m.box("glass", x0, x0 + 0.1, y0, y1, 0.6, 3.0)
        m.box("dark", (x0 + x1) / 2 - 0.15, (x0 + x1) / 2 + 0.15, y0 + 0.4, y1 - 0.4, 0.3, 1.0)
        m.box("company", (x0 + x1) / 2 - 0.1, (x0 + x1) / 2 + 0.1, y1 + 0.2, y1 + 0.4, 0, 4.4)

    if drive_through:
        shelter(-3, 0, -7.6, -6, "side")
        shelter(0, 3, 6, 7.6, "side")
    else:
        m.box("concrete", -8, -4, -8, 8, 0, 0.25)
        shelter(-7.6, -5.6, -5, 5, "front")
    m.save("bus_stop_drive_through.glb" if drive_through else "bus_stop.glb")


def lorry_stop(drive_through=False):
    """A loading bay with a canopy over the place where lorries stop."""
    m = Model()
    if drive_through:
        for y in (-7.4, 7.0):
            for x in (-6, 6):
                m.box("metal", x - 0.2, x + 0.2, y, y + 0.4, 0, 6)
        m.box("company", -7, 7, -7.6, 7.6, 6, 6.5)
    else:
        m.box("concrete", -8, -4.5, -8, 8, 0, 1.4)  # loading dock
        m.box("cargo", -8, -6, -7, 7, 1.4, 4.0)
        for y in (-7.4, 7.0):
            m.box("metal", 5.4, 5.8, y, y + 0.4, 0, 6)
        m.box("company", -8, 6.5, -7.6, 7.6, 6, 6.5)
    m.save("lorry_stop_drive_through.glb" if drive_through else "lorry_stop.glb")


def build():
    bus()
    lorry()
    steam_engine()
    diesel_engine()
    diesel_engine(electric=True)
    passenger_carriage()
    railcar()
    van("company_dark", "mail_van.glb", doors="dark")
    van("wood", "goods_van.glb", vents=True)
    open_wagon()
    hopper()
    tanker()
    house()
    flats()
    office_tower()
    shops()
    church()
    factory_hall()
    factory_chimney()
    station_platform()
    station_building()
    station_roof()
    bus_stop()
    bus_stop(drive_through=True)
    lorry_stop()
    lorry_stop(drive_through=True)
    return {
        "vehicles": [
            {
                "type": "road",
                "ids": [
                    0,
                    1,
                    2,
                    3
                ],
                "model": "bus.glb"
            },
            {
                "type": "road",
                "ids": [
                    7,
                    8,
                    9,
                    10,
                    11,
                    12
                ],
                "model": "lorry.glb"
            },
            {
                "type": "train",
                "ids": [
                    0,
                    2,
                    3,
                    4,
                    7,
                    8,
                    9,
                    10
                ],
                "model": "steam_engine.glb"
            },
            {
                "type": "train",
                "ids": [
                    1,
                    5,
                    6,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    21
                ],
                "model": "diesel_engine.glb"
            },
            {
                "type": "train",
                "ids": [
                    23,
                    24
                ],
                "model": "electric_engine.glb"
            },
            {
                "type": "train",
                "ids": [
                    11,
                    12
                ],
                "model": "railcar.glb"
            },
            {
                "type": "train",
                "ids": [
                    27
                ],
                "model": "passenger_carriage.glb"
            },
            {
                "type": "train",
                "ids": [
                    28
                ],
                "model": "mail_van.glb"
            },
            {
                "type": "train",
                "ids": [
                    31,
                    32,
                    37,
                    38,
                    39,
                    42,
                    47,
                    49,
                    50,
                    52
                ],
                "model": "goods_van.glb"
            },
            {
                "type": "train",
                "ids": [
                    29,
                    34,
                    36,
                    43,
                    44,
                    51,
                    53
                ],
                "model": "open_wagon.glb"
            },
            {
                "type": "train",
                "ids": [
                    33,
                    35,
                    40,
                    45,
                    46
                ],
                "model": "hopper.glb"
            },
            {
                "type": "train",
                "ids": [
                    30,
                    41,
                    48
                ],
                "model": "tanker.glb"
            }
        ],
        "buildings": [
            {
                "type": "house",
                "ids": [
                    6,
                    24,
                    25,
                    26
                ],
                "model": "house.glb"
            },
            {
                "type": "house",
                "ids": [
                    1,
                    2,
                    13,
                    19,
                    27,
                    36
                ],
                "model": "flats.glb"
            },
            {
                "type": "house",
                "ids": [
                    0,
                    4,
                    17,
                    28
                ],
                "model": "office_tower.glb"
            },
            {
                "type": "house",
                "ids": [
                    14,
                    15,
                    16,
                    29,
                    30
                ],
                "model": "shops.glb"
            },
            {
                "type": "house",
                "ids": [
                    3
                ],
                "model": "church.glb"
            },
            {
                "type": "industry_tile",
                "ids": [
                    39,
                    40,
                    41
                ],
                "model": "factory_hall.glb"
            },
            {
                "type": "industry_tile",
                "ids": [
                    42
                ],
                "model": "factory_chimney.glb"
            },
            {
                "type": "rail_station",
                "ids": [
                    0
                ],
                "model": "station_platform.glb"
            },
            {
                "type": "rail_station",
                "ids": [
                    1
                ],
                "model": "station_building.glb"
            },
            {
                "type": "rail_station",
                "ids": [
                    2,
                    3
                ],
                "model": "station_roof.glb"
            },
            {
                "type": "road_stop",
                "ids": [
                    0
                ],
                "model": "bus_stop.glb"
            },
            {
                "type": "road_stop",
                "ids": [
                    1
                ],
                "model": "lorry_stop.glb"
            },
            {
                "type": "road_stop",
                "ids": [
                    2
                ],
                "model": "bus_stop_drive_through.glb"
            },
            {
                "type": "road_stop",
                "ids": [
                    3
                ],
                "model": "lorry_stop_drive_through.glb"
            }
        ]
    }
