###Colormap Editing

It is possible to import custom colormap from .json file like this:

```
[
	{
		"Name" : "Example colormap from blue to white",
		"RGBPoints" : 
		[
			0, 0, 0, 1,
			
			1, 1, 1, 1
		]
	}
]
```

This format is the simplified version of format from Paraview,
so it is possible to import colormaps from Paraview, with some limitations or differences.
We only use attributes "Name" and "RGBPoints", all other attributes will be ignored.

Colormap is defined in attribute "RGBPoints" where every 4 numbers represent one node.
These 4 numbers define: value, red, green, blue (in this order). Colors between defined nodes are gained from linear interpolation.
Warning!!! color values must be in range 0-1.

As default Genie will change range of values to always utilize the whole colormap, but there is option to link colors to values.
When colors are linked the value range of the colormap will stay the same despite of range defined in Genie.

Example: If Genie defines range 1-5 and the example colormap from this document is used...

1) when colors arent linked then value 1 will be blue and value 5 will be white despite how is the colormap defined.

2) when colors are linked then all values in range 1-5 will be white, because they are outside defined range in colormap.
Values outside defined range are always the same color as the last closest defined color.


