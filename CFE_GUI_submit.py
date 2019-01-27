'''
10/01/2019
This code does the following,
1. creates xml file from searchable pdf using pdftohtml command using system
2. removes extra tags from xml in preProcess function
3. writes into a txt file in learnXML function
4. extracts relevant data in csv file
'''

'''
process to run this code:

excelFileDetected = "GUI_output/InvoiceExtractedData.xlsx"
FINAL_FILE="GUI_output/new.xlsx"

put this two files in proper location as in above lines.

use code as,

python CFE_GUI_SUBMIT.py (dirname)
where, dirname is name of directory containing searchable pdfs.

'''


import xml
import xml.etree.ElementTree as ET
import csv
import operator 
import sys
import re
import nltk
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
from xlrd import open_workbook
from xlutils.copy import copy
import xlrd
import os
import xlwt
from tkinter import *
from tkinter import ttk
import pandas as pd 
import subprocess, sys

#use code as python cleanFormatExtract.py DIR_NAME
dirname=sys.argv[1]
IPTPATH=dirname+"/"

finalList=[]
greatList=[]
excelFileDetected = "GUI_output/InvoiceExtractedData.xlsx"
FINAL_FILE="GUI_output/new.xlsx"
GUI_ctr=0

book_ro = open_workbook(FINAL_FILE)
book = copy(book_ro) # creates a writeable copy
finalSheet = book.get_sheet(0) # get a first sheet



stop = stopwords.words('english')

def createXMLfromSearchablePDF(filename):
	xmlfilename=filename.split(".")[0]+".xml"
	os.system("pdftohtml -c -hidden -xml "+dirname+"/"+filename+" "+dirname+"/"+ xmlfilename)
	print("xml created")


def preProcess(filename):
	filename=str(filename.split('.')[0]+".xml")
	filepath=os.path.join(IPTPATH,filename)
	f = open(filepath,'r')
	a = ['<b>','</b>','<i>','</i>','.:','@','%']
	lst = []
	for line in f:
		for word in a:
			if word in line:
				if word ==".:":
					line = line.replace(word,':')
				else:
					line = line.replace(word,' ')
		lst.append(line)
	f.close()
	f = open(filepath,"w")
	for line in lst:
		f.write(line)
	f.close()

def learnXML(filename):
	filename=filename.split('.')[0]+".xml"
	filepath=os.path.join(IPTPATH,filename)

	tree = ET.parse(filepath)
	rt = tree.getroot()
	textData=[]
	textDataAttrib=[]
	for child in rt:
		print(child.tag)
		#only child of root(rt) is page in xml after pdftohtml
		
		for grandchild in child:
			if grandchild.tag=="text":
				textData=grandchild.text
				temp=grandchild.attrib
				temp.update({"data":textData})
				textDataAttrib.append(temp)

	textDataAttrib=sorted(textDataAttrib, key=lambda k: (int(k["top"]),int(k["left"])))
	#print(textDataAttrib)

	prevTop=0
	f=open(dirname+"/"+filename.split(".")[0]+".txt","w+")
	for item in textDataAttrib:
		top=int(item["top"])
		if not (prevTop<=top+2 and prevTop>=top-2):
			f.write("\n")
			try:
				f.write(item["data"])
				f.write(" ")
				prevTop=top
			except:
				pass
		else:
			try:

				f.write(item["data"])
				f.write(" ")
			except:
				pass


#functions for extracting data

def ie_preprocess(document):
	document = ' '.join([i for i in document.split() if i not in stop])
	sentences = nltk.sent_tokenize(document)
	sentences = [nltk.word_tokenize(sent) for sent in sentences]
	sentences = [nltk.pos_tag(sent) for sent in sentences]
	return sentences
def extract_gst(document):
	gstnums=[]
	#15 digit number with statecode(2,digit)-PANCARD(10, 5 alpha,5 numeric)-alphanumeric(1)-Z(1)-digit(1)
	r = re.compile(r'([0-9]{2}[a-zA-Z]{5}[0-9]{4}[a-zA-Z]{1}[1-9a-zA-Z]{1}Z[0-9a-zA-Z]{1})')
	gstnums = r.findall(document)

	return gstnums
	
def convert_into_lines(document):

	lines=[]
	temp=" "
	for item in document:
		if item=="\n":
			lines.append(temp)
			temp=""
		else:
			temp=temp+item
	return lines

def extract_invoice(document):
	filename=dirname+"/invoice.txt"
	document=convert_into_lines(document)

	with open(filename, 'r') as myfile:
		data = myfile.read()

	keywords=convert_into_lines(data)
	keywords=list(map(lambda x:x.strip(),keywords))
	for key in keywords:	
		for line in document:
			if key in line:
			
				linesplit=line.split(key)[-1]

				p = re.compile('\d+\/?\d+\/?\d+')
				elem = p.findall(linesplit)
					
				if elem:
					val=elem[0]
					#details["INVOICE"]=val


def extract_bill_amount(document):
	global details
	details={}
	ctr=0
	cgst_line=0
	sgst_line=0
	igst_line=0
	gst_line=0
	total_line=0
	vat_line=0
	document=convert_into_lines(document)
	print("document")
	print(document)
	for line in document:	
		ctr=ctr+1
		line=line.upper()
		if "CGST" in line:

			if "CGST" in details.keys():
				continue
			cgst_line=ctr
			p = re.compile('\d+\.?\d+')
			elem = p.findall(line)
			if elem:
				elem=sorted(elem, key=lambda x:float(x))
				print("CGST ",elem)
				val=float(elem[-1])
				details["CGST"]=val

		elif "IGST" in line:

			if "IGST" in details.keys():
				continue
			igst_line=ctr
			p = re.compile('\d+\.?\d+')
			elem = p.findall(line)
			if elem:
				elem=sorted(elem, key=lambda x:float(x))
				print("IGST ",elem)
				val=float(elem[-1])
				details["IGST"]=val
			
		elif "SGST" in line:

			if "SGST" in details.keys():
				continue

			sgst_line=ctr
			p = re.compile('\d+\.?\d+')
			elem = p.findall(line)
			if elem:
				elem=sorted(elem, key=lambda x:float(x))
				print("SGST ",elem)
				val=float(elem[-1])
				details["SGST"]=val
				
		elif "GST" in line:
			if "GST" in details.keys():
				continue

			gst_line=ctr
			if gst_line >=sgst_line and gst_line>=cgst_line:
				p = re.compile('\d+\.?\d+')
				elem = p.findall(line)
				if elem:
					elem=sorted(elem, key=lambda x:float(x))
					print("GST ",elem)
					val=float(elem[-1])
					details["GST"]=val


		elif "TOTAL" in line:
		
			total_line=ctr
			if total_line >=sgst_line or total_line>=cgst_line or total_line>=vat_line:
				linesplit=line.split("TOTAL")[-1]
				p = re.compile('\d+\.?\d+')
				elem = p.findall(linesplit)
				
				if elem:
					elem=sorted(elem, key=lambda x:float(x))
					print("TOTAL ",elem)
					val=float(elem[-1])
					if "TOTAL" in details.keys():
						if val > details["TOTAL"]:
							details["TOTAL"]=val
					else:
						details["TOTAL"]=val


				
		elif "BILL" in line:
			if "BILL" in details.keys():
				continue
			bill_line=ctr
			linesplit=line.split("BILL")[-1]

			print("bill ", linesplit, line)

			p = re.compile('\d+\/?\d+\/?\d+')
			elem = p.findall(linesplit)
				
			if elem:
				val=elem[0]
				details["BILL"]=val


		elif "INVOICE" in line:
			if "INVOICE" in details.keys():
				continue
			
			linesplit=line.split("INV")[-1]
			temp=0
			start=0
			print("invoice ", linesplit, line)
			p = re.compile('\d+\/?\d+\/?\d+')
			elem = p.findall(linesplit)
				
			if elem:
				val=elem[0]
				details["INVOICE"]=val
				
		
		elif "VAT" in line:

			if "VAT" in details.keys():
				continue
			vat_line=ctr
			linesplit=line.split("VAT")[-1]
			temp=0
			start=0
			p = re.compile('\d+\.?\d+')
			print("Line ",linesplit)
			elem = p.findall(line)
		
			if elem:
				elem=sorted(elem, key=lambda x:float(x))
				print("vat ",elem)
				val=float(elem[-1])
				#for cases when total is not found out yet
				if  vat_line >= total_line and ("TOTAL" not in details.keys()):
					if "VAT" in details.keys() :
						details["VAT"]=val
					else:
						details["VAT"]=val
		
					
		else: 
			continue
	return details
	
def get_date(data):
	#format d/m/y & d-m-y is supported
	f1 = re.findall(r'((0?[1-9]|[12][0-9]|3[01])/(0?[1-9]|1[012])/([\d]{4}|[\d]{2}))',data)
	f2 = re.findall(r'((0?[1-9]|[12][0-9]|3[01])-(0?[1-9]|1[012])-([\d]{4}|[\d]{2}))', data)
	dates=[]
	for i in f1:
		dates.append(i[0])
	for i in f2:
		dates.append(i[0])

	regex = re.compile(r'\w(.*)20\d{2}')
	text = data
	match = re.search(regex, text)
	if match:
		date = match.group(0)
		dates.append(date)
	else:
		date = "-"
	print("in dates",dates)

	return dates





def extractData(filename,i):
	
	print("in extractData ", filename)
	finalList=[]
	filename=filename.split(".")[0]+".txt"
	filepath=os.path.join(IPTPATH,filename)

	with open(filepath, 'r') as myfile:
		data = myfile.read()

	gstnums = extract_gst(data)
	dates=get_date(data)
	details=extract_bill_amount(data)
	invoice=extract_invoice(data)
	if dates:
		details["DATE"]=dates[0]
	if gstnums:
		details["GSTNUM"]=gstnums[0]
	if invoice:
		details["INVOICE"]=invoice
	book_ro = open_workbook(excelFileDetected)
	book = copy(book_ro) # creates a writeable copy
	sheet1 = book.get_sheet(0) # get a first sheet
	colx = 0
	with xlrd.open_workbook(excelFileDetected) as wb:
		cs= wb.sheet_by_index(0)
		num_cols= cs.ncols
		num_rows= cs.nrows

	count = num_rows

	# Write the data to rox, column
	
	if "INVOICE" in details.keys():
		sheet1.write(count,colx, details["INVOICE"])
		finalList.append(details["INVOICE"])	
	else:	
		if "BILL" in details.keys():
			sheet1.write(count,colx, details["BILL"])
			finalList.append(details["BILL"])
		else:
			finalList.append("")

	if "DATE" in details.keys():
		sheet1.write(count,colx+1, details["DATE"])
		finalList.append(details["DATE"])
	else:
		finalList.append("")

	if "GSTNUM" in details.keys():
		sheet1.write(count,colx+2, details["GSTNUM"])
		finalList.append(details["GSTNUM"])
	else:
		finalList.append("")

	if "CGST" in details.keys():
		sheet1.write(count,colx+3, details["CGST"])
		finalList.append(details["CGST"])
	else:
		finalList.append("")

	if "IGST" in details.keys():
		sheet1.write(count,colx+4, details["IGST"])
		finalList.append(details["IGST"])
	else:
		finalList.append("")


	if "SGST" in details.keys():
		sheet1.write(count,colx+5, details["SGST"])
		finalList.append(details["SGST"])
	else:
		finalList.append("")


	if "VAT" in details.keys():
		sheet1.write(count,colx+6, details["VAT"])
		finalList.append(details["VAT"])
	else:
		finalList.append("")

	if "TOTAL" in details.keys():
		sheet1.write(count,colx+7, details["TOTAL"])
		finalList.append(details["TOTAL"])
	else:
		finalList.append("")

	finalList.append(filename.split(".")[0]+".pdf")
	sheet1.write(count,colx+8,filename)

	book.save(excelFileDetected)
	
	return finalList
	'''
	print("details",details.keys(),details)
	print("from dates",dates[0])
	print("emails",emails)
	print("names",names)
	print("gstnums",gstnums[0])
	'''


def clear(): 
	Tinv.delete(0, END) 
	Tdate.delete(0, END) 
	Tgstnum.delete(0, END) 
	Tcgst.delete(0, END) 
	Tigst.delete(0, END) 
	Tsgst.delete(0, END) 
	Tvat.delete(0, END) 
	Ttotal.delete(0, END) 
	Tfilename.delete(0, END) 

def insert():
	with xlrd.open_workbook(FINAL_FILE) as wb:
		cs= wb.sheet_by_index(0)
		current_row= cs.nrows
	print(current_row, " rows")
	
	finalSheet.write(current_row, 0, Tinv.get()) 
	finalSheet.write(current_row, 1, Tdate.get()) 
	finalSheet.write(current_row, 2, Tgstnum.get()) 
	finalSheet.write(current_row, 3, Tcgst.get()) 
	finalSheet.write(current_row, 4, Tigst.get()) 
	finalSheet.write(current_row, 5, Tsgst.get()) 
	finalSheet.write(current_row, 6, Tvat.get()) 
	finalSheet.write(current_row, 7, Ttotal.get()) 
	finalSheet.write(current_row, 8, Tfilename.get()) 
	finalSheet.write(current_row, 9, Tremark.get())
        # save the file 
	print("keys of details...",greatList[GUI_ctr])
	
	
	if Tinv.get()!=greatList[GUI_ctr][0]:

		newline=Tinv.get()
		newline=newline.replace(".","")

		keyword=re.sub('[0-9]+', '', newline)

		keyword=keyword.lower()
		print("keyword to be inserted ",keyword,"************")	
		
		f=open(dirname+"/"+"invoice.txt","w+")
		f.write(keyword)
		f.write("/n")
		f.close()
		'''
		df=pd.read_csv(dirname+"/invoice.csv")
		print("dataframe", df)
		myData=[[keyword,1]]
		df=df.append([{'Keyword':keyword, 'frequency':"1"}], ignore_index=True)
		df.to_csv('invoice.csv')
		
		
		listof=df['Keyword'].value_counts()
		listof=listof.iloc[1:,:]
		listof.to_csv('out.csv')
		'''
	if Tdate.get()!=greatList[GUI_ctr][1]:

		newline=Tdate.get()
		newline=newline.replace(".","")

		keyword=re.sub('[0-9]+', '', newline)

		keyword=keyword.lower()
		print("keyword to be inserted ",keyword,"************")	
		
		f=open(dirname+"/"+"date.txt","w+")
		f.write(keyword)
		f.write("/n")
		f.close()


	if Tgstnum.get()!=greatList[GUI_ctr][2]:
		newline=Tgstnum.get()
		newline=newline.replace(".","")

		keyword=re.sub('[0-9]+', '', newline)

		print("keyword to be inserted ",keyword,"************")	
		
		f=open(dirname+"/"+"gstnum.txt","w+")
		f.write(keyword)
		f.write("/n")
		f.close()

	if Tcgst.get()!=greatList[GUI_ctr][3]:
		newline=Tcgst.get()
		newline=newline.replace(".","")

		keyword=re.sub('[0-9]+', '', newline)

		keyword=keyword.lower()
		print("keyword to be inserted ",keyword,"************")	
		
		f=open(dirname+"/"+"cgst.txt","w+")
		f.write(keyword)
		f.write("/n")
		f.close()

		print("same CGST")
	if Tigst.get()!=greatList[GUI_ctr][4]:
		newline=Tigst.get()
		newline=newline.replace(".","")

		keyword=re.sub('[0-9]+', '', newline)

		keyword=keyword.lower()
		print("keyword to be inserted ",keyword,"************")	
		
		f=open(dirname+"/"+"igst.txt","w+")
		f.write(keyword)
		f.write("/n")
		f.close()

	if Tsgst.get()!=greatList[GUI_ctr][5]:
		newline=Tsgst.get()
		newline=newline.replace(".","")

		keyword=re.sub('[0-9]+', '', newline)

		keyword=keyword.lower()
		print("keyword to be inserted ",keyword,"************")	
		
		f=open(dirname+"/"+"sgst.txt","w+")
		f.write(keyword)
		f.write("/n")
		f.close()

	if Tvat.get()!=greatList[GUI_ctr][6]:
		newline=Tvat.get()
		newline=newline.replace(".","")

		keyword=re.sub('[0-9]+', '', newline)

		keyword=keyword.lower()
		print("keyword to be inserted ",keyword,"************")	
		
		f=open(dirname+"/"+"vat.txt","w+")
		f.write(keyword)
		f.write("/n")
		f.close()

	if Ttotal.get()!=greatList[GUI_ctr][7]:
		newline=Ttotal.get()
		newline=newline.replace(".","")

		keyword=re.sub('[0-9]+', '', newline)
		keyword=keyword.lower()
		print("keyword to be inserted ",keyword,"************")	
		
		f=open(dirname+"/"+"total.txt","w+")
		f.write(keyword)
		f.write("/n")
		f.close()
	
	book.save(FINAL_FILE)
	print("destroying..")
	root.destroy()
	print("done.....")

	
def createWindow(root,l):
	global Tinv, Tdate, Tgstnum, Tcgst, Tigst, Tsgst, Tvat, Ttotal, Tfilename, Tremark

	lbl=Label(root, text="Invoice Data",  fg="#03065E",bg="White", font=("Times",14,'bold') )
	lbl.grid(column=1,row=0)
	root.geometry('400x350')

	lbl=Label(root, text="Invoice Number ", fg="#FFFFFF", bg="#514357", font=("Times",11,'bold'),width=15)
	lbl.grid(column=0,row=2,sticky=E)
	invoiceNum=l[0]
	print("in number ",invoiceNum)
	Tinv= StringVar()
	Tinv.set(invoiceNum)
	entry_invoicenum = Entry(root, textvariable=Tinv).grid(row=2, column=1)

	lbl=Label(root, text="Date",fg="#FFFFFF", bg="#514357", font=("Times",11,'bold'),width=15)
	lbl.grid(column=0,row=3,sticky=E)
	date=l[1]
	Tdate = StringVar()
	Tdate.set(date)
	entry_date = Entry(root, textvariable=Tdate).grid(row=3, column=1)
		
	lbl=Label(root, text="GST Number", fg="#FFFFFF", bg="#514357", font=("Times",11,'bold'),width=15)
	lbl.grid(column=0,row=4,sticky=E)
	gstNum=l[2]
	print("gst ",gstNum)
	Tgstnum = StringVar()
	Tgstnum.set(gstNum)
	entry_gstnum = Entry(root, textvariable=Tgstnum).grid(row=4, column=1)	
		
	lbl=Label(root, text="CGST", fg="#FFFFFF", bg="#514357", font=("Times",11,'bold'),width=15)
	lbl.grid(column=0,row=5,sticky=E)
	cgst=l[3]
	print("cgst ",cgst)
	Tcgst= StringVar()
	Tcgst.set(cgst)
	entry_cgst = Entry(root, textvariable=Tcgst).grid(row=5, column=1)

	lbl=Label(root, text="IGST", fg="#FFFFFF", bg="#514357", font=("Times",11,'bold'),width=15)
	lbl.grid(column=0,row=6,sticky=E)
	igst=l[4]
	print("igst ",igst)
	Tigst = StringVar()
	Tigst.set(igst)
	entry_igst = Entry(root, textvariable=Tigst).grid(row=6, column=1)

	lbl=Label(root, text="SGST", fg="#FFFFFF", bg="#514357", font=("Times",11,'bold'),width=15)
	lbl.grid(column=0,row=7,sticky=E)
	sgst=l[5]
	print("sgst ",sgst)
	Tsgst = StringVar()
	Tsgst.set(sgst)
	entry_sgst = Entry(root, textvariable=Tsgst).grid(row=7, column=1)
		
	lbl=Label(root, text="VAT", fg="#FFFFFF", bg="#514357", font=("Times",11,'bold'),width=15)
	lbl.grid(column=0,row=8,sticky=E)
	vat=l[6]
	print("vat ",vat)
	Tvat = StringVar()
	Tvat.set(vat)
	entry_vat = Entry(root, textvariable=Tvat).grid(row=8, column=1)

	lbl=Label(root, text="Total", fg="#FFFFFF", bg="#514357", font=("Times",11,'bold'),width=15)
	lbl.grid(column=0,row=9,sticky=E)
	total=l[7]
	print("total ",total)
	Ttotal = StringVar()
	Ttotal.set(total)
	entry_total = Entry(root, textvariable=Ttotal).grid(row=9, column=1)

	lbl=Label(root, text="Filename", fg="#FFFFFF", bg="#514357", font=("Times",11,'bold'),width=15)
	lbl.grid(column=0,row=10,sticky=E)
	filename=l[8]
	print("filename ",filename)
	Tfilename= StringVar()
	Tfilename.set(filename)
	entry_filename = Entry(root, textvariable=Tfilename).grid(row=10, column=1)

	lbl=Label(root, text="Remark", fg="#FFFFFF", bg="#514357", font=("Times",11,'bold'),width=15)
	lbl.grid(column=0,row=11,sticky=E)
	Tremark= StringVar()
	entry_remark = Entry(root, textvariable=Tremark).grid(row=11, column=1)
	
	opener ="open" if sys.platform == "darwin" else "xdg-open"
	subprocess.call([opener, dirname+"/"+l[-1]])	

	submit = Button(root, text="Submit", fg="#FFFFFF", bg="#514357",  font=("Times",11,'bold'),command=insert) 
	submit.grid(row=14, column=1) 
	
	root.mainloop()



if __name__ == '__main__':
	
	files=[]

	colnames=["INVOICE/BILL","Date","GSTNUM","CGST","IGST","SGST","VAT","TOTAL","FILENAME"]

	for f in os.listdir(IPTPATH):
		if f.endswith(".pdf"):
			files.append(f)
			
	totalpdfs=len(files)
	print(files)		

	for i in range (totalpdfs):
		rawfilename=files[i]
		filename=rawfilename.replace(" ","_")
		os.rename(dirname+"/"+rawfilename,dirname+"/"+filename)
		createXMLfromSearchablePDF(filename)
		preProcess(filename)
		learnXML(filename)
		finalList=extractData(filename,i)
		greatList.append(finalList)

	#comment following loop to disable gui
	print("GreatList",greatList)
	for l in greatList:
		global root 
		root= Tk()
		root.title("Invoice Data Extraction ")
		createWindow(root,l)
		GUI_ctr=GUI_ctr+1
	
