<link rel="stylesheet" href="path/to/css/air.css">

# Genie reference manual

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

## Summary
Collection of the Genie tools (GeniERT and GenieST) is suited to performing 3D inversion of electical resistivity and seismic measurements, respectively.
Both tools are specialy crafted to simplify 3D inversion in mining gallery with complex geometry. The library [MeshLab](https://www.meshlab.net) is used to process laserscan data
into geometry of the galleries, then the [GMSH](https://gmsh.info/doc/texinfo/gmsh.html) meshing library is used for preparation of the computational mesh. Finally the [PyGIMLI](https://www.pygimli.org/) library is used to run actual ERT and ST inversions. Moreover, we provide tools for organization of the data from measurements and simple vizualization of the inversion results.


## Genie ERT
GenieERT is a software for [electrical resistivity tomography](https://en.wikipedia.org/wiki/Electrical_resistivity_tomography) 
in particular on exterior domains like surrounding rock of the mine galleries.

## Forward model
From many resistance measurements (usually) on the surface of a rock block, ERT constructs an approximation of the specific resistivity 
of the rock as a function of space and thus allows to infer the geological structure of the rock. The resistivity of the rock is mainly
affected by the amount of water in the rock and its salinity.
Let us denote $\Omega_b$ the domain of ​​the investigated block, to approximate the influence of the outer rock  we consider 
a larger computational domain $\Omega \supset \Omega_b$ with a boundary $\partial\Omega$. 
This boundary includes both the surface of the gallery $\Gamma_n$ as well as the outer boundary $\Gamma_d$ sufficiently far from $\Omega_b$.
The basic equation is conservation of the electric charge:

$$ div J(x) = f(x) $$


where $J$ is the current density $[Am^{-2}]$ and $f$ is the density of the current sources $[Am^{-3}]$. 
The current density is given by Ohm's law:

$$ J = \sigma E$

where $\sigma$ is the electrical conductivity $[\Omega^{-1}m^{-1}]$, which is the inverse of the resistivity $\rho$ $[\Omega m]$. The intensity of the electric field 
$E$ $[Vm^{-1}]$ is given by the electric potential $u$ $[V]$:

$$ E = -\nabla u$$

After substituting to the previous equations, we obtain a partial differential equation for the potential $u$:

$$ -div\left( \frac{1}{\rho} \nabla u \right) = f \quad \mbox{in} \Omega $$

providied the resistivity field $\rho$ and the prescribed density of current sources $f$.
We consider a homogeneous Neumann boundary condition (zero current density) on the surface of the gallery $\Gamma_n$
and a homogeneous Dirichlet condition (zero potential) on the outer boundary $$\Gamma_d$$. 
The source density usually includes two point sources with opposite signs corresponding to the current electrodes:

$$ f(x) = I\left(\delta(x-x_B)- \delta(x-x_A)\right).$$

Since the potential is a linear function of the current, it is sufficient to consider the unit current $I=1$ from $A$ to $B$ in the calculation.


In the case of an infinite domain, constant resistivity, and point source in $x_0$:

$$ f(x) = I\delta(x-x_0)$$

The governing equation in 3d space admits the analytical solution:

$$ u(x) = \frac{\rho_a I}{4 \pi |r|}, \quad r=x-x_0.$$ 

Theoretically, it would be possible to measure the current for the prescribed voltage between two electrodes,
but to eliminate very variable contact resistance between electrodes and rock, a four-point scheme is usually chosen, 
where a constant current $I$ is maintained between electrodes with and positions $x_A$ and $x_B$ and the potential difference $U$
is measured between the electrodes $x_C$ and $x_D$. 
In equidistant line measurements on the earth's surface, the positions of the electrodes are approximately given by their order,
but when measuring on the surface of the mine gallery, complete and sufficiently accurate information 
about the position of the electrodes in space is crucial for 3d inversion of the resistivity. 
The ratio $U/I$ is a sufficient input to the inversion since $U$ is a linear function of $I$.
However, to narrow the magnitude of the inputs and better assess mesurement deviations, 
the so-called apparent resistivity is usually considered. That is the resistance of an imaginary infinite medium with constant resistivity. 
To this end we use the analytical solution for individual electrodes to obtain the potential difference:


$$ U(C,D) = u_{AB}(D) - u_{AB}(C) = \frac{\rho_a I}{4\pi} \left( \frac{1}{r_DB} - \frac{1}{r_DA} - \frac{1}{r_CB} + \frac{1}{r_CA} \right) $$ 

From here, the apparent resistivity $\rho_a$ can be determined for known positions of the electrodes.
The input of the inversion is therefore:

    - Computation domain $\Omega$. A computational network is also required for numerical calculation.
    - Vector of electrode positions $x_i$.
    - Data of individual measurements $(i_A, i_B, i_C, i_D, \rho_a, s)$, 
      including the indices of current and potential electrodes, the apparent resistivity and its standard deviation.

The forward model is calculated for each measured pair of current electrodes and while all pairs of potential electrodes
are evaluated from the resulting approximation of the potential.


## 3.2 Computational geometry and mesh

Genie ERT software aims mainly on underground applications of ERT. 
One of the goals is to characterize the excavation damage zone (EDZ) close to the mine gallery walls.
Manual modelling of such complex geometry is very laborious and could introduce other source of error for the sake of simplicity.
Genie ERT and ST significantly simplifies this process by automatic creation of the computational geometry and mesh
from laser scanning.

Laser scanning is a rapidly evolving and cost-effective technology for converting real geometries 
into a virtual model. In our case, the result of scanning and subsequent processing is a cloud 
of points on the walls of the mine in the form of a text file where on each line there are three
XYZ coordinates of one point. The local coordinate system is used in the scan, however, 
when processing the data, the coordinates are converted to the regional coordinate system. 
For use in the Czech Republic, we assume the JTSK system for XY coordinates and altitude for the Z coordinate. 
A diferent coordinate system can be used, but the same system must then be used for the coordinates of electrodes or geophones.

The input point cloud can be extremely detailed with a resolution of up to 1mm and a file size in tens of GB. 
Working with such a large file is time consuming, so the import of the point cloud includes a filter to reduce
the resolution, other operations then take place over the reduced point cloud.
The geometry is created before the actual inversion calculation according to the specified block calculation area $\Omega$.
The procedure for creating a computer network is as follows:

The point cloud is cropped to a slightly expanded computing area. Then the points (on the mine wall) are used to approximation
of the surface by a triangular mesh. The MeshLab is used for this step based on the Marching cubes algorithm. By changing 
the size of the cubes it is possible to influence the resolution of the approximation. Moderate resolution is suitable to capture significant
shape of the gallery while eliminate unwanted artifacts in the point cloud.
Furthermore, the intersection of the surface mesh with the outer boundary is determined and the computational domain is described using the boundary
representation in the BREP format. This process includes:
    1. Cutting out the gallery from the computational block.
    2. Trimming the gallery surface with the boundary block.
    3. Joining these two objects to form closed boundary of the computational domain without holes.
The boundary representation is then input to the GMSH meshing tool, which is called via its Python API.
A scalar field is constructed to control the step of the mesh elements, 
which depends on the distance from the gallery walls. It is thus possible to prescribe a fine step 
near the walls and gradual coarsening towerds the outer boundary.

The overall procedure is relatively robust to various artifacts in the input data if the dimensions 
of the artifacts are smaller than the required mesh resolution, which should be adapted to resolve individual electrodes properly.
However if the size of the artefacts (e.g. fences, ventilation, cables) is comparable to the target resolution the point cloud has to be 
manually cleaned with an appropriate tool (e.g. LabMesh).

There are two other options how to prepare the computational mesh. First is a block domain with an uneven surface given 
by the point cloud/grid for classical surface applications of ERT. Second option is to import the mesh prepared manually 
using GMSH (https://gmsh.info/).





## Organization of input data
Genie ERT assumes measurement data in the form of text files with format produced by the apparatus Ares II from company GF Instrumnets.
The format (see input files in `tests` folder) starts with header containing the measurement metadata: time and date, 
location, operator, measuring method, arrangement of electrodes. After header the data of individual measurements
follows, every line contains: indices of two current and two potential electrodes, voltage on current 
electrodes $U_{out}$ $[V]$, current on current electrodes $I$ $[A]$, voltage on potential electrodes $U$ $[mV]$, 
apparent resistivity $R$ $[\ Ohm]$  and standard deviation $S$ of the measurement $[%]$.
The electrode indices, the $U / I$ ratio and the standard deviation are used for the calculation. 
The apparent resistivity $R$ is calculated by the apparatus assuming the linear placement of the electrodes
and is therefore not used. We rather use apparent resistivity $R_{in}$ calculated from true electorde positions (see the next paragraph).
Both resistivities as well as the model results can be compared in the `Measurement table` panel (see below).
Some measurements contain negative U-values. Although theoretically possible these values cause problems
in the inversion, so they are masked by default.

As the raw measurement data do not contain the actual electrode positions, it was necessary to create a format 
for additional metadata containing: 3d electrode coordinates, measurement overview with links to measurement 
result files, assignment of electrodes in individual measurements to their coordinates. From the information
point of view, it is appropriate to manage separately a table with unique electrode indices and their coordinates
and a table with an overview of measurements assigning electrodes in one measurement to their global indices. 
This concept was also implemented first, but did not meet the needs of the project partner, so the format
of one table was finally chosen. A section of the input table in XLS Excel format is shown in 
*Fig. 1.: Input table with measurement metadata*. 
Columns A-J contain electrode arrangement data, columns K-T contain 
data from the first measurement in this arrangement, other columns contain repeated measurements.

![](excel_table.png "Table of electrode positions")
*Obr. 1 Input table view with measurement metadata.* Columns A-J contain electrode arrangement data, 
columns K-T contain data from the first measurement in this arrangement, other columns contain repeated measurements.

The Genie ERT program reads the electrode arrangement data from the columns A-J, the measurement code from column K, 
the date from column L and the file with measured data from column O. Corresponding columns of the repeated measurments are used.
The folder column N is ignored, the measurement data file has to be placed in the subdirectory named by the measurement code 
relative to the table file.
From columns A-J, only the coordinates (columns H-J) and the electrode index within measurement (column F) 
are actually used for the calculation, the other columns are only used for reference.

Import function of the metadata table also deals with possible inconsitencies, i particular it performs following steps:
- load the table from the Excel format
- try to recognize structure of repeated measurements on the same set of electrodes
- deduplicate information about electrodes used in multiple measurements
- detect possible errors in the electrode indices wihin measurements and their coordinates
- check consistency of metadata and measurement data

Having the matadata table imported, the referenced measurement files are loaded and inadmissible values ​​
are excluded (masked) (negative potential differences, large deviations, ..). 
The user can perform custom masking using the `Measurement table` panel.









## 3.4 User Interface
The Genie ERT program organizes inverse tasks into projects, each project has complete data in the directory of the same name,
contains a point cloud, a background map, a file with measurement metadata and its own measurement data. 
It is possible to perform several separate inversions over this data.
The user interface consists of the main menu, configuration panels on the left and the main graphic window with several tabs,
see Fig. 2. We will describe these components in more detail below.


Giant. 2 Genie ERT user interface preview. Standard menu, configuration panels on the left, main graphic window with the situation on the right.

### Main menu
The main menu contains the item ‘File’ for project organization and configuration and the item ‘Inversions’ to select 
the current inversion and organize the inversion list. Next, we will describe the specifics of dialogs for importing data into projects in the `File` menu.
`Import excel file…` - import metadata file. The dialog allows you to transform the electrode coordinates into a conventional
positive quadrant of the JTSK system during reading.
`Import point cloud…` - import point cloud. The dialog allows you to prescribe the starting point of the local system 
to be used in the calculations, this reduces the numerical error. It is also possible to set the merging of nearby points 
with a given tolerance to reduce the amount of data. The ‘Read’ button will load the selected file with the specified 
transformation and filter. The ‘Save results’ button allows you to save the result for reuse, the ‘Import’ button will load the result into the project.
`Import mesh gallery…` - load computer network. To use it, you need to change the ‘Mesh from’ item in the inversion start dialog.
`Import maps …` - common raster (png, jpg, tiff) and vector (svg, pdf, eps) formats are supported for loading map works. 
To display the map correctly, you need to georeference it by setting the red and blue points to points with known coordinates and entering these coordinates.

###  3.4.2 Graphic panels
In the left part of the application there are graphic panels for electrode selection, calculation area selection and 
measurement selection. The configuration changes in the panels are linked to the display of the electrodes and the calculation
area in the situation in the main graphics window on the right. There are four configuration panels:

Electrodes - List of color-coded electrode groups. Measurements that contain electrodes from the selected groups are selected for the selected groups.
‘Mesh cut tool’ - selection of the computational block area. In the situation, it can be controlled graphically using the red tool.
The inversion area is strongly marked, the larger computational area of ​​the direct model is weakly marked. 
Their size ratio can be entered via the ‘inv factor’ item.
‘Side view’ - control of the section view (at the bottom of the situation). In the situation, it can be controlled using a blue graphics tool.
‘Measurements’ - selection of measurements used for inversion. The combined data of the selected measurements can be further 
filtered using the ‘Measurement table’ and ‘Measurement histogram’ tabs.
The ‘Run inversion’ button brings up the dialog for starting the inversion described in a separate section.

###  3.4.3 Main graphics window
The main graphics window contains tabs: `Situation`,` Measurement table`, `Measurement histogram`,` Misfit log`.
The key is the situation tab used to select the calculation area and to display the data used for the inversion. The view consisting
of the floor plan (top) and the vertical section (bottom) includes the following graphic elements:
The background map displayed in the background is bound to other elements using the georeferencing specified during import.
The point cloud is indicated by gray dots. Only a subset of the total set is used for this display.
Computer network. If an external computer network is used, it is displayed instead of a point cloud.
The positions of the electrodes are marked with different colors according to the areas of the mining work. For the currently
selected measurements, the respective points are highlighted with a larger size.
The position of the vertical section is displayed and adjusted using the blue control.
The calculation area is selected using the red control. The outer edge of the computing area is a prism. The floor plan is a 
parallelogram that can be entered interactively in the scene, the bases are entered numerically using altitude or using a graphic element in the section.
The `Measurement table` and` Measurement histogram` tabs allow you to display the data entering the inversion. The first displays 
the data using a table, the second using a histogram for individual quantities (see Fig. 3). The data can be masked by selecting 
individual rows or by using a filter when displaying the histogram. In addition, after the inversion, the quantities predicted by 
the model are available, especially the apparent resistance of individual measurements predicted by the model (quantity `AppResModel`).

Giant. 3 Histogram panel for the selected quantity. The previously selected quantity with the same unit is displayed in gray for comparison.
The `Misfit log` tab contains a graph of the development of key indicators during the iterative solution of the last inverse problem, see Fig. 4.
There are individual iterations on the horizontal axis. On the vertical axis, the standard deviation of the model 
from the measurement (Misfit), the value of the regularization functional (Regularization) and the value of the regularization coefficient (Lambda).

Giant. 4 Example of displaying the progress of solving an inverse problem in the “Misfit log” panels.

### 3.4.4 Inversion start
The inversion calculation includes both the automatic preparation of the computer network and then the iterative 
optimization algorithm. The main input data of the inversion: selected measurements, the range of the calculation area,
the point cloud are entered graphically. Invalid and masked measurements are automatically removed from the inversion input,
as well as measurements with electrodes outside the inversion area.

The inversion start dialog (Fig. 5) sets other parameters of the used algorithms. At the top of the dialog is the log from 
the last inversion run. The following are the parameters of the algorithms divided into groups. Here we present only a basic 
overview, a detailed description of individual parameters is in the documentation:
`General` - inversion working directory and detailed log selection
`Mesh` - choice of algorithm for network creation, network fineness setting
`Electorodes` - electrodes are automatically attracted to the surface of the computing area to a specified distance. 
By suitable choice, the attraction of the electrodes in the wells can be switched off.
`Inversion` - regularization parameters (especially Lambda parameter) and optimization algorithm
`Output` - inversion results are output in VTK format by default. Alternatively, you can turn on output on a regular grid in P3D format.


Giant. 5 Inversion start dialog.
            3.4.5 Visualization of results
After the inversion calculation, the resistance distribution field on the computer network elements is written in VTK format 
to the inversion working directory. The basic visualization of the results can be performed directly in the application 
in the `Inversion 3D View` tab, see Fig. 6.


Giant. 6 Visualization of the inversion result: field of resistances on the specified section.
# 4 Seismic tomography
 
## 4.1 Forward model
 Measurements for seismic tomography are as follows: geophones are placed on the wall of the work or in the borehole, 
 which are connected to the measuring apparatus (limited to about 16 current inputs). Subsequently, a mechanical shock 
 is induced in selected positions by tapping the wall of the work with a geological hammer. The strike is also registered 
 in the apparatus and the signal on the geophones is recorded from the moment of the strike.
Theoretically, the process is described by the Navier-Cauchy equation with a potentially inhomogeneous and anisotropic
elasticity tensor. Its direct solution would theoretically allow the use of a complete recorded signal for inversion, 
but the solution is sensitive to the initial condition, which is burdened with great uncertainty in the event of an impact.
This approach is thus more suitable for periodic input signals, such as ultrasonic measurements.
Of the recorded signals, only the arrival time of the sample from the source is used. To predict this quantity, it is possible 
to use Fermat's principle, ie that the excitation in the sense of a specific beam propagates from the source to the receiver 
along the path with the shortest time. The Parsk tracking method (Moser (1991), Klimeš and Kvasnička (1994)) using graph 
theory algorithms, specifically Dijkstra's modified algorithm for finding the shortest path in an evaluated graph, 
is based on this principle. The input of the forward model is the slownesses, i.e. the inverse values ​​of the wave velocities 
on the elements, the output is the predicted arrival times for the individual measurements. Additional auxiliary nodes are
added to the walls of the computer network elements. Let us denote the extended set of network nodes and the set of nodes 
on the element surface. The calculation graph is constructed on vertices and a complete subgraph on vertices is added for each element. 
Each edge is assigned a rating:

where is the geometric distance of the corresponding nodes and is the slowness on the element.
Dijkstra's algorithm determines the shortest path from one source vertex to all vertices of the graph. Thus, one run of the
algorithm finds the arrival times for all measurements with one common source. Dijkstra's algorithm with appropriate modifications
has approximately linear complexity, so the total time of the forward model is proportional, where is the number of nodes,
the average number of edges from one node and is the number of sources.
The resulting arrival time depends continuously, but not smoothly, on the slowness vector on the elements. 
This can cause some problems for gradient methods. However, if derivation-penalized regularization is used, the changes 
in the slow field are small and there are no problems with the convergence of the solver.

##  4.2 Organization of input data
Recordings of signals from geophones for individual strikes are stored in SEG2 format. As with ERT, the coordinates of each 
location must be assigned to each geophone and resource. In addition, the times of the first deployments (arrival of the P-wave) 
must be subtracted from the raw data.

Metadata for individual measurements consists of two tables in XLSX format of Excel. The table on the first sheet contains 
unique indexes of positions in 3D space, used for geophones or for resources. The table contains columns: position number,
approximate length, XYZ coordinates. The table on the second sheet lists the metadata for each signal log file. The table 
contains columns: file name, source position number, position number of the first geophone, position number of the last geophone, first valid channel.
Here, it is assumed that the scanned geophones form a continuous sequence in the main position table.

To identify first deployment times, Genie ST includes its own functionality for automatic or manual reading of first deployment times.
Alternatively, you can also import a table of already deployed first deployments. The XLSX table must contain the coordinates
of the geophones in the first three columns and the coordinates of the sources in the first three rows. The coordinates are
retrieved in the main metadata file, and for valid source-geophone pairs, the first deployment time is imported from the cell
on the appropriate column (source) and the appropriate row (geophone). Imported times are used as if they were deducted manually.

## 4.3 User interface
User interface very similar to GenieERT. The main differences are the input of the inversion area without the extended computing
area and the tool for identifying the first deployments from the geophone signals. The editor can be opened for individual measurements
by double-clicking in the `Measurements` table.

Editor, viz. Figure 6 shows the synchronized waveforms on the individual geophones. The times of the first deployments are automatically 
deducted from these signals. The automatically read value (green) can be confirmed or selected own (blue).

GenieST also does not include a table and histogram for the input data overview.

Giant. 7 First Deployment Editor. Displays signals from geophones and allows automatic or manual identification of the time of first deployment

## Perform inversion
- from File menu choose New project
- enter project directory in dialog
- import xsl file
- import point cloud, region covered with points is shown with green color
- with Mesh cut tool sets area of interest
- on left bottom part check measurements, which will be used in inversion
- press Run inversion
- sets inversion parameters, parameters are mostly taken from BERT/GIMLI
- press Start
- after successful inversion and closing Run inversion dialog, is shown tab Inversion 3D view with inversion results,
  in which is possible browse slices of 3D space

## Inversion mesh options

**Mesh from** - Defines how it is created inversion mesh.
"Gallery cloud" means that gallery mesh is created from imported point cloud and that mesh is subtracted from area of interest.
"Surface cloud" means that surface is created from imported point cloud, this surface is cut and complete to form defined by area of interest.
"Gallery mesh" means that imported gallery mesh is used instead point cloud.
<!---
**Reconstruction depth** - In case that previous option is "Gallery cloud", define how much details will be reconstructed from point cloud. Bigger value means more details.
This value is integer from 4 to 10.
-->
**Small component ratio** - Small gallery mesh components are removed. This ratio define threshold for removing relative to largest component.
**Edge length** - Reconstructed mesh is remeshed with this target edge length.
**Element size** - Defines inversion mesh element size based od distance from electrode. On distance smaller then "d" element size will be "h".
On distance larger then "D" element size will be "H". Between these points is element size defined by linear function.

## Electrode options

**Snap distance** - Electrodes are snapped to gallery surface, this parameter determine maximal snap distance.

## Inversion parameters

**Min resistivity, Max resistivity** - Minimal resp. maximal value of resistivity allowed in model.
**Lambda** - Float, global regularization parameter. Higher values leads to smoother result, lower values to overfitting. Default value is 20.
**Optimize lambda** - If true lambda will be optimized by Lcurve.
**Robust data** - Boolean, if set to 1, the [L1 minimization scheme](https://library.seg.org/doi/abs/10.1190/1.1440378) is used. 
Can be benefitial in the case of significant outliers in the data, but
not used by defalut as it may cause deteriorated resolution. Default value 0 use L2 scheme assuming Gaussian error of the input data.
**Z weight** Float, anisotropic regularization parameter. Default value 1 prescribes an isometric regularization. For the values 
less then 1 the regularization in the vertical direction (Z-axis) is
diminished, which can lead to better result for verticaly layered geological structures.
**Blocky model** Boolean, L1 minimization scheme for the regularization term. Allow non-smooth transitions in the resistivity.
<!---
**Constrant type** (? is it supported in PyGimli) 0,1,2 (1 is default), order of derivative used in the regularization term. 
TBD see [PyGimli tutorial](https://www.pygimli.org/_tutorials_auto/3_inversion/plot_6-geostatConstraints.html)
-->
**Max iter** - maximal number of iterations
**Data log** - Use logarithmic transformation in data.

Based on [parameters of the inversion](https://www.pygimli.org/pygimliapi/_generated/pygimli.manager.html) of the PyGimply library and 
on the related SW Bert [Chapter 2.2](http://www.resistivity.net/download/bert-tutorial.pdf).

## Output options

**Local coordinates** - Save outputs in local coordinates.
**p3d** - If checked inversion result is also saved in p3d format suitable for software Voxler.
**p3d step** - Defines step between individual points.

## Mesh cut tool
Mesh cut tool sets area of interest, either in text edits or using red shape on right side,
position of shape in 3D space must be that, gallery cut was on shape faces, not on edges.
Button "+" move origin point to center of area defined by points cloud, electrode positions and map.
Button "L" sets gen vector perpendicular to other vector.

## Analyse measurement
Analyse measurement dialog is activated by double clicking on measurement in left bottom part, it shows data from measurements files.
Columns ca, cb, pa, pb, I, V, std, AppRes are from measurement files.
**AppResGimli** is apparent resistivity computed from input values using Gimli geometric factor function,
which use full 3d space not half space and use elecrode positions from input xls file, that apparent resistivity values are different.
Lines not suitable for computation are marked with red color, this lines are not use in computation, they do not need to be deleted from the files.

## Measurement table
Table shows all measurements from selected measurements from left bottom panel.
Table may be sorted by individual columns by clicking on column header.
Individual measurements may be masked by clicking on checkbox. This measurement will not be used in inversion.
For mask multiple measurements select them and click on mask in context menu.

## Measurement histogram
Shows histograms of quantities from Measurement table. It is possible to apply filter on relevant quantity.
This filter is also applied on relevant quantity in Measurement table.

## Map file
It is posible to import a map. From file menu choose "Import map...".
After image file is selected, dialog for map calibration is appeared.
Move blue and red cross to two points with known positions and type this positions to edit box below, then click on import.

## Import gallery mesh
Gallery mesh generated from point cloud can be replaced by own mesh.
Mesh must be in .msh format.
From file menu choose "Import gallery mesh...".
Mesh is shown in blue color.
In "Run inversion" dialog set parameter "meshFrom" to "Gallery mesh".

## Surface from point cloud
Inversion mesh can be defined by point cloud on some surface. Other mesh faces are defined by Mesh cut tool area of interest.
Area of interest must be positioned inside region defined by point cloud.
From file menu choose "Import point cloud...".
In "Run inversion" dialog set parameter "meshFrom" to "Surface cloud".

## Measurements on model panel
After successful inversion is shown tab "Measurements on model" in which are displayed apparent resistivity on model obtained by inversion.
Columns meas_number, ca, cb, pa, pb, I, V, AppRes, std are from measurement files.
**AppResGimli** is apparent resistivity computed from input values.
**AppResModel** is apparent resistivity on model.

## Tips
- cut of point cloud is time consuming operation, if we want to work with smaller area,
  after first inversion computation is possible to import to project file inversions/inversion_name/point_cloud_cut.xyz,
  which contains cut point cloud
- in installation is included software Gmsh, which can be used for showing and editing of meshes

## Description of files in inversion directory
- inv.conf - configuration of inversion
- point_cloud_cut.xyz - cut point cloud
- gallery_mesh.ply, gallery_mesh.msh - gallery mesh
- inv_mesh.msh - mesh for own inversion
- input.dat - file with electrode positions and list of individual measurements
- input_snapped.dat - like previous, but electrodes are snapped to gallery mesh
- resistivity.vtk - result of inversion .vtk file
- resistivity.vector - resistivity vector on individual elements
- resistivity.p3d - result in p3d format
- resistivity.q - second file of p3d format

## Known issues
- some measurements have to small current, it may cause inaccuracy in computation, currently this is not solved in any way

## Genie ST
Application Genie ST is similar to Genie RT. There is a "First arrival editor" dialog instead of "Analyse measurement",
in which are displayed signal waveforms from individual measurement files.
It is possible to set actual first arrivals by blue vertical lines.
Some receivers can be disabled by unchecking checkboxs in left column.


