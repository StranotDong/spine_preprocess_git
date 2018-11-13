from utils.utils import nameRules as nr
from utils.utils import *
import utils.geometryOp as go

import SimpleITK as sitk
import cv2

import numpy as np
import math
from scipy import ndimage

'''
if the straight box is not square (because of out of image bounds), 
mirror the pixel at the eage to make it square
input:
    piece: the matrix of the piece
    pieceRange: the range of the piece on the original image [x_max, x_min, y_max, y_min]
    img_shape: the shape of the original image
return
    the processed piece
'''
def _mirror_to_square(piece, pieceRange, img_shape):
    x_max = pieceRange[0]
    x_min = pieceRange[1]
    y_max = pieceRange[2]
    y_min = pieceRange[3]
    
    img_x_max = img_shape[1]
    img_y_max = img_shape[0]

    # mirror the pixels between x_min~0, y_min~0, x_max~img_x_max, y_max~img_y_max
    if x_min < 0:
        pixel_to_mirror = piece[:, 0:-x_min]
        mirrored = np.flip(pixel_to_mirror, axis=1)
        piece = np.concatenate((mirrored, piece), axis=1)
    if x_max > img_x_max:
        temp_x = x_max - img_x_max
        pixel_to_mirror = piece[:, piece.shape[1]-temp_x:piece.shape[1]]
        mirrored = np.flip(pixel_to_mirror, axis=1)
        piece = np.concatenate((piece, mirrored), axis=1)
    if y_max > img_y_max:
        temp_y = y_max - img_y_max
        pixel_to_mirror = piece[piece.shape[0]-temp_y:piece.shape[0], :]
        mirrored = np.flip(pixel_to_mirror, axis=0)
        piece = np.concatenate((piece, mirrored), axis=0)
    if y_min < 0:
        pixel_to_mirror = piece[0:-y_min, :]
        mirrored = np.flip(pixel_to_mirror, axis=0)
        piece = np.concatenate((mirrored, piece), axis=0)
    
    return piece

'''
get a piece from an image
input:
    npa: the matrix of image
    xy_range: x range and y range of the piece on the image
return: 
    the piece
'''
def get_one_piece(npa, xy_range):
#     print(npa)
    y_limit, x_limit = npa.shape
    
    x_max = min(int(xy_range[0]), x_limit)
    x_min = max(int(xy_range[1]), 0)
    y_max = min(int(xy_range[2]), y_limit)
    y_min = max(int(xy_range[3]), 0)
    npa_ = npa[y_min:y_max, x_min:x_max]
#     print(npa)
    
    # if there is some part out of the range of the whole image, do interpolation
    npa_ = _mirror_to_square(npa_, xy_range, npa.shape)

    return npa_

'''
get all pieces from one image
input: 
    num_labelled_VBs: total number of labelled VBs in this image
    storedInfo: the data of the image from the StoredDict
    VBLabelList: the list of VB names
    bias: a list contain bias for the bounding box lines. 
        If 4 elements are given, then the order is superior, posterior, inferior, anterior, all positive
        If 2 elements are given, then the order is superior, posterior, and inferior = superior, anterior = posterior
    square: if force the vb bounding box to be square
return:
    pieceDict: the image matrix bounded by the "large straight" box, for each VB piece
    pieceBoxDict: the corner coodinates of the VB bounding box in the piece, for each VB
    pieceRangeDict: the x range and y range of the piece on the origial image for each VB piece
    BoxDict: the corner coodinates of the VB bounding box in the original image, for each VB
'''
def get_all_pieces(num_labelled_VBs, StoredInfo, img_path, bias=[100,100], square=False):
    pieceBoxDict = {}
    pieceDict = {}
    pieceRangeDict = {}
    BoxDict = {}
    for i in range(num_labelled_VBs):
        # get bounding box
        vb2 = nr.VBLabelList[i]
        p2 = StoredInfo[vb2][nr.Coords]
        if i == 0:        
            vb3 = nr.VBLabelList[i+1]        
            p3 = StoredInfo[vb3][nr.Coords]
            vx = go.get_normal_vector(go.get_vector(p2,p3))
            cen = p2
        elif i == num_labelled_VBs - 1:
            vb3 = nr.VBLabelList[i-1]
            p3 = StoredInfo[vb3][nr.Coords]
            vx = go.get_normal_vector(go.get_vector(p2,p3))
            cen = p2
        else:  
            vb1 = nr.VBLabelList[i-1]
            vb3 = nr.VBLabelList[i+1]
            p1 = StoredInfo[vb1][nr.Coords]
            p3 = StoredInfo[vb3][nr.Coords]
            cen, vx = go.get_angle_bisector(p1,p2,p3)

        cor = StoredInfo[vb2][nr.CorCoords]
    #     print(cen, cor)
        # ab_box on original image
        ab_box, rel_box = go.get_box_corners(cen, cor, vx, bias,square = square)
        BoxDict[nr.VBLabelList[i]] = ab_box
        # the large box
        xy_range = go.get_straight_box(ab_box)
        pieceRangeDict[nr.VBLabelList[i]] = xy_range

        img = sitk.ReadImage(img_path)[:,:,0]
        npa = np.array(sitk.GetArrayViewFromImage(img))
        piece = get_one_piece(npa, xy_range)
        pieceDict[nr.VBLabelList[i]] = piece
                
        # new ab_box for each piece
        x_max = xy_range[0]
        x_min = xy_range[1]
        y_max = xy_range[2]
        y_min = xy_range[3]
        piece_ab_box = []
        for j in range(4):
            piece_ab_box.append((ab_box[j][0]-x_min, ab_box[j][1]-y_min))
        pieceBoxDict[nr.VBLabelList[i]] = piece_ab_box
        
    return pieceDict, pieceBoxDict, BoxDict, pieceRangeDict

'''
judge if back is towards left or right
'''
def img_orientation(piece_ab_box):
    # judge the orientation of the vb: whether the posterior is oriented to left or right
    if piece_ab_box[0][0] > piece_ab_box[3][0]: # posterior is on the right side of the image
        right = True
    else:
        right = False
    return right

'''
rotate image given the ab_box
input:
    img: the matrix of image
    piece_ab_box: the corner coodinates of the vb bounding box
return:
    rotated_img: the matrix of rotated image
    rotated_box: the coordinates of the vb bounding box in rotated image
    right: if the back is towards right. If right = None, automatically determine the orientation.
'''
def image_rotate(img, piece_ab_box, right=None):
    # judge the orientation of the vb: whether the posterior is oriented to left or right
    if right == None:
        right = img_orientation(piece_ab_box)
    y_diff = piece_ab_box[0][1] - piece_ab_box[3][1]
    x_diff = piece_ab_box[0][0] - piece_ab_box[3][0]
    if right:        
        degree = math.degrees(math.atan2(y_diff, x_diff))
    else:
        degree = math.degrees(math.atan2(y_diff, x_diff))-180
    
    height, width = img.shape
    image_center = (width/2, height/2) # getRotationMatrix2D needs coordinates in reverse order (width, height) compared to shape

    rotation_mat = cv2.getRotationMatrix2D(image_center, degree, 1.)

    # rotation calculates the cos and sin, taking absolutes of those.
    abs_cos = abs(rotation_mat[0,0]) 
    abs_sin = abs(rotation_mat[0,1])

    # find the new width and height bounds
    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)

    # subtract old image center (bringing image back to origo) and adding the new image center coordinates
    rotation_mat[0, 2] += bound_w/2 - image_center[0]
    rotation_mat[1, 2] += bound_h/2 - image_center[1]

    # rotate image with the new bounds and translated rotation matrix
    rotated_img = cv2.warpAffine(img, rotation_mat, (bound_w, bound_h))
    
    
    rotated_box = []
    rad = math.radians(-degree)
#     print(degree, rad)
    for i in range(4):
        new_x = int(math.cos(rad)*(piece_ab_box[i][0] - image_center[0]) - \
            math.sin(rad)*(piece_ab_box[i][1] - image_center[1]) + bound_w/2)
        new_y = int(math.sin(rad)*(piece_ab_box[i][0] - image_center[0]) + \
            math.cos(rad)*(piece_ab_box[i][1] - image_center[1]) + bound_h/2)
        rotated_box.append((new_x, new_y))
            
    return rotated_img, rotated_box


'''
resize image
'''
def image_resize(img, x_scale, y_scale, interpolation = cv2.INTER_CUBIC):
    resized_img = cv2.resize(img, None,fx=x_scale, fy=y_scale, interpolation = interpolation)
    return resized_img
