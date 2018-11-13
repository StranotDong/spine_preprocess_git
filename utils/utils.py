import csv
import os
from os.path import exists, join

class nameRules:
    # def __init__(:
        # edit/view mode
        edit = 'edit'
        view = 'view'
        
        # temp_file
        temp_filename = '.usrnm'

        # vb list
        VBLabelList = ['S1', 'L5','L4','L3','L2','L1', \
                           'T12','T11','T10','T9','T8','T7',\
                           'T6','T5','T4','T3']

        # coordinate types
        CoordTypeList = ['cen', 'cor']

        # VBDict keys
        Coords = 'Coords'
        CorCoords = 'CorCoords'
        Fracture = 'Fracture'
        
        # controversial dict keys
        Modifier = 'Modifier'
        ConPart = 'ConPart'
        ConStatus = 'ConStatus'

        # fracture types
        normal = 'normal'
        ost = 'osteoporotic fracture'
        non_ost = 'non-osteoporotic deformity'

        # touch/untouch status
        touch = 'T'
        untouch = 'U'

        # contoversial status
        controversial = 'C'
        uncontroversial = 'UC'

        # readable status
        readable = 'R'
        unameRuleseadable = 'UR'

        # csv headers
        head_imgID = 'Image ID'
        head_status = 'Status'
        head_vbLabel = 'VB Label'
        head_cenX = 'Center X'
        head_cenY = 'Center Y'
        head_corX = 'Corner X'
        head_corY = 'Corner Y'
        head_frac = 'Fracture?'
        head_modifier = 'Last Modifier'
        head_conStatus = 'Controversial Status'
        head_conParts = 'Comments'
        head_readableStatus = 'Readable?'

        csv_headers = [head_imgID, head_status, head_vbLabel, head_cenX, head_cenY, head_corX, head_corY, head_frac, head_modifier, head_conStatus, head_conParts, head_readableStatus]

        # save status
        saved = 'saved'
        unsaved = 'unsaved'
"""
Construct the ImgIDList
"""
def get_ImgIDList(root_dir):
    rst = []
    for root, dirs, files in os.walk(root_dir):     
        for file in files:
            if file.endswith(".dcm"):
            ##############################################################
#                 rst.append(file)
            ##############################################################
                rst.append(join(root,file))
    return rst



"""
Read the csv file and construct StoreDict and Status Dict
Delete the unameRuleseadable, untouched, controvesial images in StoreList and ImgIDList
"""
def label_dict_constructor(fpath, ImgIDList):
    StoreDict = {}
    for ID in ImgIDList:
        VBDict = dict((vb, {nameRules.Coords:(None,None), nameRules.CorCoords:(None,None), nameRules.Fracture:None}) \
                   for vb in nameRules.VBLabelList)
        StoreDict[ID] = VBDict
    if exists(fpath):
        with open(fpath) as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row[nameRules.head_readableStatus] == nameRules.unameRuleseadable or row[nameRules.head_status] == nameRules.untouch or row[nameRules.head_conStatus] == nameRules.controversial:
                    StoreDict.pop(row[nameRules.head_imgID], None)
                    if row[nameRules.head_imgID] in ImgIDList:
                        ImgIDList.remove(row[nameRules.head_imgID])
                    continue

                if row[nameRules.head_cenX] != '' and row[nameRules.head_cenY] != '':
                    StoreDict[row[nameRules.head_imgID]][row[nameRules.head_vbLabel]][nameRules.Coords] = (float(row[nameRules.head_cenX]), float(row[nameRules.head_cenY]))
                if row[nameRules.head_corX] != '' and row[nameRules.head_corY] != '':
                    StoreDict[row[nameRules.head_imgID]][row[nameRules.head_vbLabel]][nameRules.CorCoords] = (float(row[nameRules.head_corX]), float(row[nameRules.head_corY]))
                if row[nameRules.head_frac] != '':
                    StoreDict[row[nameRules.head_imgID]][row[nameRules.head_vbLabel]][nameRules.Fracture] = row[nameRules.head_frac]

    return StoreDict

"""
get the number of labelled VB for each image
"""
def VB_num_dict_constructor(StoreDict):
    vb_num_dict = {}
    for img in StoreDict:
        vb_dict = StoreDict[img]
        co = 0
        for vb in vb_dict:
            if vb_dict[vb][nameRules.Coords][0] != None and vb_dict[vb][nameRules.Coords][1] != None \
            and vb_dict[vb][nameRules.CorCoords][0] != None and vb_dict[vb][nameRules.CorCoords][1] != None:
                co += 1
        vb_num_dict[img] = co
    
    return vb_num_dict
