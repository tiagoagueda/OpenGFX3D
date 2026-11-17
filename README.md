# OpenGFX3D

3D models for the experimental 3D view of the OpenTTD 3D fork (see `docs/viewport3d.md` there).
The 3D view draws a vehicle or a building with a model from this package when the package has one for it.
Everything else keeps the sprites of the 2D game, so the package can grow one model at a time.

The fork includes this repository as a git submodule at `bin/opengfx3d`.

All models here are made for this project; do not add models copied from elsewhere without checking their licence.

## Files

* `opengfx3d.json`: the index. It lists which model replaces which vehicles and buildings.
* `*.glb`: the models, as binary glTF 2.0 files.
* `make_models.py`: makes all the sample models from simple shapes (it needs only Python 3). Run it in this folder after changing it.

The build copies the package to `opengfx3d/` in the build folder. The game looks for a folder of that name in all places where it looks for its data, such as your personal OpenTTD folder.

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

* `type`: for vehicles `train`, `road`, `ship` or `aircraft`; for buildings `house`, `industry_tile`, `rail_station`, `road_stop` or `object`.
* `grfid`: the ID of the NewGRF that defines the vehicles, as the eight hexadecimal digits the game shows for it. Leave it out for the vehicles of the base game.
* `ids`: the numbers within that NewGRF. For the base game:
  * vehicles count from 0 per type, in the order of `src/table/engines.h`: road vehicle 0 is the MPS Regal Bus;
  * `house`: the house type, as in `src/table/town_land.h`;
  * `industry_tile`: the industry tile type, as in `src/table/build_industry.h`;
  * `rail_station`: the station tile layout divided by two: 0 plain platform, 1 platform with building, 2 and 3 platform with roof;
  * `road_stop`: 0 bus bay, 1 lorry bay, 2 drive-through bus stop, 3 drive-through lorry stop;
  * `object`: the object type.
* `model`: a file in this folder.
* `scale`: optional; world units per unit of the model.

## Models

* Binary glTF 2.0 (`.glb`), as exported by Blender and other programs, with the data inside the file.
* The front points to +Z, up is +Y. The ground is at height 0 and the middle of the vehicle or building is at the origin.
* One unit is one sixteenth of a tile. A road vehicle is about 9 long, 3 wide and 3.5 high; a one-tile building fits in 16 by 16.
* A building model covers its whole footprint (a 2 by 2 house is 32 by 32) and stands on the highest corner of it. On sloped ground the game adds a stone foundation under it.
* Fronts: houses, industry tiles and objects face the south-west edge of the map view. Stations and drive-through stops lie along their track or road; the side to -X is the side with the station building. Bay stops face their road.
* Triangles take the base colour of their material. Textures, animations and skins are not read yet.
* A material with a name that starts with `company` takes a colour from the game, multiplied with its base colour: white becomes that colour, grey a darker shade of it. For vehicles, stations, stops and objects it is the owner's company colour; houses and industries use the colour the game picked for them.
* Each wagon or part of a vehicle is drawn with the model of its own vehicle ID.
* Houses and industries are replaced only when they are finished; while being built they keep their sprites.

## Licence

GPL-2.0, like OpenTTD (see `LICENSE`).
