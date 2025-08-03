
# Parserasgeo

PARSE hec-RAS GEOmetry - Import/Export [HEC-RAS](https://www.hec.usace.army.mil/software/hec-ras/) geometry files. 

Parserasgeo is a Python library for importing, editing, and exporting HEC-RAS geometry files and can be used for automating sensitivity analyses, Monte Carlo analyses, and any other workflow that requires changing RAS geometry programmatically. Parserasgeo is a work in progress; however, most cross section functionality exists. Lines that are not understood are stored as text and will be rewritten when the geometry is exported. Parserasgeo is known to work with Python 2 and should also work with Python 3.

HEC-RAS models can be run automatically using [rascontrol](https://github.com/mikebannis/rascontrol).

---

## About This Fork

This is an actively maintained fork of [mikebannis/parserasgeo](https://github.com/mikebannis/parserasgeo), hosted at [chunyaoyang/parserasgeo](https://github.com/chunyaoyang/parserasgeo).

### Key changes:
- Replaced `uflow.py` with `pyflow.py`, which provides unified support for both steady (`*.f??`) and unsteady (`*.u??`) flow data.
- Enhanced `pyplan.py` to support reading and writing additional plan file content and metadata.
- Updated `pyprj.py` with new methods for programmatically inserting project file entries and changing active plan settings.
- Improved formatting, parsing robustness, and file export support.

This fork will continue development and welcomes contributions.

---

## Getting Started

Parserasgeo is mostly easily installed from GitHub:

```bash
git clone https://github.com/chunyaoyang/parserasgeo.git
cd parserasgeo
pip install .
```

---

## Examples

### Edit Geometry File

Open a model, increase all Manning's n values by 50%, and save the geometry as a new file.

```python
import parserasgeo as prg

geo = prg.ParseRASGeo('my_model.g01')

for xs in geo.get_cross_sections():
    n_vals = xs.mannings_n.values 
    new_n = [(station, n*1.5, other) for station, n, other in n_vals]
    xs.mannings_n.values = new_n

geo.write('my_model.g02')
```

### Read and Modify a Plan File (`prplan`)

```python
from parserasgeo import prplan

plan = prplan.ParseRASPlan("example.p01")
print(plan.plan_title)
print(plan.geo_file)

# Modify plan title
plan.plan_title = "Modified Plan Title"
plan.write("example_modified.p01")
```

### Add Internal Change Line to a Steady Flow File (`prflow`)

```python
from parserasgeo import prflow

flow = prflow.SteadyFlow("example.f01")
flow.add_internal_change_line(river_station=2000.0, ws_change=1.5)
flow.export("example_modified.f01")
```

### Modify and Add Entries to a Project File (`prprj`)

```python
from parserasgeo import prprj

project = prprj.ParseRASProject("example.prj")

# Add a new geometry, flow, and plan file entry
project.insert_entry(["g03", "f03", "p03"])

# Change the current plan to p02
project.change_plan("02")

project.write("example_modified.prj")
```

---

## Contributing

While currently functional, this is very much a work in progress. Well-written and tested pull requests are gladly accepted.

One of the goals for this library is that exported geometries will match original geometries to the character. This allows easy testing of new functionality by comparing the original geometry file to one exported from parserasgeo (assuming no changes were made).
