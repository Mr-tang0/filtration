#!/usr/-bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np
from tifffile import imwrite
from gvxrPython3 import gvxr, json2gvxr
import time
from tqdm import tqdm


def initGVXR(JSONFileName: str):
    pass


def main():
    start_time = time.time()

    print(f"[RUNNING] __file__ = {__file__}")

    # --- 静默初始化阶段冗余输出（跨平台） ---
    original_stdout = sys.stdout
    try:
        sys.stdout = open(os.devnull, 'w')
    except Exception as e:
        print("Error opening stdout:", e)
        pass

    # --- 载入 JSON 并初始化场景 ---
    JSON_fname = "mytest2.json"
    json2gvxr.initGVXR(JSON_fname)

    # 恢复 stdout，后面会有提示信息
    sys.stdout = original_stdout

    # --- 读取参数并拼输出路径 ---
    sample0 = json2gvxr.params["Samples"][0]
    material_name = sample0["Material"][1]  # 例: "Ti90Al6V4"
    density = sample0["Density"]  # 例: 0.5 g/cm3

    src_pos = json2gvxr.params["Source"]["Position"]  # [-120,0,0,"mm"]
    det_pos = json2gvxr.params["Detector"]["Position"]  # [ 120,0,0,"mm"]
    dso = abs(float(src_pos[0]))
    dsd = dso + abs(float(det_pos[0]))

    nDetectorX = int(json2gvxr.params["Detector"]["NumberOfPixels"][0])
    sDetectorX = float(json2gvxr.params["Detector"]["Size"][0])

    numproj = int(json2gvxr.params["Scan"]["NumberOfProjections"])
    final_ang = float(json2gvxr.params["Scan"]["FinalAngle"])
    include_final = bool(json2gvxr.params["Scan"]["IncludeFinalAngle"])

    # [!!] 4. 修复：删除了本行开头的 "G[" [!!]
    output_root = json2gvxr.params["Scan"]["OutPath"]
    out_folder_prefix = json2gvxr.params["Scan"]["OutFolder"]
    projection_path = os.path.join(
        output_root,
        f'{out_folder_prefix}_{material_name}_density_{density}_'
        f'DSD_{dsd}_DSO_{dso}_nDetector_{nDetectorX}_sDetector_{sDetectorX}_numproj_{numproj}'
    )
    os.makedirs(projection_path, exist_ok=True)

    # --- 初始化源/谱、探测器、样品、噪声 ---
    json2gvxr.initSourceGeometry()
    json2gvxr.initSpectrum(verbose=0)
    print(f"[INFO] Spectrum: {json2gvxr.params['Source']['Beam']['TextFile']} "
          f"in {json2gvxr.params['Source']['Beam']['Unit']}")

    json2gvxr.initDetector()
    json2gvxr.initSamples()
    gvxr.moveToCentre()

    gvxr.usePoissonNoise()
    print("[INFO] Poisson noise enabled")

    # --- 用 computeCTAcquisition 计算整套投影（v2.0.10 接口逐分量传参） ---
    first_angle = 0.0
    last_angle = final_ang
    n_white = 0

    # 旋转中心与旋转轴（单位沿用场景几何，通常是 mm；轴为单位向量）
    centre_x, centre_y, centre_z = 0.0, 0.0, 0.0
    axis_x, axis_y, axis_z = 0.0, 0.0, 1.0

    integrate_energy = True
    verbose = 1

    print("[INFO] Starting CT acquisition (this may take a moment)...")

    # 让 gVXR 只在内存里生成投影（不自动落盘）
    gvxr.computeCTAcquisition(
        "",  # 1. projectionOutputPath
        "",  # 2. screenshotOutputPath
        int(numproj),  # 3. numberOfProjections
        float(first_angle),  # 4. firstAngle (deg)
        bool(include_final),  # 5. includeLastAngleFlag (int -> bool)
        float(last_angle),  # 6. lastAngle (deg)
        int(n_white),  # 7. numberOfWhiteImagesInFlatField
        float(centre_x), float(centre_y), float(centre_z),  # 8, 9, 10. centreOfRotation
        "mm",  # 11. aUnitOfLength (Added)
        float(axis_x), float(axis_y), float(axis_z),  # 12, 13, 14. axisOfRotation
        bool(integrate_energy),  # 15. integrateEnergyFlag
        int(verbose)  # 16. verbose
    )

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"[INFO] Total execution time: {elapsed_time:.2f} seconds.")

    print("[INFO] CT acquisition complete.")

    # 取回投影与角度（方便你校验是否包含末角）
    angle_set = list(gvxr.getAngleSetCT())

    projection_set = np.array(gvxr.getLastProjectionSet(), dtype=np.float32)

    print(f"[INFO] Angles ({len(angle_set)}): {angle_set[:10]}{' ...' if len(angle_set) > 10 else ''}")

    # --- 保存 .tif ---
    print(f"[INFO] Saving {len(projection_set)} projections to: {projection_path}")

    for i, projection in enumerate(tqdm(projection_set, desc="Saving projections")):
        fname = os.path.join(projection_path, f"projection-{i:04d}.tif")
        imwrite(fname, projection)

    print("[INFO] All projections saved. Done.")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"[INFO] Total execution time: {elapsed_time:.2f} seconds.")


if __name__ == "__main__":
    main()
