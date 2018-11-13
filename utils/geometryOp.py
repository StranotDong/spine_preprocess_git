import math
import numpy as np


"""
get the vector of two points
    inputs: two tuples of coodinates, p1, p2
    output: the tuple of the normalized vector, p1 -> p2, i.e., p2-p1
"""
def get_vector(p1, p2):
    x = p2[0] - p1[0]
    y = p2[1] - p1[1]
    return (x, y)

def l2_norm(p):
    l = math.sqrt(p[0]**2 + p[1]**2) 
    return l

'''
get normalized vector. Input is a vector, output is the normalized vector
'''
def vector_normalization(p):
    l = l2_norm(p)
    return (p[0]/l, p[1]/l)


'''
get the bisector of the two vectors
'''
def get_bisector_vector(v1, v2):
    v1_normal = vector_normalization(v1)
    v2_normal = vector_normalization(v2)
    midpoint_x = (v1_normal[0] + v2_normal[0])/2
    midpoint_y = (v1_normal[1] + v2_normal[1])/2
    return (midpoint_x, midpoint_y)

'''
given three points, p1 and p2 are connected and p2 and p3 are connected. 
Get the bisector and the connected points, i.e., point-norm form to represent the bisector line.
'''
def get_angle_bisector(p1,p2,p3):
    v21 = get_vector(p2,p1)
    v23 = get_vector(p2,p3)
    v_bi = get_bisector_vector(v21, v23)
    return p2, v_bi


'''
get the normal vector of a given vector
'''
def get_normal_vector(v):
    return (v[1], -v[0])


def get_inverse_dir_vector(v):
    return (-v[0], -v[1])

'''
inner multiplication
'''
def inner_mul(v1, v2):
    return v1[0]*v2[0]+v1[1]*v2[1]

'''
construct the relative coordinates system. 
x axes points to posterior, y axes points to superior, 
orignal points is center points

inputs: 
    cen: the center point of the vb
    cor: the cornor point of the vb
    vx: the horizontal directior, not necessarily points to posterior for now. 
outpurs: original points, x positive direction, y positive direction w.r.t absolute coordinate system
'''
def get_rel_coord_system(cen, cor,  vx):
    d = get_vector(cen,cor)
    if inner_mul(d, vx) < 0:
        vx = get_inverse_dir_vector(vx)
    vy = get_normal_vector(vx)
    if inner_mul(d, vy) < 0:
        vy = get_inverse_dir_vector(vy)
    return cen, vector_normalization(vx),vector_normalization(vy)

'''
coordinate transformation from absolute to relative
inputs: 
    ab_coords: absolute coordinates
    rel_ori: relative original point wrt absolute coordinate system
    rel_vx: relative x positive direction (normalized)
    rel_vy: relative y positive direction (normalized)
'''
def coord_transfrom_ab2rel(ab_coords, rel_ori, rel_vx, rel_vy):
    transplate_coords = get_vector(rel_ori, ab_coords)
    rel_x = inner_mul(transplate_coords, rel_vx)
    rel_y = inner_mul(transplate_coords, rel_vy)
    return (rel_x, rel_y)
    
'''
coordinate transformation from relative to absolute
inputs: 
    rel_coords: relative coordinates
    rel_ori: relative original point wrt absolute coordinate system
    rel_vx: relative x positive direction (normalized)
    rel_vy: relative y positive direction (normalized)
'''
def coord_transfrom_rel2ab(rel_coords, rel_ori, rel_vx, rel_vy):
    ab_vx = (1,0)
    ab_vy = (0,1)
    ab2rel_vx = (inner_mul(ab_vx, rel_vx), inner_mul(ab_vx, rel_vy))
    ab2rel_vy = (inner_mul(ab_vy, rel_vx), inner_mul(ab_vy, rel_vy))
    ab_ori = get_inverse_dir_vector(rel_ori)
    ab2rel_ori = (inner_mul(ab_ori, rel_vx), inner_mul(ab_ori, rel_vy))
    return coord_transfrom_ab2rel(rel_coords, ab2rel_ori, ab2rel_vx, ab2rel_vy)

# p = (5,6)
# ori = (1,1)
# vx = (-1,-1)
# cor = (1,2)
# ori, vx, vy = get_rel_coord_system(ori, cor, vx)
# rel_coords = coord_transfrom_ab2rel(p, ori, vx, vy)
# print(rel_coords)
# print(coord_transfrom_rel2ab(rel_coords, ori, vx,vy))
'''
get symmetric point via x axes
'''
def get_sym_point_x(p):
    return (p[0], -p[1])

'''
get symmetric point via y axes
'''
def get_sym_point_y(p):
    return (-p[0], p[1])

'''
get symmetric point via original point
'''
def get_sym_point_ori(p):
    return (-p[0], -p[1])

'''
vector add
'''
def vector_add(p1, p2):
    return (p1[0]+p2[0], p1[1]+p2[1])

'''
get the bounding box corners
inputs:
    cen: center coordinates
    cor: corner coordinates
    hor_vec: direction vector of horizontal lines/length
    bias: a list contain bias for the bounding box lines. 
    If 4 elements are given, then the order is superior, posterior, inferior, anterior, all positive
    If 2 elements are given, then the order is superior, posterior, and inferior = superior, anterior = posterior
    square: if force the box to be square

outputs: two lists contains the absulote coordinates and relative coordinates (to cen) of the 4 corners are returned, the order is from sup-post, post-in, in-an, an-sup
some corner may go out of the image. We don't care here. We fix this in get_piece function
'''
def get_box_corners(cen, cor, hor_vec, bias, square=False):
    # get the full bias list
    if len(bias) == 2:
        bias_sup = bias[0]
        bias_post = bias[1]
        bias_inf = bias_sup
        bias_ant = bias_post
    elif len(bias) == 4:
        bias_sup = bias[0]
        bias_post = bias[1]
        bias_inf = bias[2]
        bias_ant = bias[3]

    # get relative coordinate system
    ori, vx, vy = get_rel_coord_system(cen,cor,hor_vec)

    # get relative coordinates of sup-post corner point
    rel_sup_post = coord_transfrom_ab2rel(cor, ori, vx, vy)
    if square:
        if abs(rel_sup_post[0]) > abs(rel_sup_post[1]):
            temp_x = rel_sup_post[0]
            temp_y = rel_sup_post[1]/abs(rel_sup_post[1])*abs(rel_sup_post[0])
        else:
            temp_y = rel_sup_post[1]
            temp_x = rel_sup_post[0]/abs(rel_sup_post[0])*abs(rel_sup_post[1])
        rel_sup_post = (temp_x, temp_y)
    # get other corner points wrt relative coordinates
    rel_post_inf = get_sym_point_x(rel_sup_post)
    rel_inf_ant = get_sym_point_ori(rel_sup_post)
    rel_ant_sup = get_sym_point_y(rel_sup_post)

    # get the bounding box corner wrt relative coords
    rel_box = []
    rel_box.append(vector_add(rel_sup_post, (bias_post, bias_sup)))
    rel_box.append(vector_add(rel_post_inf, (bias_post, -bias_inf)))
    rel_box.append(vector_add(rel_inf_ant, (-bias_ant, -bias_inf)))
    rel_box.append(vector_add(rel_ant_sup, (-bias_ant, bias_sup)))

    # get the bounding box corner wrt absolute coords
    ab_box = []
    for c in rel_box:
        ab_box.append(coord_transfrom_rel2ab(c, ori, vx, vy))

    return ab_box, rel_box


'''
distance between two points
'''
def pair_points_distance(p1,p2):
    return math.sqrt((p1[0]-p2[0])**2+ (p1[1]-p2[1])**2)


def get_straight_box(ab_box):
    x = np.array([ab_box[0][0], ab_box[1][0], ab_box[2][0], ab_box[3][0]])
    y = np.array([ab_box[0][1], ab_box[1][1], ab_box[2][1], ab_box[3][1]])
    x_max = np.max(x)
    x_min = np.min(x)
    y_max = np.max(y)
    y_min = np.min(y)
    
    # rst.append((x_max, y_min))
    # rst.append((x_max, y_max))
    # rst.append((x_min, y_max))
    # rst.append((x_min, y_min))

    return list([int(x_max), int(x_min), int(y_max), int(y_min)])


"""
polar coordinates to cartesian coordinates
r is positive
theta is in radian representation
"""
def polar2cart(r, theta):
    return r*math.cos(theta), r*math.sin(theta)

def cart2polar(x, y):
    r = l2_norm((x,y))
    theta = math.atan2(y,x)
    return r, theta
