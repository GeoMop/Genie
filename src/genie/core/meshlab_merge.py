def gen(script_file, distance):
    with open(script_file, "w") as f:
        f.write(template.format(distance))


template = '''<!DOCTYPE FilterScript>
<FilterScript>
  <filter name="Merge Close Vertices">
    <Param name="Threshold" min="0" type="RichAbsPerc" isxmlparam="0" max="1" value="{}"/>
  </filter>
</FilterScript>
'''
