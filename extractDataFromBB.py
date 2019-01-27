'''
This code is used to perform data extraction from images using OCR techniques.
User is prompted to draw a bounding box for the part of image that he/she wants to extract data from.
The OCR result is written to a text file.
'''


import cv2
import os
import pytesseract
import matplotlib.pyplot as plt
import numpy as np

target_width=540
target_height=960
kernel=np.ones((3,3),np.uint8)
	
def auto_canny(image, sigma):
    v = np.median(image)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)
    return edged

def get_ipt(img_path):
	#loading image and storing original width and height
	img=cv2.imread(img_path,0)
	origx=img.shape[1]
	origy=img.shape[0]
	'''
	temp=img.copy()
	temp=auto_canny(temp,0.33)
	temp=cv2.Canny(img,50,150,apertureSize=3)
	temp=cv2.dilate(temp,kernel,iterations=4)
	cv2.imshow("Canny Dilated",temp)
	'''
	#Resize image to target_width and target_height
	resized = cv2.resize(img, (target_width,target_height))

	#Select ROI to send to tesseract and selectROI returns x,y,width, height of bounding box
	r = cv2.selectROI("Image",resized,False,False)
	
	#Scaling drawn bounding box from resized image to an original image and sending it for further processing
	x_scale=origx/target_width
	y_scale=origy/target_height
	(left,top,bottom,right)=(int(r[0]),int(r[1]), int(r[1]+r[3]), int(r[0]+r[2]))
	x=int(np.round(left*x_scale))
	y=int(np.round(top*y_scale))
	xmax = int(np.round(right * x_scale))
	ymax = int(np.round(bottom * y_scale))
	cv2.rectangle(img, (x,y),(xmax,ymax), (255,0,0), 3)
	#cv2.imwrite("bbforSample.jpg",img)	
	
	#numpy array are col-first thus img[y:y+h,x:x+w]
	imCrop = img[y:ymax, x:xmax]
	cv2.imshow("Cropped image",imCrop)
	imCrop = cv2.resize(imCrop, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
	imCrop=cv2.bitwise_not(imCrop)

	# Noise Removal
	imCrop=cv2.dilate(imCrop,kernel,iterations=2)
	cv2.imshow("Dilated",imCrop)
	imCrop=cv2.erode(imCrop,kernel,iterations=1)
	cv2.imshow("Eroded",imCrop)
	
	#smothening
	imCrop = cv2.bilateralFilter(imCrop,9,75,75)
	cv2.imshow("Bilateral Filter",imCrop)

	#Binarization of images
	imCrop = cv2.threshold(imCrop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
	
	cv2.imshow("Binary",imCrop)

	result=pytesseract.image_to_string(imCrop, lang="eng")

	file_name = os.path.basename(img_path).split('.')[0]
	file_name = file_name.split()[0]
	
	#cv2.imwrite("Hough_"+file_name+".jpg",line_img)
	cv2.imwrite("optFileOf_"+file_name+".jpg",img)
	f=open("optFileOf_"+file_name+".txt", "w")
	f.write(result)
	print(result)
	
get_ipt("sample.jpg")
print("Done")
																																																																																																																																																												
k=cv2.waitKey(0)

if k == 27:
    cv2.destroyWindow('img')
