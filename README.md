
# stepfg: STEP File Generator                
Authors: E. Valetov and M. Berz  
Organization: Michigan State University  
Creation date: 03-Feb-2017  
Email: valetove@msu.edu

## 0. Introduction

This program converts a list of polygons in the x-y plane specified by
vertices into a STEP\* file containing a 3D part obtained by extrusion of
interiors regions of these polygons along the z-axis.

\* STEP is an abbreviation for STandard for the Exchange of Product model data – ISO 10303-242.

## 1. Repository contents

[README.md](README.md) This file  
[LICENSE.md](LICENSE.md) Copyright notice  
[stepfg.py](stepfg.py) Python source code  
[part_geometry.txt](part_geometry.txt) Sample input file (Muon g-2 Collaboration quadrupole)

## 2. Command-line arguments

    stepfg [filename_in [filename_out]] [-h] [/h]  
filename_in:    Input file containing 2D geometry data (default: "part_geometry.txt")  
filename_out:   Output STEP file with resulting 3D part (default: "part_out.stp")  
-h or /h:       Help information  

## 3. Input file format

The input file format is three parameters as follows:

    [First_argument,
    Second_argument,
    Third_argument]

First_argument: List of polygon specifications [pol1,pol2,...,poln]. Each
    polygon specification is a sequential list [vert1,vert2,...,vertm] of the
    polygon's vertices in the x-y plane. Each vertex is specified as a list
    [x,y] or [x,y,0].  
Second_argument: z-coordinate interval [z1, z2] that the resulting 3D part
    should span.  
Third_argument: Geometric proportionality coefficient. The output unit of
    length in the STEP file is mm, so use 10 if the 2D geometry is specified
    in cm.

A sample input file, "part_geometry.txt" containing a representation of the
Muon g-2 Collaboration quadrupole, is supplied with this program.

## 5. Copyright Notice
© 2017 Eremey Valetov and Martin Berz
