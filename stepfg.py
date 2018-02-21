#!/usr/bin/python
helpstr = '''
This program converts a list of polygons in the x-y plane specified by
vertices into a STEP file containing a 3D part obtained by extrusion of
interiors regions of these polygons along the z-axis.

stepfg [filename_in [filename_out]] [-h] [/h]
    filename_in    Input file containing 2D geometry data
                   (default: "part_geometry.txt")
    filename_out   Output STEP file with resulting 3D part
                   (default: "part_out.stp")
    -h or /h       This information

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
'''

__author__ = "E. Valetov and M. Berz"
__version__ = "1.0.1"
__maintainer__ = "E. Valetov"
__email__ = "valetove@msu.edu"
__status__ = "Production"

import re
import math
import operator
import ast
import sys
import datetime
from numbers import Number
from pathlib import Path


def line_index(line):
    search_result = re.search('#(.+?)=', line)
    return 0 if search_result is None else int(search_result.group(1))


def rotate(list_in, x):
    return list_in[-x:] + list_in[:-x]


def item_exists_q(string_in):
    if not work_array:
        return False
    search_result = [i for i, item in enumerate(work_array) if
                     item.endswith(string_in)]
    return False if not search_result else True


def existing_item_ln(string_in):
    if not work_array:
        return False
    if not item_exists_q(string_in):
        return False
    search_result = [item for item in work_array if item.endswith(string_in)]
    return line_index(search_result[0])


def new_item(string_in):
    global current_index
    global work_array
    if item_exists_q(string_in):
        return_index = existing_item_ln(string_in)
    else:
        work_array.append('#' + str(current_index) + '=' + string_in)
        return_index = current_index
        current_index += 1
    return return_index


def to_coord(clist):
    if len(clist) != 3:
        print('to_coord: Error. Coordinates not 3D.')
        sys.exit()
    return str(clist[0]) + ',' + str(clist[1]) + ',' + str(clist[2])


def to_step_list(slist):
    if not isinstance(slist, list):
        slist1 = '#' + str(slist)
    else:
        slist1 = ''
        for j in range(0, len(slist) - 1):
            slist1 += '#' + str(slist[j]) + ','
        slist1 += '#' + str(slist[-1])
    return slist1


def fort_bool(bool_in):
    return '.T.' if (bool_in == True) or (bool_in == '.T.') else '.F.'


def normalize(vector_in):
    if len(vector_in) != 3:
        print('normalize: Error. Coordinates not 3D.')
        sys.exit()
    magnitude = math.sqrt(sum([i ** 2 for i in vector_in]))
    return [x / magnitude for x in vector_in]


def cross_product(x, y):
    return [-x[2] * y[1] + x[1] * y[2], x[2] * y[0] - x[0] * y[2],
            -x[1] * y[0] + x[0] * y[1]]


def point(coord_in):
    return new_item("CARTESIAN_POINT('',(" + to_coord(coord_in) + ")) ;\n")


def line(origin, direction):
    coord_ln = new_item(
        "CARTESIAN_POINT('Origin Line',(" + to_coord(origin) + ")) ;\n")
    dir_ln = new_item("DIRECTION('Vector Direction',(" + to_coord(
        normalize(direction)) + ")) ;\n")
    vec_ln = new_item("VECTOR('Line Direction',#" + str(dir_ln) + ",1.) ;\n")
    return new_item(
        "LINE('Line',#" + str(coord_ln) + ",#" + str(vec_ln) + ") ;\n")


def vertex(coord_in):
    coord_ln = new_item(
        "CARTESIAN_POINT('Vertex',(" + to_coord(coord_in) + ")) ;\n")
    return new_item("VERTEX_POINT('',#" + str(coord_ln) + ") ;\n")


def edge_curve(vertex1_ln, vertex2_ln, line_coord_ln, same_sense=True):
    return new_item(
        "EDGE_CURVE('',#" + str(vertex1_ln) + ",#" + str(
            vertex2_ln) + ",#" + str(line_coord_ln) + "," + fort_bool(
            same_sense) + ") ;\n")


def edge_curve_0(vertex1, vertex2, same_sense=True):
    return edge_curve(vertex(vertex1), vertex(vertex2), line(
        [x / 2 for x in list(map(operator.add, vertex1, vertex2))],
        list(map(operator.sub, vertex2, vertex1))),
                      fort_bool(same_sense))


def oriented_edge(edge_curve_ln, same_sense=True):
    return new_item(
        "ORIENTED_EDGE('',*,*,#" + str(edge_curve_ln) + "," + fort_bool(
            same_sense) + ") ;\n")


def edge_loop(lines):
    return new_item("EDGE_LOOP('',(" + to_step_list(lines) + ")) ;\n")


def edge_loop_0(vertices):
    return edge_loop(list(
        map(lambda x1, x2: oriented_edge(edge_curve_0(x1, x2)), vertices,
            rotate(vertices, -1))))


def face_outer_bound(edge_loop_ln, same_sense: True):
    return new_item(
        "FACE_OUTER_BOUND('',#" + str(edge_loop_ln) + "," + fort_bool(
            same_sense) + ") ;\n")


def edge_loop_1(vertices, same_sense: True):
    return face_outer_bound(edge_loop_0(vertices), same_sense)


def axis2_placement_3d(origin_coord, direction1, direction2):
    origin_ln = new_item("CARTESIAN_POINT('Axis2P3D Location',(" + to_coord(
        origin_coord) + ")) ;\n")
    direction1_ln = new_item(
        "DIRECTION('Axis2P3D ZDirection',(" + to_coord(direction1) + ")) ;\n")
    direction2_ln = new_item(
        "DIRECTION('Axis2P3D XDirection',(" + to_coord(direction2) + ")) ;\n")
    return new_item(
        "AXIS2_PLACEMENT_3D('Plane Axis2P3D',#" + str(origin_ln) + ",#" + str(
            direction1_ln) + ",#" + str(
            direction2_ln) + ") ;\n")


def plane(axis2_placement_3d_ln):
    return new_item("PLANE('',#" + str(axis2_placement_3d_ln) + ") ;\n")


def plane_0(origin_coord, direction1, direction2):
    return plane(axis2_placement_3d(origin_coord, direction1, direction2))


def advanced_face(face_outer_bound_ln, plane_ln, same_sense_plane=True):
    return new_item(
        "ADVANCED_FACE('PartBody',(" + to_step_list(
            face_outer_bound_ln) + "),#" + str(plane_ln) + "," + fort_bool(
            same_sense_plane) + ") ;\n")


def advanced_face_0(vertices, zaxis, same_sense_1=True, same_sense_2=True):
    if list(map(operator.add, normalize(zaxis), normalize(
            cross_product(list(map(operator.sub, vertices[2], vertices[1])),
                          list(map(operator.sub, vertices[2],
                                   vertices[0])))))) == [0, 0, 0]:
        af_ln = advanced_face(edge_loop_1(vertices, same_sense_1), plane(
            axis2_placement_3d(vertices[0], normalize(zaxis),
                               normalize(list(map(operator.sub, vertices[1],
                                                  vertices[0]))))),
                              same_sense_2)
    else:
        af_ln = advanced_face(
            edge_loop_1(list(reversed(vertices)), same_sense_1), plane(
                axis2_placement_3d(vertices[0], normalize(zaxis), normalize(
                    list(map(operator.sub, list(reversed(vertices))[1],
                             list(reversed(vertices))[0]))))), same_sense_2)
    return af_ln


def advanced_face_1(vertices, same_sense_1=True, same_sense_2=True):
    return advanced_face(edge_loop_1(vertices, same_sense_1),
                         plane(axis2_placement_3d(vertices[0], normalize(
                             cross_product(list(
                                 map(operator.sub, vertices[2], vertices[1])),
                                 list(map(operator.sub, vertices[1],
                                          vertices[0])))), normalize(
                             list(map(operator.sub, vertices[1],
                                      vertices[0]))))), same_sense_1)


def closed_shell(advanced_face_ln_list):
    return new_item("CLOSED_SHELL('Closed Shell',(" + to_step_list(
        advanced_face_ln_list) + ")) ;\n")


def manifold_solid_brep(closed_shell_ln):
    global part_body_index
    msb = new_item(
        "MANIFOLD_SOLID_BREP('PartBody." + str(part_body_index) + "',#" + str(
            closed_shell_ln) + ") ;\n")
    part_body_index += 1
    return msb


def advanced_brep_shape_representation(manifold_solid_brep_list, init_ln=45):
    return new_item(
        "ADVANCED_BREP_SHAPE_REPRESENTATION('NONE',(" + to_step_list(
            manifold_solid_brep_list) + "),#" + str(
            init_ln) + ") ;\n")


def shape_representation_relationship(advanced_brep_shape_representation_ln,
                                      shape_representation_ln=48):
    return new_item("SHAPE_REPRESENTATION_RELATIONSHIP(' ',' ',#" + str(
        shape_representation_ln) + ",#" + str(
        advanced_brep_shape_representation_ln) + ") ;\n")


def zface(vertex1, vertex2, geom_depth_list):
    z_neg = geom_depth_list[0]
    z_pos = geom_depth_list[1]
    return advanced_face_0(
        [list(map(operator.add, vertex1, [0, 0, z_neg])),
         list(map(operator.add, vertex2, [0, 0, z_neg])),
         list(map(operator.add, vertex2, [0, 0, z_pos])),
         list(map(operator.add, vertex1, [0, 0, z_pos]))],
        normalize(cross_product(list(map(operator.sub, vertex2, vertex1)),
                                [0, 0, -(z_pos - z_neg)])))


def xyface(vertex_list, depth, zdir):
    return advanced_face_0(list(
        map(lambda x: list(map(operator.add, x, [0, 0, depth])), vertex_list)),
        zdir)


def af2d3d(vertex_list, geom_depth_list):
    taflist = []
    z_neg = geom_depth_list[0]
    z_pos = geom_depth_list[1]
    taflist.append(xyface(vertex_list, z_pos, [0, 0, 1]))
    taflist.append(xyface(vertex_list, z_neg, [0, 0, -1]))
    taflist += list(
        map(lambda x1, x2: zface(x1, x2, geom_depth_list), vertex_list,
            rotate(vertex_list, -1)))
    return taflist


def af_list_2_assembly(af_list):
    return shape_representation_relationship(
        manifold_solid_brep(closed_shell(af_list)))


def af_list_2_part(af_list):
    return manifold_solid_brep(closed_shell(af_list))


def part_2_assembly(part_list):
    return shape_representation_relationship(
        advanced_brep_shape_representation(part_list))


def generate_part(vert_list, geom_depth, clockwise_p=True):
    return af_list_2_part(
        af2d3d(vert_list, geom_depth)) if clockwise_p else af_list_2_part(
        af2d3d(reversed(vert_list), geom_depth))


def convert_3d(element_in):
    if (isinstance(element_in, list)) and (len(element_in)) == 2 and (
            isinstance(element_in[0], Number)) and (
            isinstance(element_in[1], Number)):
        return [element_in[0], element_in[1], 0]
    else:
        return element_in


def convert_to_clockwise(part_list):
    pol_sum = sum(list(
        map(lambda x1, x2: (x2[0] - x1[0]) * (x2[1] + x1[1]), part_list,
            rotate(part_list, 1))))
    if pol_sum == 0:
        print(
            "[FAILED]\nconvert_to_clockwise: Error. Polygon is" +
            " neither clockwise nor counter-clockwise.")
        sys.exit()
    elif pol_sum > 0:
        return reversed(part_list)
    else:
        return part_list


def generate_assembly(list_vert_list, geom_depth_list, p_coeff=1):
    print("Generating assembly... ", end="")
    if not isinstance(p_coeff, Number):
        print(
            "[FAILED]\ngenerate_assembly: Error. NaN supplied for" +
            " proportionality coefficient.")
        sys.exit()
    if p_coeff == 0:
        print(
            "[FAILED]\ngenerate_assembly: Error. Zero supplied as" +
            " the proportionality coefficient.")
        sys.exit()
    if not isinstance(geom_depth_list, list):
        print(
            "[FAILED]\ngenerate_assembly: Error. z-coordinate interval" +
            " [z1, z2] expected, scalar supplied.")
        sys.exit()
    if not geom_depth_list:
        print(
            "[FAILED]\ngenerate_assembly: Error. z-coordinate interval" +
            " [z1, z2] expected, empty list supplied.")
        sys.exit()
    for depth_element in geom_depth_list:
        if not isinstance(depth_element, Number):
            print(
                "[FAILED]\ngenerate_assembly: Error. NaN found in the" +
                " z-coodinate interval.")
            sys.exit()
    if geom_depth_list[0] == geom_depth_list[1]:
        print(
            "[FAILED]\ngenerate_assembly: Error. z2 must be different" +
            " from z1 in the z-coordinate interval [z1, z2].")
        sys.exit()
    if geom_depth_list[0] > geom_depth_list[1]:
        tvar = geom_depth_list[0]
        geom_depth_list[0] = geom_depth_list[1]
        geom_depth_list[1] = tvar
    if not isinstance(list_vert_list, list):
        print(
            "[FAILED]\ngenerate_assembly: Error. List of vertices lists" +
            " expected, scalar supplied.")
        sys.exit()
    if not list_vert_list:
        print(
            "[FAILED]\ngenerate_assembly: Error. Empty list of vertices" +
            " lists.")
        sys.exit()
    for part_element in list_vert_list:
        if not part_element:
            print(
                "[FAILED]\ngenerate_assembly: Error. Empty list of" +
                " vertices.")
            sys.exit()
        if not isinstance(part_element, list):
            print(
                "[FAILED]\ngenerate_assembly: Error. List of vertices" +
                " expected, scalar supplied")
            sys.exit()
        for vertex_element in part_element:
            if not vertex_element:
                print(
                    "[FAILED]\ngenerate_assembly: Error. Empty list of" +
                    "vertex coordinates.")
                sys.exit()
            if not isinstance(part_element, list):
                print(
                    "[FAILED]\ngenerate_assembly: Error. List of vertex" +
                    " coordinates expected, scalar supplied")
                sys.exit()
            if (len(vertex_element) < 2) or (len(vertex_element) > 3):
                print(
                    "[FAILED]\ngenerate_assembly: Error. Number of vertex" +
                    " coordinates should be 2 or 3, " + str(
                        len(vertex_element)) + " coordinates supplied.")
                sys.exit()
            for coordinate_element in vertex_element:
                if not isinstance(coordinate_element, Number):
                    print(
                        "[FAILED]\ngenerate_assembly: Error. NaN is supplied" +
                        " for a vertex coordinate.")
                    sys.exit()
    list_vert_list = [
        [convert_3d(vertex_element) for vertex_element in part_element] for
        part_element in
        list_vert_list]
    list_vert_list = [convert_to_clockwise(x) for x in list_vert_list]
    list_vert_list = [
        [[p_coeff * 1.0 * coordinate_element for coordinate_element in
          vertex_element] for vertex_element in
         part_element] for part_element in list_vert_list]
    geom_depth_list = [p_coeff * 1.0 * i for i in geom_depth_list]
    part_list = [generate_part(x, geom_depth_list) for x in list_vert_list]
    part_2_assembly(part_list)
    resulting_array = file_array[:index1] + work_array + file_array[
                                                         index1 + 1:]
    print("[DONE]")
    print("Writing STEP file... ", end="")
    with open(file_out_name, 'w+') as file_out:
        for item in resulting_array:
            file_out.write("%s" % item)
    print("[DONE]")


file_in2_name = 'part_geometry.txt'
file_out_name = 'part_out.stp'

print("----------------------------------------------------")
print("                STEP File Generator")
print("              E. Valetov and M. Berz")
print("             Michigan State University")
print("                Created 03-Feb-2017")
print("              Email: valetove@msu.edu")
print("----------------------------------------------------")

if (len(sys.argv) > 1):
    if ((str(sys.argv[1]) == '-h') or (str(sys.argv[1]) == '/h')):
        print(helpstr)
        sys.exit()
    file_in2_name = str(sys.argv[1])
    if (len(sys.argv) > 2):
        if ((str(sys.argv[2]) == '-h') or (str(sys.argv[2]) == '/h')):
            print(helpstr)
            sys.exit()
        file_out_name = str(sys.argv[2])

print("Use command-line option -h or /h for help.\n")

print("Reading 2D geometry file " + file_in2_name + "... ", end="")
if not Path(file_in2_name).is_file():
    print(
        "[FAILED]\nError. 2D geometry file " + file_in2_name +
        " doesn't exist.")
    sys.exit()
with open(file_in2_name, 'r') as file_in:
    data = ast.literal_eval(file_in.read())
if not isinstance(data, list):
    print("[FAILED]\nError. Input data is not a list.")
    sys.exit()
if len(data) != 3:
    print(
        "[FAILED]\nError. The top-level length of the input data list is not" +
        " 3.")
    sys.exit()
in_array = data[0]
in_depth = data[1]
in_coeff = data[2]
print("[DONE]")

print("Initializing STEP file data... ", end="")
d = datetime.datetime.now()
file_array = ["ISO-10303-21;",
              "HEADER;",
              "FILE_DESCRIPTION(('none'),'2;1');",
              "",
              "FILE_NAME('" + file_out_name + "','none',('none'),('none')," +
              "'none','none','none');",
              "",
              "FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));",
              "",
              "ENDSEC;",
              "DATA;",
              "#1=APPLICATION_CONTEXT('configuration controlled 3D design of" +
              " mechanical parts and assemblies') ;",
              "#2=MECHANICAL_CONTEXT(' ',#1,'mechanical') ;",
              "#3=DESIGN_CONTEXT(' ',#1,'design') ;",
              "#4=APPLICATION_PROTOCOL_DEFINITION('international standard'," +
              "'config_control_design',1994,#1) ;",
              "#5=PRODUCT('Part1','','',(#2)) ;",
              "#6=PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE('',' '" +
              ",#5,.NOT_KNOWN.) ;",
              "#7=PRODUCT_CATEGORY('part',$) ;",
              "#8=PRODUCT_RELATED_PRODUCT_CATEGORY('detail',$,(#5)) ;",
              "#9=PRODUCT_CATEGORY_RELATIONSHIP(' ',' ',#7,#8) ;",
              "#10=COORDINATED_UNIVERSAL_TIME_OFFSET(0,0,.AHEAD.) ;",
              "#11=CALENDAR_DATE(" + str(getattr(d, 'year')) + "," + str(
                  getattr(d, 'month')) + "," + str(
                  getattr(d, 'day')) + ") ;",
              "#12=LOCAL_TIME(" + str(getattr(d, 'hour')) + "," + str(
                  getattr(d, 'minute')) + "," + str(
                  getattr(d, 'second')) + ".,#10) ;",
              "#13=DATE_AND_TIME(#11,#12) ;",
              "#14=PRODUCT_DEFINITION('',' ',#6,#3) ;",
              "#15=SECURITY_CLASSIFICATION_LEVEL('unclassified') ;",
              "#16=SECURITY_CLASSIFICATION(' ',' ',#15) ;",
              "#17=DATE_TIME_ROLE('classification_date') ;",
              "#18=CC_DESIGN_DATE_AND_TIME_ASSIGNMENT(#13,#17,(#16)) ;",
              "#19=APPROVAL_ROLE('APPROVER') ;",
              "#20=APPROVAL_STATUS('not_yet_approved') ;",
              "#21=APPROVAL(#20,' ') ;",
              "#22=PERSON(' ',' ',' ',$,$,$) ;",
              "#23=ORGANIZATION(' ',' ',' ') ;",
              "#24=PERSONAL_ADDRESS(' ',' ',' ',' ',' ',' ',' ',' ',' '," +
              "' ',' ',' ',(#22),' ') ;",
              "#25=PERSON_AND_ORGANIZATION(#22,#23) ;",
              "#26=PERSON_AND_ORGANIZATION_ROLE('classification_officer') ;",
              "#27=CC_DESIGN_PERSON_AND_ORGANIZATION_ASSIGNMENT(#25,#26," +
              "(#16)) ;",
              "#28=DATE_TIME_ROLE('creation_date') ;",
              "#29=CC_DESIGN_DATE_AND_TIME_ASSIGNMENT(#13,#28,(#14)) ;",
              "#30=CC_DESIGN_APPROVAL(#21,(#16,#6,#14)) ;",
              "#31=APPROVAL_PERSON_ORGANIZATION(#25,#21,#19) ;",
              "#32=APPROVAL_DATE_TIME(#13,#21) ;",
              "#33=CC_DESIGN_PERSON_AND_ORGANIZATION_ASSIGNMENT(#25,#34," +
              "(#6)) ;",
              "#34=PERSON_AND_ORGANIZATION_ROLE('design_supplier') ;",
              "#35=CC_DESIGN_PERSON_AND_ORGANIZATION_ASSIGNMENT(#25,#36," +
              "(#6,#14)) ;",
              "#36=PERSON_AND_ORGANIZATION_ROLE('creator') ;",
              "#37=CC_DESIGN_PERSON_AND_ORGANIZATION_ASSIGNMENT(#25,#38," +
              "(#5)) ;",
              "#38=PERSON_AND_ORGANIZATION_ROLE('design_owner') ;",
              "#39=CC_DESIGN_SECURITY_CLASSIFICATION(#16,(#6)) ;",
              "",
              "#40=PRODUCT_DEFINITION_SHAPE(' ',' ',#14) ;",
              "#41=(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.)) ;",
              "#42=(NAMED_UNIT(*)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.)) ;",
              "#43=(NAMED_UNIT(*)SI_UNIT($,.STERADIAN.)SOLID_ANGLE_UNIT()) ;",
              "#44=UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.005),#41," +
              "'distance_accuracy_value','CONFUSED CURVE" +
              " UNCERTAINTY') ;",
              "#45=(GEOMETRIC_REPRESENTATION_CONTEXT(3)" +
              "GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#44))" +
              "GLOBAL_UNIT_ASSIGNED_CONTEXT((#41,#42,#43))" +
              "REPRESENTATION_CONTEXT(' ',' ')) ;",
              "",
              "#46=CARTESIAN_POINT(' ',(0.,0.,0.)) ;",
              "#47=AXIS2_PLACEMENT_3D(' ',#46,$,$) ;",
              "#48=SHAPE_REPRESENTATION(' ',(#47),#45) ;",
              "#49=SHAPE_DEFINITION_REPRESENTATION(#40,#48) ;",
              "",
              "/* Part Specification */",
              "",
              "ENDSEC;",
              "END-ISO-10303-21;"]
file_array = [i + "\n" for i in file_array]

index1 = file_array.index("/* Part Specification */\n")
initial_work_array = list(filter(lambda k: k.startswith('#'), file_array))

highest_index = line_index(sorted(initial_work_array, key=line_index)[-1])
current_index = highest_index + 1
part_body_index = 1
work_array = []
print("[DONE]")

generate_assembly(in_array, in_depth, in_coeff)
