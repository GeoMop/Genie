#!/usr/bin/env bash
# Builds win installer

# download prerequisites
wget -r -np -nd -nv -R "index.html*" -e robots=off -P build/win_x86 https://geomop.nti.tul.cz/genie/prerequisites/

# run nsis build
mkdir -p dist
docker run -i -u $(id -u):$(id -u) -v $(pwd):/nsis-project flow123d/nsis-3.05-1 /nsis-project/win_x86.nsi
#makensis -V4 win_x86.nsi
