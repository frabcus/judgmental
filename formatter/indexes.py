"""
Reads file metadata from database and transforms files.
"""

from dateutil.parser import parse as dateparse
from lxml import html, etree
import re
import os
import string
import traceback

from StringIO import StringIO

from general import *


# must use a global variable to ensure it is visible throughout the process pool
with open("template_index.html",'r') as html_template_file:
    html_template_index_stringio = StringIO(html_template_file.read())

# List of long and short names for courts.  The short names mostly match those
# in neutral citations.

# This could be better placed somewhere else, possibly in the courts table of
# judgmental.db, if that could be stable instead of regenerated.

courts = [
("UKSC", "United Kingdom Supreme Court"),
("NICA", "Court of Appeal in Northern Ireland Decisions"),
("CAT", "United Kingdom Competition Appeals Tribunal"),
("UKPC", "Privy Council Decisions"),
("UKVAT", "United Kingdom VAT & Duties Tribunals Decisions"),
("UKVAT(Customs)", "United Kingdom VAT & Duties Tribunals (Customs) Decisions"),
("UKVAT(Excise)", "United Kingdom VAT & Duties Tribunals (Excise) Decisions"),
("UKVAT(Landfill)", "United Kingdom VAT & Duties Tribunals (Landfill Tax) Decisions"),
("UKVAT(IPT)", "United Kingdom VAT & Duties Tribunals (Insurance Premium Tax) Decisions"),
("UKEAT", "United Kingdom Employment Appeal Tribunal"),
("UKUT(AAC)", "Upper Tribunal (Administrative Appeals Chamber)"),
("UKUT(LC)", "United Kingdom Upper Tribunal (Lands Chamber)"),
("UKUT(TCC)", "United Kingdom Upper Tribunal (Finance and Tax)"),
("DRS", "Nominet UK Dispute Resolution Service"),
("UKSIAC", "Special Immigrations Appeals Commission"),
("ScotHC", "Scottish High Court of Justiciary Decisons"),
("ECHR", "European Court of Human Rights"),
("UKSPC", "United Kingdom Special Commissioners of Income Tax Decisions"),
("ScotCS", "Scottish Court of Session Decisions"),
("IECCA", "Irish Court of Criminal Appeal"),
("UKHL", "United Kingdom House of Lords Decisions"),
("IEHC", "High Court of Ireland Decisions"),
("NIFET", "Fair Employment Tribunal Northern Ireland Decisions"),
("NISSCSC", "Northern Ireland - Social Security and Child Support Commissioners' Decisions"),
("EUECJ", "Court of Justice of the European Communities (including Court of First Instance Decisions)"),
("EWCST", "England and Wales Care Standards Tribunal"),
("IECA", "Irish Competition Authority Decisions"),
("IECA (Notice)", "Irish Competition Authority Decisions (Notice Division)"),
("EWCA Civ", "England and Wales Court of Appeal (Civil Division) Decisions"),
("EWCA Crim", "England and Wales Court of Appeal (Criminal Division) Decisions"),
("IEIC", "Irish Information Commissioner's Decisions"),
("IESC", "Supreme Court of Ireland Decisions"),
("IEDPC", "Irish Data Protection Commission Case Studies"),
("EWCC (Fam)", "England and Wales County Court (Family)"),
("NIQB", "High Court of Justice in Northern Ireland Queen's Bench Division Decisions"),
("NIFam", "High Court of Justice in Northern Ireland Family Division Decisions"),
("NIMaster", "Northand Ireland High Court of Justice, Master's decisions"),
("NICH", "High Court of Justice in Northern Ireland Chancery Division Decisions"),
("EWLands", "England and Wales Lands Tribunal"),
("EWPCC", "England and Wales Patents County Court"),
("UKIT", "United Kingdom Information Tribunal including the National Security Appeals Panel"),
("UKFSM", "United Kingdom Financial Services and Markets Tribunals Decisions"),
("ScotSC", "Scottish Sheriff Court Decisions"),
("NIIT", "Industrial Tribunals Northern Ireland Decisions"),
("EWHC (Comm)", "England and Wales High Court (Commercial Court) Decisions"),
("EWHC (QB)", "England and Wales High Court (Queen's Bench Division) Decisions"),
("EWHC (Admin)", "England and Wales High Court (Administrative Court) Decisions"),
("EWHC (Ch)", "England and Wales High Court (Chancery Division) Decisions"),
("EWHC (TCC)", "England and Wales High Court (Technology and Construction Court) Decisions"),
("EWHC (Pat)", "England and Wales High Court (Patents Court) Decisions"),
("EWHC (Fam)", "England and Wales High Court (Family Division) Decisions"),
("EWHC (Admlty)", "England and Wales High Court (Admiralty Division) Decisions"),
("EWHC (Costs)", "England and Wales High Court (Senior Courts Costs Office) Decisions"),
("EWHC KB", "England and Wales High Court (King's Bench Division) Decisions"),
("EWHC Exch", "England and Wales High Court (Exchequer Court) Decisions"),
("EWHC (Mercantile)", "Mercantile Court"),
("UKIAT", "United Kingdom Asylum and Immigration Tribunal"),
("NICC", "Crown Court for Northern Ireland Decisions"),
("UKSSCSC", "UK Social Security and Child Support Commissioners' Decisions"),
("UKFTT (TC)", "United Kingdom First Tier Tribunal (Tax)"),
("UKFTT (HESC)", "First-tier Tribunal (Health Education and Social Care Chamber)")]

months = ["", "January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December"]

def make_indexes(dbfile_name, logfile, output_dir, use_multiprocessing):

    print "-"*25
    print "Conversion..."

    finished_count = Counter()

    def convert_report(basename):
        "Callback function; reports on success or failure"
        def closure(r):
            "Take True and a list of report strings, or false and a message"
            (s,x) = r
            try:
                if s:
                    finished_count.inc()
                    if len(x)>0:
                        logfile.write("[convert success] " + basename + " (" + ", ".join(x) + ")" + "\n")
                    print "convert:%6d. %s"%(finished_count.count, basename)
                else:
                    raise StandardConversionError(x)
            except ConversionError, e:
                e.log("indexing fail",basename,logfile)
        return closure

    print "Generating indexes"
    with ProcessManager(use_multiprocessing, verbose=True) as process_pool:
    
    	# Index by court ID
        with DatabaseManager(dbfile_name,use_multiprocessing) as cursor:
            courts = list(cursor.execute('SELECT courtid, name FROM courts'))
    	
    	process_pool.apply_async(make_top_index,(output_dir,),callback=convert_report("top"))
    	for (id, name) in courts:
    		process_pool.apply_async(make_court_index,(id,name,dbfile_name,use_multiprocessing,output_dir),callback=convert_report(name))

    broadcast(logfile,"Converted %d files successfully"%finished_count.count)

def make_element(tag,attribs,text):
	e = etree.Element(tag)
	for a in attribs:
		e.attrib[a] = attribs[a]
	e.text = text
	return e

def make_court_index(id,name,dbfile_name,use_multiprocessing,output_dir):
	current_year=0
	current_month=0
	year_content_div = None
	try:
	
		template = html.parse(html_template_index_stringio)
		template.find('//title').text = name + ": Judgmental"
		template.find('//div[@id="content"]/h1').text = name
		template.find('//span[@id="bc-courtname"]').text = name
		missing_index = template.find('//div[@class="index"]')
		missing_index.text = ""
		table = make_element("table",{},"")
		missing_index.append(table)


		short_name = [short for (short, long) in courts if long == name][0]

		with DatabaseManager(dbfile_name,use_multiprocessing) as cursor:
			judgments = list(cursor.execute('SELECT date,judgmentid,title,bailii_url FROM judgments WHERE courtid=? ORDER BY date DESC',(id,)))
			print "%d judgments found" % len(judgments)
			for j in judgments:

				date = dateparse(j[0])
				if date.year != current_year or date.month != current_month:
					# strftime doesn't work with dates before 1900
					month_human = months[date.month] + " " + str(date.year)
					month_id = "%d-%d" % (date.year, date.month)
					print month_human
					current_year = date.year
					current_month = date.month
					
					table_row = make_element("tr", {}, "")
					table_header = make_element("td", {}, "")
					table_content = make_element("td", {}, "")
					table_row.append(table_header)
					table_row.append(table_content)
					table.append(table_row)
					
					year_head_div = make_element("div", {"class": "index-year",
							"onclick": 'showHide("%s");' % month_id}, month_human + "\n")
					table_header.append(year_head_div)
					year_content_div = make_element("div", {"class": "index-judgments",
					    "id": month_id, "style": "display: none"}, "")
					table_content.append(year_content_div)
					

				case = make_element("div", {"class": "row"}, "")
				link = make_element("a", {"href": j[3]}, j[2])
				case.append(link)
				case.tail = "\n"
				year_content_div.append(case)
				
		outfile = open(os.path.join(output_dir,short_name+".html"),'w')
		outfile.write(etree.tostring(template, pretty_print=True))
		return (True,"")
				
				

	except ConversionError,e:
		return (False,e.message)
	except Exception, e:
		# Something really unexpected happened
		return (False, traceback.format_exc())
		
		
def make_top_index(output_dir):
	try:
		print "make_top_index"
		template = html.parse(html_template_index_stringio)
		name = "All Courts and Tribunals"
		template.find('//title').text = name + ": Judgmental"
		template.find('//div[@id="content"]/h1').text = name
		template.find('//span[@id="bc-courtname"]').text = ""
		missing_index = template.find('//div[@class="index"]')
		missing_index.text = ""

		print "make_top_index"


		for (short, long) in courts:
			
			case = make_element("div", {"class": "row"}, "")
			link = make_element("a", {"href": short+".html"}, long)
			case.append(link)
			case.tail = "\n"
			missing_index.append(case)

		print "make_top_index"
				
		outfile = open(os.path.join(output_dir,"index.html"),'w')
		outfile.write(etree.tostring(template, pretty_print=True))
		return (True,"")

	except ConversionError,e:
		return (False,e.message)
	except Exception, e:
		# Something really unexpected happened
		return (False, traceback.format_exc())

class CantFindElement(ConversionError):
    def __init__(self,searchstring):
        self.message = "can't find element \"%s\""%searchstring
        
if __name__ == "__main__":
	make_indexes("../judgmental.db",open("errors.log", "w"),"indexes",False)
