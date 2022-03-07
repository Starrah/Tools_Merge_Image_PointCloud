"""
 @leofansq
 Main function
"""
import sys
# sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import cv2
import numpy as np

import os
import time
from tqdm import tqdm

from func import find_files, cal_proj_matrix, cal_proj_matrix_raw, load_img, load_lidar, project_lidar2img, generate_colorpc, save_pcd

#**********************************************************#
#                         Option                           #
#**********************************************************#
################## FILE PATH ###################
# Calib File
CALIB_TYPE = 0      # 0:All parameters in one file. e.g. KITTI    1: Seperate into two files. e.g. KITTI raw
# if CALIB_TYPE == 0
CALIB = "./calib/000001.txt"
# if CALIB_TYPE == 1    
CAM2CAM = "./calib/calib_cam_to_cam.txt"
LIDAR2CAM = "./calib/calib_velo_to_cam.txt"

# Source File
IMG_PATH = "./img/"
LIDAR_PATH = "./lidar/"

# Save File
SIMG_PATH = "./result/img/"
SPC_PATH = "./result/pcd/"
SBEV_PATH = "./result/bev/"
SFV_PATH = "./result/fv/"

################# PARAMETER ####################
CAM_ID = 0

#**********************************************************#
#                     Main Function                        #
#**********************************************************#
def main():
    time_cost = []

    # Calculate P_matrix
    if CALIB_TYPE:
        p_matrix = cal_proj_matrix_raw(CAM2CAM, LIDAR2CAM, CAM_ID)
    else:
        p_matrix = cal_proj_matrix(CALIB, CAM_ID)

    # Batch Process
    for img_path in tqdm(find_files(IMG_PATH, '*.png')):
        _, img_name = os.path.split(img_path)
        pc_path = LIDAR_PATH + img_name[:-4] + '.bin'
        # print ("Working on", img_name[:-4])        
        start_time = time.time()

        # Load img & pc
        img = load_img(img_path)
        pc = load_lidar(pc_path)

        # Project & Generate Image & Save
        points = project_lidar2img(img, pc, p_matrix, debug=True)

        pcimg = img.copy()
        depth_max = np.max(pc[:,0])
        for idx,i in enumerate(points):
            color = int((pc[idx,0]/depth_max)*255)
            cv2.rectangle(pcimg, (int(i[0]-1),int(i[1]-1)), (int(i[0]+1),int(i[1]+1)), (0, 0, color), -1)
        
        cv2.imwrite(SIMG_PATH+img_name, pcimg)

        # Generate PC with Clor & Save
        pc_color = generate_colorpc(img, pc, points)

        save_pcd(SPC_PATH + img_name[:-4] + ".pcd", pc_color)

        # BEV
        img_bev = np.zeros((2000, 2000, 3))
        for i in pc_color:
            img_bev[-int(i[0]*10)+1999, int(-i[1]*10)+1000] = [i[5], i[4], i[3]]
        cv2.imwrite(SBEV_PATH+img_name[:-4]+"_bev.png", img_bev)

        # FV
        img_fv = np.zeros((1000,2000,3))
        for i in pc_color:
            img_fv[-int(i[2]*10+500), int(-i[1]*10)+1000] = [i[5], i[4], i[3]]
        cv2.imwrite(SFV_PATH+img_name[:-4]+"_fv.png", img_fv)
        
        # Time Cost
        end_time = time.time()
        time_cost.append(end_time - start_time)

    print ("Mean_time_cost:", np.mean(time_cost))
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
