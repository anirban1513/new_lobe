from __future__ import print_function, division
import os
import numpy as np
import pandas as pd
import SimpleITK as sitk


def getRangImageRange(image, index=0):
    """
    :param image:
    :return:rang of image depth
    """
    startposition = 0
    endposition = 0
    for z in range(0, image.shape[index], 1):
        if index == 0:
            notzeroflag = np.max(image[z, :, :])
        elif index == 1:
            notzeroflag = np.max(image[:, z, :])
        elif index == 2:
            notzeroflag = np.max(image[:, :, z])
        if notzeroflag:
            startposition = z
            break
    for z in range(image.shape[index] - 1, -1, -1):
        if index == 0:
            notzeroflag = np.max(image[z, :, :])
        elif index == 1:
            notzeroflag = np.max(image[:, z, :])
        elif index == 2:
            notzeroflag = np.max(image[:, :, z])
        if notzeroflag:
            endposition = z
            break
    return startposition, endposition


def resize_image_itkwithsize(itkimage, newSize, originSize, resamplemethod=sitk.sitkNearestNeighbor):
    """
    image resize withe sitk resampleImageFilter
    :param itkimage:
    :param newSize:such as [1,1,1]
    :param resamplemethod:
    :return:
    """
    resampler = sitk.ResampleImageFilter()
    originSize = np.array(originSize)
    newSize = np.array(newSize)
    factor = originSize / newSize
    originSpcaing = itkimage.GetSpacing()
    newSpacing = factor * originSpcaing
    resampler.SetReferenceImage(itkimage)
    resampler.SetOutputSpacing(newSpacing.tolist())
    resampler.SetSize(newSize.tolist())
    resampler.SetTransform(sitk.Transform(3, sitk.sitkIdentity))
    resampler.SetInterpolator(resamplemethod)
    itkimgResampled = resampler.Execute(itkimage)
    imgResampled = sitk.GetArrayFromImage(itkimgResampled)
    return imgResampled, itkimgResampled


def resize_image_itk(itkimage, newSpacing, originSpcaing, resamplemethod=sitk.sitkNearestNeighbor):
    """
    image resize withe sitk resampleImageFilter
    :param itkimage:
    :param newSpacing:such as [1,1,1]
    :param resamplemethod:
    :return:
    """
    newSpacing = np.array(newSpacing, float)
    # originSpcaing = itkimage.GetSpacing()
    resampler = sitk.ResampleImageFilter()
    originSize = itkimage.GetSize()
    factor = newSpacing / originSpcaing
    newSize = originSize / factor
    newSize = newSize.astype(np.int)
    resampler.SetReferenceImage(itkimage)
    resampler.SetOutputSpacing(newSpacing.tolist())
    resampler.SetSize(newSize.tolist())
    resampler.SetTransform(sitk.Transform(3, sitk.sitkIdentity))
    resampler.SetInterpolator(resamplemethod)
    itkimgResampled = resampler.Execute(itkimage)
    imgResampled = sitk.GetArrayFromImage(itkimgResampled)
    return imgResampled, itkimgResampled


def ConvertitkTrunctedValue(image, upper=200, lower=-200, normalize=True):
    """
    load files,set truncted value range and normalization 0-255
    :param filename:
    :param upper:
    :param lower:
    :return:
    """
    # 1,tructed outside of liver value
    srcitkimage = sitk.Cast(image, sitk.sitkFloat32)
    srcitkimagearray = sitk.GetArrayFromImage(srcitkimage)
    srcitkimagearray[srcitkimagearray > upper] = upper
    srcitkimagearray[srcitkimagearray < lower] = lower
    # 2,get tructed outside of liver value image
    sitktructedimage = sitk.GetImageFromArray(srcitkimagearray)
    origin = np.array(srcitkimage.GetOrigin())
    spacing = np.array(srcitkimage.GetSpacing())
    sitktructedimage.SetSpacing(spacing)
    sitktructedimage.SetOrigin(origin)
    # 3 normalization value to 0-255
    if normalize:
        rescalFilt = sitk.RescaleIntensityImageFilter()
        rescalFilt.SetOutputMaximum(255)
        rescalFilt.SetOutputMinimum(0)
        rescalFilt.SetGlobalDefaultNumberOfThreads(8)
        itkimage = rescalFilt.Execute(sitk.Cast(sitktructedimage, sitk.sitkFloat32))
    else:
        itkimage = sitk.Cast(sitktructedimage, sitk.sitkFloat32)
    return itkimage


def calcu_dice(Y_pred, Y_gt, K=255):
    """
    calculate two input dice value
    :param Y_pred:
    :param Y_gt:
    :param K:
    :return:
    """
    intersection = 2 * np.sum(Y_pred[Y_gt == K])
    denominator = np.sum(Y_pred) + np.sum(Y_gt) + 1e-5
    loss = (intersection / denominator)
    return loss


def file_name_path(file_dir, dir=True, file=False):
    """
    get root path,sub_dirs,all_sub_files
    :param file_dir:
    :return: dir or file
    """
    for root, dirs, files in os.walk(file_dir):
        if len(dirs) and dir:
            print("sub_dirs:", dirs)
            return dirs
        if len(files) and file:
            print("files:", files)
            return files


def check_trained_data(csv_path, ratio=0.001):
    csvdata = pd.read_csv(csv_path)
    maskdata = csvdata.iloc[:, 1].values
    count = 0
    for num in range(len(maskdata)):
        mask = np.load(maskdata[num])
        labelpixel_count = (mask != 0).sum()
        backgroundpixel_count = (mask == 0).sum()
        pixel_ratio = labelpixel_count / backgroundpixel_count
        if backgroundpixel_count != 0 and pixel_ratio > ratio:
            count = count + 1
    print(count / len(maskdata))


def save_file2csv(file_dir, file_name):
    """
    save file path to csv,this is for segmentation
    :param file_dir:preprocess data path
    :param file_name:output csv name
    :return:
    """
    out = open(file_name, 'w')
    image = "Image"
    mask = "Mask"
    file_image_dir = file_dir + "/" + image
    file_mask_dir = file_dir + "/" + mask
    file_paths = file_name_path(file_image_dir, dir=False, file=True)
    out.writelines("Image,Mask" + "\n")
    for index in range(len(file_paths)):
        out_file_image_path = file_image_dir + "/" + file_paths[index]
        out_file_mask_path = file_mask_dir + "/" + file_paths[index]
        out.writelines(out_file_image_path + "," + out_file_mask_path + "\n")


if __name__ == "__main__":
    save_file2csv("/data/lobedata/LUNG_LOBE_CT_Data/data/", "trainaugdata.csv")
