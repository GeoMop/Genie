# Genie
3D inversion tool for Electrical Resistivity Tomography (ERT) and active Seismic Tomography (ST).

Genie is a GUI software for processing of electrical resistivity tomography data in 3D space.
Processing of data is consisting of this operations:

- import xls file with position of electrodes and list of measurements
- import point cloud, that describes surface of gallery
- combine multiple measurements
- make mesh of interested part of gallery and its surrounding
- solve inverse problem
- show results in 3D view

## Installation
### Windows
Installation packages are available at <https://geomop.nti.tul.cz/genie/packages/>.
Standard graphical installer is available for Windows 10. To run the installation execute file
genie_1.0.0_x86_64.exe and go through installation wizard. Individual tools are executable by
their shortcuts or by batch files. Batch files are in default installation located in directory:
c:\\Users\\UserName\\AppData\\Local\\Programs\\Genie\\bin\\.

### Linux
#### install pygimli
``` bash
conda create -n pg -c gimli -c conda-forge pygimli=1.2.1
```
For detailed description go to <https://www.pygimli.org/installation.html>.

#### clone project repository
``` bash
git clone https://github.com/GeoMop/Genie.git
```

#### install python packages
``` bash
pip install -r requirements.txt
```

## Documentation
[documentation](doc/documentation.md)
