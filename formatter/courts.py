"""
Reads file metadata from database and transforms files.
"""

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
("UKVAT-Customs", "United Kingdom VAT & Duties Tribunals (Customs) Decisions"),
("UKVAT-Excise", "United Kingdom VAT & Duties Tribunals (Excise) Decisions"),
("UKVAT-Landfill", "United Kingdom VAT & Duties Tribunals (Landfill Tax) Decisions"),
("UKVAT-IPT", "United Kingdom VAT & Duties Tribunals (Insurance Premium Tax) Decisions"),
("UKEAT", "United Kingdom Employment Appeal Tribunal"),
("UKUT-AAC", "Upper Tribunal (Administrative Appeals Chamber)"),
("UKUT-LC", "United Kingdom Upper Tribunal (Lands Chamber)"),
("UKUT-TCC", "United Kingdom Upper Tribunal (Finance and Tax)"),
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
("IECA-Notice", "Irish Competition Authority Decisions (Notice Division)"),
("EWCA-Civ", "England and Wales Court of Appeal (Civil Division) Decisions"),
("EWCA-Crim", "England and Wales Court of Appeal (Criminal Division) Decisions"),
("IEIC", "Irish Information Commissioner's Decisions"),
("IESC", "Supreme Court of Ireland Decisions"),
("IEDPC", "Irish Data Protection Commission Case Studies"),
("EWCC-Fam", "England and Wales County Court (Family)"),
("NIQB", "High Court of Justice in Northern Ireland Queen's Bench Division Decisions"),
("NIFam", "High Court of Justice in Northern Ireland Family Division Decisions"),
("NIMaster", "Northern Ireland High Court of Justice, Master's decisions"),
("NICH", "High Court of Justice in Northern Ireland Chancery Division Decisions"),
("EWLands", "England and Wales Lands Tribunal"),
("EWPCC", "England and Wales Patents County Court"),
("UKIT", "United Kingdom Information Tribunal including the National Security Appeals Panel"),
("UKFSM", "United Kingdom Financial Services and Markets Tribunals Decisions"),
("ScotSC", "Scottish Sheriff Court Decisions"),
("NIIT", "Industrial Tribunals Northern Ireland Decisions"),
("EWHC-Comm", "England and Wales High Court (Commercial Court) Decisions"),
("EWHC-QB", "England and Wales High Court (Queen's Bench Division) Decisions"),
("EWHC-Admin", "England and Wales High Court (Administrative Court) Decisions"),
("EWHC-Ch", "England and Wales High Court (Chancery Division) Decisions"),
("EWHC-TCC", "England and Wales High Court (Technology and Construction Court) Decisions"),
("EWHC-Pat", "England and Wales High Court (Patents Court) Decisions"),
("EWHC-Fam", "England and Wales High Court (Family Division) Decisions"),
("EWHC-Admlty", "England and Wales High Court (Admiralty Division) Decisions"),
("EWHC-Costs", "England and Wales High Court (Senior Courts Costs Office) Decisions"),
("EWHC-KB", "England and Wales High Court (King's Bench Division) Decisions"),
("EWHC-Exch", "England and Wales High Court (Exchequer Court) Decisions"),
("EWHC-Mercantile", "Mercantile Court"),
("UKIAT", "United Kingdom Asylum and Immigration Tribunal"),
("NICC", "Crown Court for Northern Ireland Decisions"),
("UKSSCSC", "UK Social Security and Child Support Commissioners' Decisions"),
("UKFTT-TC", "United Kingdom First Tier Tribunal (Tax)"),
("UKFTT-HESC", "First-tier Tribunal (Health Education and Social Care Chamber)")]

categories = {

"United Kingdom": ["UKSC", "CAT", "UKPC", "UKVAT", "UKVAT-Customs", "UKVAT-Excise", "UKVAT-Landfill", 
"UKVAT-IPT", "UKEAT", "UKUT-AAC", "UKUT-LC", "UKUT-TCC-", "DRS", "UKSIAC", 
"UKSPC", "UKSSCSC", "UKFTT-TC", "UKFTT-HESC","UKHL", "UKIT", "UKFSM", "UKIAT"],

"England and Wales": ["EWCA-Civ", "EWCA-Crim", "EWCST", "EWCC-Fam", "EWLands", "EWPCC", "EWHC-Comm", 
"EWHC-QB", "EWHC-Admin", "EWHC-Ch", "EWHC-TCC", "EWHC-Pat", "EWHC-Fam", "EWHC-Admlty", 
"EWHC-Costs", "EWHC-KB", "EWHC-Exch", "EWHC-Mercantile"], 

"Scotland": ["ScotHC", "ScotCS", "ScotSC"], 

"Northern Ireland": ["NICA", "NIFET", "NISSCSC", "NIQB", "NIFam", "NIMaster", "NICH", "NIIT", "NICC"],

"Europe": ["ECHR", "EUECJ"], 

"Republic of Ireland": ["IECCA", "IEHC", "IECA", "IECA-Notice", "IEIC", "IESC", "IEDPC"]

}

