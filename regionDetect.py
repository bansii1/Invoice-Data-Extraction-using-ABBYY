import cv2
import numpy as np
import sys
import os, glob
import process


#global variables
target_width=540
target_height=960
erodeIter=3
dilateIter=6
dirName=sys.argv[1]
IPTPATH=dirName+"/"
OPTPATH="Newoutput/"
listOfFiles=[]
files=[]

#listOfFiles contain path of input images, files contain list of images in input directory
for f in os.listdir(IPTPATH):
	if f.endswith(".jpg"):
		files.append(f)
		listOfFiles.append(os.path.join(IPTPATH,f))


def auto_canny(img, sigma=0.33):
    v = np.median(img)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(img, lower, upper)
    return edged

'''
def sort_contours(cnts, method="left-to-right"):
	# initialize the reverse flag and sort index
	reverse = False
	i = 0

	# handle if we need to sort in reverse
	if method == "right-to-left" or method == "bottom-to-top":
		reverse = True

	# handle if we are sorting against the y-coordinate rather than
	# the x-coordinate of the bounding box
	if method == "top-to-bottom" or method == "bottom-to-top":
		i = 1

	boundingBoxes = [cv2.boundingRect(c) for c in cnts]
	(cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),key=lambda b: b[1][i], reverse=reverse))

	return (cnts, boundingBoxes)

def draw_contour_with_numbering(image, c):
	# compute the center of the contour area and draw a circle
	# representing the center
	for i in range(len(c)):
		M = cv2.moments(c[i])
		if M["m00"] !=0:
			cX = int(M["m10"] / M["m00"])
			cY = int(M["m01"] / M["m00"])
	 
		# draw the countour number on the image
		cv2.putText(image, "#{}".format(i + 1), (cX - 20, cY), cv2.FONT_HERSHEY_SIMPLEX,
			1.0, (255, 255, 255), 2)
	return image
'''

def get_straight_lines(img,aperture_size=3):  
                                                                                                       
	edges = auto_canny(img)
	min_line_length = 100                                                                                             
	max_line_gap = 25
	lines = cv2.HoughLinesP(edges, 1, np.pi/180, 80, min_line_length,max_line_gap)

	return lines

length=len(listOfFiles)
for i in range(length):

	filename=listOfFiles[i]
	basename=filename.split("/")[-1]
	basename=basename.split(".")[0]

	im=cv2.imread(filename)
	img=cv2.imread(filename,0)
	img = cv2.bilateralFilter(img,9,75,75)
	
	#adaptive thresholding 	
	img_bin = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,5,1 )
	img_bin1=img_bin.copy()

	#parameters denoising(img_source, template_size(odd), searchWindowSize(odd), filterStrength)
	img_bin2 = cv2.fastNlMeansDenoising(img_bin1, 7, 21, 9) 

	resized = cv2.resize(img_bin, (target_width,target_height))
	#cv2.imshow("thresh",resized)

	img_bin2 = cv2.resize(img_bin2, (target_width,target_height))
	#cv2.imshow("denoised", img_bin2)

	oimg_bin=255-img_bin
	#cv2.imshow("Image_bin.jpg",oimg_bin)

	kernel_length=np.array(img).shape[1]//50
	print(kernel_length)

	verticle_kernel=cv2.getStructuringElement(cv2.MORPH_RECT, (1,kernel_length))
	hori_kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(kernel_length,1))

	#kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))

	img_temp1=cv2.erode(oimg_bin,verticle_kernel,erodeIter)
	verticle_lines_img=cv2.dilate(img_temp1, verticle_kernel,dilateIter)
	#cv2.imwrite(os.path.join(OPTPATH,"vlines_"+basename+str(erodeIter)+".jpg"),verticle_lines_img)

	img_temp2=cv2.erode(oimg_bin,hori_kernel,erodeIter)
	horizontal_lines_img=cv2.dilate(img_temp2,hori_kernel,dilateIter)
	#cv2.imwrite(os.path.join(OPTPATH,"hlines_"+basename+str(erodeIter)+".jpg"),horizontal_lines_img)

	alpha=0.5
	beta=1.0-alpha
	layout_img=cv2.addWeighted(verticle_lines_img, alpha, horizontal_lines_img, beta, 0.0)

	(_,layout_img)= cv2.threshold(layout_img, 128,255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
	cv2.imwrite(os.path.join(OPTPATH,"layoutOf_"+str(basename)+".jpg"), layout_img)


	im2,contours,hierarchy = cv2.findContours(layout_img.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	contours=sorted(contours, key=cv2.contourArea)
	contours.reverse()
	
	area=[cv2.contourArea(c) for c in contours]
	area = [ elem for elem in area if elem >5]
	
	length = len(area)
	contours=contours[:length]
		
	thresholdArea=sum(area)/len(area)	
	
	temp=im.copy()
	temp1=im.copy()

	x,y,w,h=cv2.boundingRect(contours[0])
	croppedTable=im[y:y+h,x:x+w]
	tempname=os.path.join(OPTPATH,"cropped1_"+basename+".jpg")
	cv2.imwrite(tempname,croppedTable)

	
	
	#os.system("python process.py "+os.path.join(OPTPATH,"cropped1_"+basename+".jpg")+" "+basename+".pdf -l English -pdf")
	#os.system("python fromTablePDFtoDF.py "+basename+".pdf")

	'''
	
	for i in range(length):
		#draws detected bounding boxes
		if area[i]>7:
			x, y, w, h = cv2.boundingRect(contours[i])
			if h>10 and w>10:
				cv2.rectangle(im,(x,y),(x+w,y+h),(255,0,0),5)

		if area[i]>thresholdArea:
			x, y, w, h = cv2.boundingRect(contours[i])
			if h>15 and w>15:
				cv2.rectangle(temp,(x,y),(x+w,y+h),(0,0,255),5)

		cv2.imwrite(os.path.join(OPTPATH,"detectedOf_"+basename+".jpg"), im)
		cv2.imwrite(os.path.join(OPTPATH,"detectedOfThresh_"+basename+".jpg"), temp)
	'''
cv2.waitKey(0)
