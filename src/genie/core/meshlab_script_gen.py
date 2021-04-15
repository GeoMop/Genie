def gen(script_file, depth, ratio, len):
    with open(script_file, "w") as f:
        f.write(template.format(depth, ratio, len, len))


template = '''<!DOCTYPE FilterScript>
<FilterScript>
  <filter name="Compute normals for point sets">
  </filter>
  <xmlfilter name="Surface Reconstruction: Screened Poisson">
    <xmlparam name="cgDepth" value="0"/>
    <xmlparam name="confidence" value="false"/>
    <xmlparam name="depth" value="{}"/>
    <xmlparam name="fullDepth" value="5"/>
    <xmlparam name="iters" value="8"/>
    <xmlparam name="pointWeight" value="4.0"/>
    <xmlparam name="preClean" value="false"/>
    <xmlparam name="samplesPerNode" value="1.5"/>
    <xmlparam name="scale" value="1.1"/>
    <xmlparam name="visibleLayer" value="false"/>
  </xmlfilter>
  <filter name="Select small disconnected component">
    <Param type="RichFloat" name="NbFaceRatio" isxmlparam="0" value="{}"/>
    <Param type="RichBool" name="NonClosedOnly" isxmlparam="0" value="false"/>
  </filter>
  <filter name="Delete Selected Faces and Vertices"/>
  <filter name="Invert Faces Orientation">
    <Param type="RichBool" name="forceFlip" isxmlparam="0" value="false"/>
    <Param type="RichBool" name="onlySelected" isxmlparam="0" value="false"/>
  </filter>
  <filter name="Remove Zero Area Faces"/>
  <filter name="Remove Duplicate Vertices"/>
  <filter name="Remeshing: Isotropic Explicit Remeshing">
    <Param type="RichInt" isxmlparam="0" value="3" name="Iterations"/>
    <Param type="RichBool" isxmlparam="0" value="false" name="Adaptive"/>
    <Param type="RichBool" isxmlparam="0" value="false" name="SelectedOnly"/>
    <Param type="RichAbsPerc" isxmlparam="0" min="0" value="{}" name="TargetLen" max="1"/>
    <Param type="RichFloat" isxmlparam="0" value="30" name="FeatureDeg"/>
    <Param type="RichBool" isxmlparam="0" value="true" name="CheckSurfDist"/>
    <Param type="RichAbsPerc" isxmlparam="0" min="0" value="{}" name="MaxSurfDist" max="1"/>
    <Param type="RichBool" isxmlparam="0" value="true" name="SplitFlag"/>
    <Param type="RichBool" isxmlparam="0" value="true" name="CollapseFlag"/>
    <Param type="RichBool" isxmlparam="0" value="true" name="SwapFlag"/>
    <Param type="RichBool" isxmlparam="0" value="true" name="SmoothFlag"/>
    <Param type="RichBool" isxmlparam="0" value="true" name="ReprojectFlag"/>
  </filter>
</FilterScript>
'''
