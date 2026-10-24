"""Spoke->hub laboratory sample referral links (MoH 'mobile laboratory' scheme, 2019-2025),
transcribed from gazette.gov.mv tenders for sample transport issued by atoll/regional hospitals.
Output: sources/public_hospital_labs/sample_referral_network.csv"""
import csv
OUT = r"C:\Users\user\Music\Datathon\data\external\health\services\diagnostics\sources\public_hospital_labs\sample_referral_network.csv"
G = "https://www.gazette.gov.mv/iulaan/"
L = [  # atoll, spoke island (HC without lab), hub facility, hub island, iulaan ids, date
 ("L","Mundoo","L. Maabaidhoo Health Centre","Maabaidhoo","258671;314857","2024-11-05"),
 ("L","Kunahandhoo","L. Hithadhoo Health Centre","Hithadhoo","258671;327512","2025-02-10"),
 ("L","Dhanbidhoo","L. Isdhoo Health Centre","Isdhoo","327515","2025-02-10"),
 ("HDh","Hirimaradhoo","Kulhudhuffushi Regional Hospital","Kulhudhuffushi","127405","2020-02-24"),
 ("HDh","Naivaadhoo","Kulhudhuffushi Regional Hospital","Kulhudhuffushi","126048","2020-02-10"),
 ("HDh","Kurinbi","Kulhudhuffushi Regional Hospital","Kulhudhuffushi","125707","2020-02-06"),
 ("HDh","(HDh health centres, atoll-wide)","Kulhudhuffushi Regional Hospital","Kulhudhuffushi","195387","2022-06-06"),
 ("B","Kudarikilu","B. Kendhoo Health Centre","Kendhoo","156064","2021-07-07"),
 ("AA","Himandhoo","AA. Mathiveri Health Centre","Mathiveri","131790;132396","2020-08-17"),
 ("AA","Bodufolhudhoo","AA. Mathiveri Health Centre","Mathiveri","131788;131793","2020-07"),
 ("AA","Maalhos","AA. Mathiveri Health Centre","Mathiveri","131791","2020-07"),
 ("AA","Feridhoo","AA. Mathiveri Health Centre","Mathiveri","131789","2020-07"),
 ("AA","Ukulhas","AA. Atoll Hospital (Rasdhoo)","Rasdhoo","131787","2020-07-22"),
 ("ADh","Fenfushi","ADh. Maamigili Health Centre","Maamigili","154105","2021-06-15"),
 ("ADh","Dhigurah","ADh. Maamigili Health Centre","Maamigili","131817;154086","2020-07-23"),
 ("ADh","Dhidhdhoo","ADh. Maamigili Health Centre","Maamigili","131817;154086","2020-07-23"),
 ("ADh","Mandhoo","ADh. Atoll Hospital (Mahibadhoo)","Mahibadhoo","128854;154051","2021"),
 ("ADh","Kunburudhoo","ADh. Atoll Hospital (Mahibadhoo)","Mahibadhoo","128856;154050","2021"),
 ("ADh","Hangnaameedhoo","ADh. Atoll Hospital (Mahibadhoo)","Mahibadhoo","128855;154049","2021"),
 ("ADh","Omadhoo","ADh. Atoll Hospital (Mahibadhoo)","Mahibadhoo","128855;154049","2021"),
 ("V","Fulidhoo","V. Atoll Hospital (Felidhoo)","Felidhoo","152533","2021-05-26"),
 ("V","Thinadhoo","V. Atoll Hospital (Felidhoo)","Felidhoo","152533","2021-05-26"),
 ("V","Keyodhoo","V. Atoll Hospital (Felidhoo)","Felidhoo","152533","2021-05-26"),
 ("V","Rakeedhoo","V. Atoll Hospital (Felidhoo)","Felidhoo","152533","2021-05-26"),
 ("M","Raiymandhoo","M. Dhiggaru Health Centre","Dhiggaru","141727","2021-01-13"),
 ("F","Dharanboodhoo","F. Atoll Hospital (Nilandhoo)","Nilandhoo","129946;151274","2021-05-04"),
 ("Dh","Maaenboodhoo","Dh. Atoll Hospital (Kudahuvadhoo)","Kudahuvadhoo","134194","2020-09-24"),
 ("Dh","Rinbudhoo","Dh. Atoll Hospital (Kudahuvadhoo)","Kudahuvadhoo","134193","2020-09-24"),
 ("Dh","Hulhudheli","Dh. Atoll Hospital (Kudahuvadhoo)","Kudahuvadhoo","134193","2020-09-24"),
 ("GA","Nilandhoo","GA. Dhaandhoo Health Centre","Dhaandhoo","139058;151279","2020-12-13"),
 ("GA","Kondey","GA. Gemanafushi Health Centre","Gemanafushi","139058;151279","2020-12-13"),
 ("GA","Maamendhoo","GA. Atoll Hospital (Villingili)","Villingili","139058;151279","2020-12-13"),
 ("HA","Utheemu","HA. Atoll Hospital (Dhidhoo)","Dhidhoo","130246;156127","2020-05-14"),
 ("HA","Maarandhoo","HA. Atoll Hospital (Dhidhoo)","Dhidhoo","160056","2021-08-19"),
 ("HA","Vashafaru","HA. Atoll Hospital (Dhidhoo)","Dhidhoo","165707","2021-10-05"),
 ("Lh","Olhuvelifushi","Lh. Kurendhoo Health Centre","Kurendhoo","127758;153414","2021-06-08"),
 ("Sh","Noomaraa","Sh. Feydhoo Health Centre","Feydhoo","157772","2021-08-03"),
 ("Sh","Goidhoo","(nearest lab; Sh mobile-lab scheme)","","132394","2020-08-17"),
 ("Sh","Narudhoo","(nearest lab; Sh mobile-lab scheme)","","132394","2020-08-17"),
 ("Sh","Maroshi","(nearest lab; Sh mobile-lab scheme)","","132394","2020-08-17"),
 ("Sh","Lhaimagu","(nearest lab; Sh mobile-lab scheme)","","132394","2020-08-17"),
 ("R","Kinolhas","R. Inguraidhoo Health Centre","Inguraidhoo","128717","2020-03-09"),
 ("R","Fainu","R. Inguraidhoo Health Centre","Inguraidhoo","128715","2020-03"),
 ("R","Angolhitheemu","R. Rasgetheemu Health Centre","Rasgetheemu","128713","2020-03"),
 ("R","Vaadhoo","R. Alifushi Health Centre","Alifushi","128711","2020-03"),
 ("R","Rasmaadhoo","R. Innamaadhoo Health Centre","Innamaadhoo","128708","2020-03"),
 ("R","Maakurathu","R. Dhuvaafaru Health Centre","Dhuvaafaru","128703","2020-03"),
 ("Th","Kinbidhoo","Th. Atoll Hospital (Veymandoo)","Veymandoo","125753","2020-02-06"),
 ("Th","Omadhoo","Th. Atoll Hospital (Veymandoo)","Veymandoo","125753","2020-02-06"),
 ("Th","Kandoodhoo","Th. Hirilandhoo Health Centre","Hirilandhoo","125753","2020-02-06"),
 ("Th","Vandhoo","Th. Hirilandhoo Health Centre","Hirilandhoo","125753","2020-02-06"),
 ("Th","Gaadhiffushi","Th. Thimarafushi Health Centre","Thimarafushi","125753","2020-02-06"),
 ("Th","Dhiyamigili","Th. Madifushi Health Centre","Madifushi","125753","2020-02-06"),
]
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["atoll", "spoke_island_no_lab", "hub_facility", "hub_island", "source_url", "source_date"])
    for a, s, h, hi, ids, d in L:
        w.writerow([a, s, h, hi, " ; ".join(G + i for i in ids.split(";")), d])
print(len(L), "links ->", OUT)
