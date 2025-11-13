import functools
import os
import sys
from io import StringIO

import numpy as np
from tifffile import imwrite
from gvxrPython3 import gvxr, json2gvxr
import time
from tqdm import tqdm


def debuggable_print(debug):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            original_stdout = sys.stdout
            if not debug:
                sys.stdout = StringIO()
            try:
                result = func(*args, **kwargs)
            finally:
                if not debug:
                    sys.stdout = original_stdout
            return result

        return wrapper

    return decorator


@debuggable_print(debug=True)
def GVXRCalculate(JSONFileName: str = "wwz/mytest2.json", saveFlag: bool = False):
    start_time = time.time()
    print(f"[RUNNING] __file__ = {__file__}")

    # --- 载入 JSON 并初始化场景 ---
    try:
        json2gvxr.initGVXR(JSONFileName)
    except Exception as e:
        print("Error initializing GVXR:", e)
        return

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

    numProj = int(json2gvxr.params["Scan"]["NumberOfProjections"])
    final_ang = float(json2gvxr.params["Scan"]["FinalAngle"])
    include_final = bool(json2gvxr.params["Scan"]["IncludeFinalAngle"])

    if saveFlag:
        # [!!] 4. 修复：删除了本行开头的 "G[" [!!]
        output_root = json2gvxr.params["Scan"]["OutPath"]
        out_folder_prefix = json2gvxr.params["Scan"]["OutFolder"]

        projection_path = os.path.join(
            output_root,
            f'{out_folder_prefix}_{material_name}_density_{density}_'
            f'DSD_{dsd}_DSO_{dso}_nDetector_{nDetectorX}_sDetector_{sDetectorX}_numproj_{numProj}'
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
        int(numProj),  # 3. numberOfProjections
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

    print(f"[INFO] CT acquisition complete. Use time: {time.time() - start_time:.2f} seconds.")

    # 取回投影与角度（方便你校验是否包含末角）
    angle_set = list(gvxr.getAngleSetCT())

    projection_set = np.array(gvxr.getLastProjectionSet(), dtype=np.float32)

    print(f"[INFO] Angles ({len(angle_set)}): {angle_set[:10]}{' ...' if len(angle_set) > 10 else ''}")

    if saveFlag:
        try:
            # --- 保存 .tif ---
            print(f"[INFO] Saving {len(projection_set)} projections to: {projection_path}")
            for i, proj in enumerate(tqdm(projection_set, desc="Saving projections")):
                name = os.path.join(projection_path, f"projection-{i:04d}.tif")
                imwrite(name, proj)
            print("[INFO] All projections saved. Done.")
        except Exception as e:
            print("Error saving projections:", e)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"[INFO] Total execution time: {elapsed_time:.2f} seconds.")

    return projection_set, angle_set


@debuggable_print(debug=True)
def saveTif(projection_set, output_path):
    # --- 保存 .tif ---
    try:
        os.makedirs(output_path, exist_ok=True)
        print(f"[INFO] Saving {len(projection_set)} projections to: {output_path}")

        for i, proj in enumerate(tqdm(projection_set, desc="Saving projections")):

            name = os.path.join(output_path, f"projection-{i:04d}.tif")
            print(name)
            imwrite(name, proj)

        print("[INFO] All projections saved. Done.")
    except Exception as e:
        print("Error saving projections:", e)


def getTif(projection_set):
    tifList = []
    for i, proj in enumerate(tqdm(projection_set, desc="Saving projections")):
        tifList.append(proj)
    return tifList


if __name__ == "__main__":
    projection, angle = GVXRCalculate("wwz/mytest2.json")
    tif = getTif(projection)
    print(len(tif))
    # saveTif(projection, "wwz/mytest2")
