#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- author: lzw5399 -*-
import os
import time
import zipfile

from flask import Flask, render_template, request, send_from_directory
import fitz

app = Flask(__name__)

PREFIX = 'images_'


# 获取当前时间戳
def get_timespan():
    return PREFIX + time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())


# 压缩指定文件夹
def zip_dir(dirpath, outFullName):
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param outFullName: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, '')

        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()


# 获取某个路径下的所有pdf
def listdir(path, list_name):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isdir(file_path):
            listdir(file_path, list_name)
        elif os.path.splitext(file_path)[1] == '.pdf':
            list_name.append(file_path)


# 递归删除文件夹
def local_rm(dirpath):
    if os.path.exists(dirpath):
        files = os.listdir(dirpath)
        for file in files:
            filepath = os.path.join(dirpath, file).replace("\\", '/')
            if os.path.isdir(filepath):
                local_rm(filepath)
            else:
                os.remove(filepath)
        os.rmdir(dirpath)


# 清楚之前的旧文件夹
def clear_legacy_folders():
    current_dir = os.getcwd()
    for file in os.listdir(current_dir):
        file_path = os.path.join(current_dir, file)
        if os.path.isdir(file_path) and file.startswith(PREFIX):
            local_rm(file_path)


# pdf转png
def pdf2image(pdf_path, img_path, zoom_x, zoom_y, rotation_angle):
    (_, file_fullname) = os.path.split(pdf_path)
    file_name = os.path.splitext(file_fullname)[0]

    # 打开PDF文件
    pdf = fitz.open(pdf_path)
    # 逐页读取PDF
    for pg in range(0, pdf.pageCount):
        page = pdf[pg]
        # 设置缩放和旋转系数
        trans = fitz.Matrix(zoom_x, zoom_y).preRotate(rotation_angle)
        pm = page.getPixmap(matrix=trans, alpha=False)
        # 开始写图像
        converted_image = os.path.join(img_path, file_name + '_' + str(pg) + ".png")
        pm.writePNG(converted_image)
        print(converted_image, '转换成功')
    pdf.close()


@app.route('/')
def hello_world():
    return render_template('index.html', name='index')


@app.route('/api/pdf2png', methods=['POST'])
def pdf2png():
    current_dir = os.getcwd()
    unique_folder_name = get_timespan()

    # 清除旧文件
    clear_legacy_folders()

    # 创建【./{时间戳}】文件夹
    unique_path = os.path.join(current_dir, unique_folder_name)
    if not os.path.exists(unique_path):
        os.makedirs(unique_path)
    # 创建【./{时间戳}/images】文件夹
    unique_images_path = os.path.join(unique_path, 'images')
    if not os.path.exists(unique_images_path):
        os.makedirs(unique_images_path)

    # 把所有文件保存到【./{时间戳}】下
    for file in request.files.getlist('file'):
        file.save(os.path.join(unique_path, file.filename))

    # 将所有的pdf都读取出来
    pdfs = []
    listdir(unique_path, pdfs)

    # 遍历pdf转成png
    for pdf_path in pdfs:
        pdf2image(pdf_path, unique_images_path, 5, 5, 0)

    # 压缩【./{时间戳}/images】文件夹为【{时间戳}.zip】
    zip_file_name = unique_folder_name + ".zip"
    zip_path = os.path.join(unique_path, zip_file_name)
    zip_dir(unique_images_path, zip_path)

    return send_from_directory(zip_path, filename=zip_file_name, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
