# OpenGFX3D

3D models for the experimental 3D view of the OpenTTD 3D fork (see `docs/viewport3d.md` there).
The 3D view draws a vehicle or a building with a model from this package when the package has one for it.
Everything else keeps the sprites of the 2D game, so the package can grow one model at a time.

The fork includes this repository as a git submodule at `bin/opengfx3d`.

All models here are made for this project; do not add models copied from elsewhere without checking their licence.

## Files

* `opengfx3d.json`: the index. It lists which model replaces which vehicles and buildings.
* `*.glb`: the models, as binary glTF 2.0 files.
* `make_models.py`: makes all the models and the index. Run it after changing a model.
* `gfx3d.py`: the toolkit the models are made with: materials and the `Model` class.
* `models_*.py`: the models, in groups (base, road, trains, ships, air, houses_north, houses_south, industry_temperate, industry_other, infra, land). Each has a `build()` that writes its models and returns its entries for the index. Each group names its .glb files and new materials with its own prefix. `make_models.py` stops when two groups give a model to the same thing.
* `ground_*.png`: the ground textures. Each repeats without a seam, and the game spreads it over several tiles.
* `make_textures.py`: makes the ground textures (needs numpy and Pillow). Run it, and then `make_models.py` to list them in the index.
* `tex_*.png`: the surface textures of the models: brickwork, roof tiles, planks, sheet metal, leaves and so on, in shades of grey. The models refer to them by file name, so all models share them.
* `make_model_textures.py`: makes the surface textures (needs numpy and Pillow). Run it, and then `make_models.py`.
* `preview.py`: draws pictures of models from the angle of the 2D game and from behind, to check them without the game (needs Pillow).
* `make_sprites.py`: draws 2D sprites of the power line models and packs them into `power.grf` for the 2D view of the game (needs numpy). Run `python3 make_sprites.py <game>/src/table/palettes.h -o <game>/media/baseset/power.grf` after changing `models_power.py`.

The build copies the package to `opengfx3d/` in the build folder. The game looks for a folder of that name in all places where it looks for its data, such as your personal OpenTTD folder.

## The ground textures

```json
"ground": { "tiles": 4, "textures": { "grass": "ground_grass.png", "soil": "ground_soil.png" } }
```

* `tiles`: along how many tiles the game spreads one texture.
* `textures`: the images by name. They must be square PNG files, all of the same size, a power of two.
  * `grass`, `soil`, `sand`, `water` and `mask` are needed; without them the game makes the ground from the sprites of the 2D game, as it does without this package.
  * `rough`, `rocks`, `snow`, `desert`, `asphalt`, `gravel` and `paving` are optional.
  * `sand` (the beach), `asphalt` (roads), `gravel` (beside tracks) and `paving` (pavements) are used as they are. The game tints all others to the average colour of the matching ground sprite of the 2D game, so only the differences in colour within the image matter.
  * `mask` is grey: where grass grows over soil first (dark) and last (light). The same goes for snow and desert over grass.

Like the models, the textures are made for this project: `make_textures.py` computes them from random numbers. Do not add photographs or textures from elsewhere without checking their licence.

## The index

```json
{
	"name": "OpenGFX3D",
	"vehicles": [
		{ "type": "road", "ids": [0, 1, 2, 3], "model": "bus.glb" },
		{ "type": "train", "grfid": "44440111", "ids": [12], "model": "engine.glb", "scale": 1.2 }
	],
	"buildings": [
		{ "type": "house", "ids": [6, 24, 25, 26], "model": "house.glb" },
		{ "type": "rail_station", "ids": [2, 3], "model": "station_roof.glb" }
	]
}
```

* `type`: for vehicles `train`, `road`, `ship` or `aircraft`; for buildings `house`, `industry_tile`, `rail_station`, `road_stop`, `object`, `airport_tile`, `dock`, `buoy`, `rail_depot`, `road_depot` or `ship_depot`; for the landscape `tree`, `field`, `rough` or `rocks`; for effects `effect`; for infrastructure `track`, `signal`, `catenary`, `fence`, `bridge`, `tunnel`, `crossing` or `roadside`; `construction` for building sites, `waypoint`, `lock` for canal locks and `disaster` for disaster vehicles; `interface` for the posts of labels and the parts of the cursor (see `models_interface.py`); `power` for pylons, substations and wires of power lines (see `models_power.py`).
* `grfid`: the ID of the NewGRF that defines the vehicles, as the eight hexadecimal digits the game shows for it. Leave it out for the vehicles of the base game.
* `ids`: the numbers within that NewGRF. For the base game:
  * vehicles count from 0 per type, in the order of `src/table/engines.h`: road vehicle 0 is the MPS Regal Bus;
  * `house`: the house type, as in `src/table/town_land.h`;
  * `industry_tile`: the industry tile type, as in `src/table/build_industry.h`;
  * `rail_station`: the station tile layout divided by two: 0 plain platform, 1 platform with building, 2 and 3 platform with roof;
  * `road_stop`: 0 bus bay, 1 lorry bay, 2 drive-through bus stop, 3 drive-through lorry stop;
  * `object`: the object type (0 transmitter, 1 lighthouse, 2 statue, 4 company headquarters);
  * `airport_tile`: the airport tile graphics, as in `src/table/airporttile_ids.h`;
  * `dock`: 0 the part on the slope, 1 the part on the water; it points from the land to the water like the other fronts;
  * `buoy`, `rail_depot`, `road_depot`: 0; depots have their door to +X;
  * `ship_depot`: 0, a model of both tiles, 32 long along X.
  * `tree`: the tree type, as in `src/tree_map.h` (0x00 temperate, 0x0C sub-arctic, 0x14 rainforest, 0x1B cactus, 0x1C sub-tropical, 0x20 toyland); sub-arctic trees above the snow line are the type + 0x40. One tree with its foot at the origin; the game puts up to four on a tile, turns each its own way and scales the growing ones.
  * `field`: the state of a farm field, 0 ploughed to 6 ripe, 7 harvested, 8 harvested with hay.
  * `rough`, `rocks`: versions 0 to 3; the game picks one for each tile and turns it by quarter turns. Fields, rough land and rocks cover the tile (16 x 16) and are tilted along its slope.
  * Infrastructure: the ids are described at the top of `models_track.py` (`track`, `signal`, `catenary`), `models_fences.py` (`fence`), `models_bridges.py` (`bridge`, `tunnel`, `crossing`) and `models_roadside.py` (`roadside`).
  * Building sites, waypoints, canal locks, disasters and the road works bulldozer: the ids are described at the top of `models_works.py`.
* `model`: a file in this folder.
* `scale`: optional; world units per unit of the model.
* `rotor`, `rotor_at`: optional, for helicopters; the model of the main rotor, which the game turns, and where its hub is in the frame of the helicopter.
* `far`: optional; a simpler model to draw far from the camera, or "" to leave the model out there (small details).
* `snow`: optional, for industry tiles; the model to use in the sub-arctic climate, where the 2D game draws the tile with snow (forests).
* `parts`: optional, for buildings; parts that move, each `{ "model": ..., "at": [x, y, z], "axis": [x, y, z], "spin": radians per second, "swing": radians, "period": seconds, "lift": world units }`. The part turns around `axis` through `at` (in the frame of the building), by `spin` all the time and back and forth by `swing`, and moves `lift` along `axis` and back once per `period` (a press, rising bubbles). Draw the part with the point it turns around at its origin. Give the ids of a tile that is animated in the game an entry of their own when only those should move.

## Models

* Binary glTF 2.0 (`.glb`), as exported by Blender and other programs, with the data inside the file.
* The front points to +Z, up is +Y. The ground is at height 0 and the middle of the vehicle or building is at the origin.
* One unit is one sixteenth of a tile. A road vehicle is about 9 long, 3 wide and 3.5 high; a one-tile building fits in 16 by 16.
* A building model covers its whole footprint (a 2 by 2 house is 32 by 32) and stands on the highest corner of it. On sloped ground the game adds a stone foundation under it.
* Fronts: houses, industry tiles and objects face the south-west edge of the map view. Stations and drive-through stops lie along their track or road; the side to -X is the side with the station building. Bay stops face their road.
* Triangles take the base colour of their material, multiplied with its base colour texture if it has one. Normal maps and other textures, animations and skins are not read.
* A texture is a PNG image, either inside the model or a file in this folder that the model names (`"uri": "tex_brick.png"`); models that name the same file share it. Textures always repeat, and only the first set of texture coordinates is read. The game brings all textures to one size, that of the largest (at most 1024 by 1024), so keep them square and of one size; it can hold 256 of them.
* A material with a name that starts with `company` takes a colour from the game, multiplied with its base colour: white becomes that colour, grey a darker shade of it. For vehicles, stations, stops and objects it is the owner's company colour; houses and industries use the colour the game picked for them.
* Triangles of a material with a name that starts with `load` are the cargo of a vehicle. They are drawn only when the vehicle carries cargo, and sink into the vehicle as it gets emptier, by up to their own height; so make the load as high as the part that should disappear, and let the sides of the vehicle hide it.
* Each wagon or part of a vehicle is drawn with the model of its own vehicle ID.
* Houses and industries are replaced only when they are finished; while being built they keep their sprites.

## The surface textures

The models made by `make_models.py` get their textures by the names of their materials: `TEXTURE_RULES` in `gfx3d.py` says which words in a name give which texture (`brick` gives brickwork, `roof` roof tiles, `company` painted sheet metal with seams and rivets). Materials that match no rule keep a plain colour.

The textures are grey and the game multiplies them with the colour of the material, so one texture serves all colours of brick, and the parts in company colour stay in company colour. `Model.save()` lays each texture flat on every surface at a fixed size (`TEXTURES` in `gfx3d.py`: world units per repeat) with its top pointing up the surface, so models need no texture coordinates of their own.

To give a material another surface, add a rule or name the material to match one; for a new kind of surface, add a function to `make_model_textures.py` and its name and size to `TEXTURES`.

Like the models, the textures are computed from random numbers; do not add photographs or textures from elsewhere without checking their licence.

## Licence

GPL-2.0, like OpenTTD (see `LICENSE`).
