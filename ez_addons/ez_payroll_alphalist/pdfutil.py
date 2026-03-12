from PyPDF2 import PdfFileWriter,PdfFileReader
from io import StringIO,BytesIO
import os,inspect,base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter,legal
from reportlab.lib.utils import ImageReader
from datetime import datetime
import base64,logging
_logger=logging.getLogger(__name__)
if __name__=='__main__':import wtax_formula;from data import*
else:from odoo import api,fields,models;from.import wtax_formula;from.data import*
DF='%Y-%m-%d'
TOP_GUIDE=990
data={}
def pdf_add_text(existing_pdf,texts,justify='left',signature=False):
	packet=BytesIO();can=canvas.Canvas(packet,pagesize=legal)
	for t in texts:
		_logger.debug('** text: %s',t);n=t[2]or''
		if len(t)>=4:can.setFont('Helvetica',t[3])
		else:can.setFont('Helvetica',12)
		if type(n)in(float,int):n='{:20,.2f}'.format(t[2]);can.drawRightString(t[0],t[1],n)
		elif isinstance(n,(str,list,tuple))and n[0:2]=='x-':can.drawCentredString(t[0],t[1],n[2:])
		elif isinstance(n,(str,list,tuple))and n[0:2]=='i-':v=n.split('-');w=int(v[1]);y=int(v[2]);img=ImageReader(signature);can.drawImage(img,t[0]-w/2,y,mask='auto',width=w,preserveAspectRatio=True,anchor='s')
		else:can.drawString(t[0],t[1],n)
	can.save();packet.seek(0);new_pdf=PdfFileReader(packet);page=existing_pdf.getPage(0);page.mergePage(new_pdf.getPage(0));return page
def set_data2(plist,key,value):
	if value:set_data(plist,key,value)
def set_data(plist,key,value):
	global data;name=data[key][0:2];name.append(value)
	if'addr1'==key:name.append(5)
	elif'addr'in key:name.append(8)
	plist.append(name)
def clean_tin(tin):
	if not tin:return'','','',''
	if'-'not in tin:n=3;tin_split=[tin[i:i+n]for i in range(0,len(tin),n)]
	else:tin_split=tin.split('-')
	n=len(tin_split)
	if n==3:return tin_split[0],tin_split[1],tin_split[2],'0000'
	elif n==4:return tin_split[0],tin_split[1],tin_split[2],tin_split[3]
	elif n>=5:return tin_split[0],tin_split[1],tin_split[2],tin_split[3],tin_split[4]
	return'','','','0000'
def expand_double(s):s2=s or'';return' '.join(s2)
def expand_space(s,space):s2=s or'';sp=' '*space;return sp.join(s2)
def create_pdf2(schedule1_ids,base_url,period_from='0101',period_to='1231',is_mwe=False,date='2021'):
	global data;directory_path=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
	if date>='2021':fn=os.path.join(directory_path,'2316-2021.pdf');data=data_2021
	else:fn=os.path.join(directory_path,'2316-2018.pdf');data=data_2018
	_logger.debug('*** create_pdf: file: %s',fn);output=PdfFileWriter();f_pdf=open(fn,'rb')
	for sch in schedule1_ids:
		existing_pdf=PdfFileReader(f_pdf);page_template=existing_pdf.getPage(0);texts=[];emp=sch.sudo().employee_id;alphalist_id=sch.sudo().alphalist_id;company_id=alphalist_id.company_id;employee_name=(sch.sudo().employee_name or'').title();set_data(texts,'year',expand_space(alphalist_id.year,3))
		if sch.hired:
			h0=fields.Date.from_string(sch.hired).strftime('%Y-%m-%d');y0=alphalist_id.year+'-01-01'
			if h0<y0:hired='0101'
			else:hired=fields.Date.from_string(sch.hired).strftime('%m%d')
		else:hired='0101'
		set_data(texts,'period1',expand_space(hired,3))
		if sch.date_end:
			h1=fields.Date.from_string(sch.date_end).strftime('%Y-%m-%d');y1=alphalist_id.year+'-12-31'
			if h1>y1:date_end='1231'
			else:date_end=fields.Date.from_string(sch.date_end).strftime('%m%d')
		else:date_end='1231'
		set_data(texts,'period2',expand_space(date_end,3));tin1,tin2,tin3,tin4=clean_tin(sch.tin_no);set_data(texts,'tin1',expand_space(tin1,2));set_data(texts,'tin2',expand_space(tin2,2));set_data(texts,'tin3',expand_space(tin3,2));set_data(texts,'tin4',expand_space(tin4,2));set_data(texts,'name',employee_name);set_data(texts,'rdo',expand_double(alphalist_id.rdo));set_data(texts,'addr1',(emp.home_address or'').replace('\n',' '));set_data(texts,'zip1',expand_double(emp.home_zip))
		if emp.birthday:bday=emp.birthday;set_data(texts,'bday-mm',expand_double(bday.strftime('%m')));set_data(texts,'bday-dd',expand_double(bday.strftime('%d')));set_data(texts,'bday-yyyy',expand_double(bday.strftime('%Y')))
		set_data(texts,'telephone',emp.work_phone)
		if is_mwe:texts.append(data['mwe'])
		if 1:tin1,tin2,tin3,tin4=clean_tin(alphalist_id.company_vat);company=alphalist_id.company_name;addr=alphalist_id.company_address;set_data(texts,'emp-present-zip',expand_double(alphalist_id.company_zip))
		else:
			tin1,tin2,tin3,tin4=clean_tin(company_id.vat);company=company_id.payslip_header or company_id.name;addr=company_id.street or''
			if company_id.street2:addr+=', '+company_id.street2
			if company_id.city:addr+=', '+company_id.city
			if company_id.country_id:addr+=', '+company_id.country_id.name
			set_data(texts,'emp-present-zip',expand_double(company_id.zip))
		set_data(texts,'emp-present-name',company);set_data(texts,'emp-present-tin1',expand_space(tin1,2));set_data(texts,'emp-present-tin2',expand_space(tin2,2));set_data(texts,'emp-present-tin3',expand_space(tin3,2));set_data(texts,'emp-present-tin4',expand_space(tin4,2));set_data(texts,'emp-present-addr',addr)
		if sch.is_main_employer:texts.append(data['employer-main'])
		else:texts.append(data['employer-secondary'])
		tin1,tin2,tin3,tin4=clean_tin(sch.previous_employer_tin);set_data(texts,'emp-prev-tin1',expand_space(tin1,2));set_data(texts,'emp-prev-tin2',expand_space(tin2,2));set_data(texts,'emp-prev-tin3',expand_space(tin3,2));set_data(texts,'emp-prev-tin4',expand_space(tin4,2));set_data(texts,'emp-prev-name',sch.previous_employer);set_data(texts,'emp-prev-addr',sch.previous_employer_address);set_data(texts,'emp-prev-zip',expand_double(sch.previous_employer_zip))
		if is_mwe:set_data2(texts,'mwe-day',alphalist_id.mwe_daily_amount);set_data2(texts,'mwe-month',alphalist_id.mwe_monthly_amount);set_data2(texts,'nt_basic',sch.pres_nt_basic);set_data2(texts,'mwe_hol',sch.pres_nt_holiday);set_data2(texts,'mwe_ot',sch.pres_nt_overtime);set_data2(texts,'mwe_night_diff',sch.pres_nt_night_diff);set_data2(texts,'mwe_hazard',sch.pres_nt_hazard)
		else:set_data2(texts,'nt_basic',sch.pres_nt_income)
		set_data2(texts,'nt_13mp',sch.pres_nt_13mp);set_data2(texts,'de_minimis',sch.pres_nt_deminimis);set_data2(texts,'td_deductions',sch.pres_nt_govded);set_data2(texts,'nt_others',sch.pres_nt_others);set_data2(texts,'total_nt',sch.pres_nt_total)
		if is_mwe:set_data2(texts,'gross-income-present',sch.pres_nt_total);set_data(texts,'t_income2',1e-06);set_data2(texts,'pe_income',1e-06);set_data2(texts,'gross-taxable-income',1e-06)
		else:
			if sch.pres_t_others:set_data2(texts,'t_others_text',sch.pres_t_others_text)
			set_data2(texts,'t_basic',sch.pres_t_income);set_data2(texts,'t_13mp',sch.pres_t_13mp);set_data2(texts,'t_others',sch.pres_t_others);set_data2(texts,'t_income',sch.pres_t_total);set_data2(texts,'gross-income-present',sch.pres_t_total+sch.pres_nt_total);set_data2(texts,'t_income2',sch.pres_t_total);set_data2(texts,'pe_income',sch.prev_t_total);set_data2(texts,'gross-taxable-income',sch.net_taxable_income)
		set_data2(texts,'total_nt2',sch.pres_nt_total)
		if sch.tax_due:set_data(texts,'tax_due',sch.tax_due)
		else:set_data(texts,'tax_due',1e-06)
		set_data2(texts,'wtax-present',sch.tax_withheld-sch.prev_tax_withheld);set_data2(texts,'wtax-previous',sch.prev_tax_withheld)
		if sch.tax_withheld:set_data(texts,'total-wtax',sch.tax_withheld)
		else:set_data(texts,'total-wtax',1e-06)
		set_data(texts,'pera-tax-credit',sch.pera_tax_credit);wtax_npera=sch.tax_withheld-sch.pera_tax_credit
		if wtax_npera:set_data(texts,'total-wtax2',wtax_npera)
		else:set_data(texts,'total-wtax2',1e-06)
		signature_image=False
		if alphalist_id.signature_data:
			y='i-%d-%d'%(alphalist_id.sig_width,alphalist_id.sig_position1);set_data(texts,'n56sig',y);signature_image=BytesIO(base64.b64decode(alphalist_id.signature_data))
			if sch.substituted_filing:y2='i-%d-%d'%(alphalist_id.sig_width,alphalist_id.sig_position2);set_data(texts,'n58sig',y2)
			if alphalist_id.sign_date:set_data(texts,'date_signed',alphalist_id.sign_date.strftime('%m    %d    %Y'))
		set_data(texts,'n56','x-'+(alphalist_id.signatory or''));set_data(texts,'n57','x-'+employee_name)
		if alphalist_id.state=='draft':set_data(texts,'n58','x-'+'DRAFT!!! NOT YET CONFIRMED');set_data(texts,'n59','x-'+employee_name)
		elif sch.substituted_filing:set_data(texts,'n58','x-'+(alphalist_id.signatory or''));set_data(texts,'n59','x-'+employee_name)
		page=pdf_add_text(existing_pdf,texts,signature=signature_image);output.addPage(page)
	outputStream=BytesIO();output.write(outputStream);res=outputStream.getvalue();outputStream.close();return res
if __name__=='__main__':
	data=data_2021;texts=[]
	for k in data:texts.append(data[k])
	if 1:
		for i in range(0,1000,10):texts.append([0,i,'%04d'%i]);texts.append([590,i,'%04d'%i])
		for i in range(0,700,25):texts.append([i,TOP_GUIDE,'%d'%i]);texts.append([i,10,'%d'%i])
	fpdf=open('2316-2021.pdf','rb');output=PdfFileWriter();existing_pdf=PdfFileReader(fpdf);page_template=existing_pdf.getPage(0);page=pdf_add_text(existing_pdf,texts);output.addPage(page);outputStream=open('out.pdf','wb');output.write(outputStream);outputStream.close()