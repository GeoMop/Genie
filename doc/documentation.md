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
We need exact version MeshLab-2020.02, due to script version which we use.
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

**lambda** - Float, global regularization parameter. Higher values leads to smoother result, lower values to overfitting. Default value is 20. 
**robustData** - Boolean, if set to 1, the [L1 minimization scheme](https://library.seg.org/doi/abs/10.1190/1.1440378) is used. Can be benefitial in the case of significant outliers in the data, but 
not used by defalut as it may cause deteriorated resolution. Default value 0 use L2 scheme assuming Gaussian error of the input data.
**zWeight** Float, anisotropic regularization parameter. Default value 1 prescribes an isometric regularization. For the values less then 1 the regularization in the vertical direction (Z-axis) is
diminished, which can lead to better result for verticaly layered geological structures.
**blockyModel** Boolean, L1 minimization scheme for the regulaization term. Allow non-smooth transitions in the resistivity.
**ConstrantType** (? is it supported in PyGimli) 0,1,2 (1 is default), order of derivative used in the regularization term. TBD see [PyGimli tutorial](https://www.pygimli.org/_tutorials_auto/3_inversion/plot_6-geostatConstraints.html)
**maxIter** - maximal number of iterations
**recalcJacobian** - Jacobian will be recomputed at every iteration, default. (TODO: omit this option)

Based on [parameters of the inversion](https://www.pygimli.org/pygimliapi/_generated/pygimli.manager.html) of the PyGimply library and 
on the related SW Bert [Chapter 2.2](http://www.resistivity.net/download/bert-tutorial.pdf).

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
