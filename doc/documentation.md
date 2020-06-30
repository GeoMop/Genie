# Genie documentation

## Installation
### Windows
Installation packages are available at <https://geomop.nti.tul.cz/genie/packages/>.
Standard graphical instalator is available for Windows 10. To run the installation execute file
genie_0.2.0_x86_64.exe and go through installation wizard. Individual tools are executable by
their shortcuts or by batch files. Batch files are in default installation located in directory:
c:\\Users\\UserName\\AppData\\Local\\Genie\\bin\\.

### Linux
#### build pygimli
``` bash
curl -Ls install.pygimli.org | bash
```
For detailed description go to <https://www.pygimli.org/compilation.html#sec-build>.
Add path to pygimli to PYTHONPATH.

#### download Meshlab
Download Meshlab from <https://github.com/cnr-isti-vclab/meshlab/releases/download/Meshlab-2020.02/MeshLab2020.02-linux.zip>.
We need exact version MeshLab-2020.02, due to scrip version which we use.
Extract archive to some directory and add it to PATH.

#### clone project repository
``` bash
git clone https://github.com/GeoMop/Genie.git
```

#### install python packages
``` bash
pip install -r requirements.txt
```

## Perform inversion
- from File menu choose New project
- enter project directory in dialog
- import xsl file
- import point cloud, region covered with points is shown with green color
- with Mesh cut tool sets area of interest, either in text edits or using red shape on right side,
  position of shape in 3D space must be that, gallery cut was on shape faces, not on edges
- on left bottom part check measurements, which will be used in inversion
- press Run inversion
- sets inversion parameters, parametrs are taken from BERT/GIMLI
- press Start
- after successful inversion and closing Run inversion dialog, is shown tab Inversion 3D view with inversion results,
  in which is possible browse slices of 3D space

## Inversion parameters
- zWeight, lambda, robustData, blockyModel - describe in http://www.resistivity.net/download/bert-tutorial.pdf chapter 2.2
- maxIter - maximal number of iterations
- recalcJacobian - Jacobian will be recompute every iteration

## Tips
- cut of point cloud is time consuming operation, if we want to work with smaller area,
  after first inversion computation is possible to import to project file inversions/inversion_name/point_cloud_cut.xyz,
  which contains cut point cloud
- in installation are included softwares Meshlab and Gmsh, which can be used for showing and editing of point clouds and meshes

## Description of files in inversion directory
- inv.conf - configuration of inversin
- point_cloud_cut.xyz - cut point cloud
- gallery_mesh.ply, gallery_mesh.msh - gallery mesh
- inv_mesh.msh - mesh for own inversion
- input.dat - file with electrode positions and list of individual measurements
- input_snapped.dat - like previous, but electrodes are snapped to gallery mesh
- resistivity.vtk - result of inversion .vtk file
- resistivity.vector - rezistivity vektor on individual elements

## Known issues
- dialog PointCloudReader is irresponsive until reading ends
