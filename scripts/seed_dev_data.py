"""Synthetic Development Seed Data for SNOMED CT and SDD.

# WARNING: This is synthetic development seed data. NOT from an official SNOMED CT or SDD release.
# Strictly for local testing and developer evaluation only.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory, engine
from app.models.base import Base
from app.models.sdd import SDDActiveIngredient, SDDCatalogueMetadata, SDDMedication
from app.models.snomed import SnomedConcept, SnomedDescription, SnomedReleaseMetadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_dev_data")

# ---------------------------------------------------------------------------
# 50 Common Clinical SNOMED CT Concepts
# ---------------------------------------------------------------------------
SNOMED_SEED_CONCEPTS = [
    # Respiratory
    {
        "id": "386661006",
        "fsn": "Acute upper respiratory tract infection (disorder)",
        "preferred": "Acute upper respiratory tract infection",
        "synonyms": ["URTI", "Common cold", "Acute URI"],
    },
    {
        "id": "233604007",
        "fsn": "Pneumonia (disorder)",
        "preferred": "Pneumonia",
        "synonyms": ["Chest infection", "Lung infection"],
    },
    {
        "id": "195967001",
        "fsn": "Asthma (disorder)",
        "preferred": "Asthma",
        "synonyms": ["Bronchial asthma", "Asthmatic attack"],
    },
    {
        "id": "13645005",
        "fsn": "Chronic obstructive pulmonary disease (disorder)",
        "preferred": "Chronic obstructive pulmonary disease",
        "synonyms": ["COPD", "Chronic airflow limitation"],
    },
    {
        "id": "32398004",
        "fsn": "Acute bronchitis (disorder)",
        "preferred": "Acute bronchitis",
        "synonyms": ["Bronchitis", "Chest cold"],
    },
    {
        "id": "40055000",
        "fsn": "Chronic sinusitis (disorder)",
        "preferred": "Chronic sinusitis",
        "synonyms": ["Sinusitis", "Sinus infection"],
    },
    # Cardiovascular
    {
        "id": "38341003",
        "fsn": "Hypertension (disorder)",
        "preferred": "Hypertension",
        "synonyms": ["High blood pressure", "HTN", "Essential hypertension"],
    },
    {
        "id": "84114007",
        "fsn": "Heart failure (disorder)",
        "preferred": "Heart failure",
        "synonyms": ["Congestive heart failure", "CHF", "Cardiac failure"],
    },
    {
        "id": "49436004",
        "fsn": "Atrial fibrillation (disorder)",
        "preferred": "Atrial fibrillation",
        "synonyms": ["AF", "A-fib", "Auricular fibrillation"],
    },
    {
        "id": "194828000",
        "fsn": "Angina pectoris (disorder)",
        "preferred": "Angina pectoris",
        "synonyms": ["Angina", "Ischemic chest pain"],
    },
    {
        "id": "22298006",
        "fsn": "Myocardial infarction (disorder)",
        "preferred": "Myocardial infarction",
        "synonyms": ["Heart attack", "MI", "Acute MI"],
    },
    # Endocrine & Metabolic
    {
        "id": "73211009",
        "fsn": "Diabetes mellitus (disorder)",
        "preferred": "Diabetes mellitus",
        "synonyms": ["Diabetes", "DM"],
    },
    {
        "id": "44054006",
        "fsn": "Type 2 diabetes mellitus (disorder)",
        "preferred": "Type 2 diabetes mellitus",
        "synonyms": ["Type 2 diabetes", "T2DM", "Non-insulin dependent diabetes"],
    },
    {
        "id": "40930008",
        "fsn": "Hypothyroidism (disorder)",
        "preferred": "Hypothyroidism",
        "synonyms": ["Underactive thyroid", "Low thyroid"],
    },
    {
        "id": "34486009",
        "fsn": "Hyperthyroidism (disorder)",
        "preferred": "Hyperthyroidism",
        "synonyms": ["Overactive thyroid", "Thyrotoxicosis"],
    },
    {
        "id": "55822004",
        "fsn": "Hyperlipidemia (disorder)",
        "preferred": "Hyperlipidemia",
        "synonyms": ["High cholesterol", "Dyslipidemia", "High lipid level"],
    },
    # Gastrointestinal
    {
        "id": "235595009",
        "fsn": "Gastroesophageal reflux disease (disorder)",
        "preferred": "Gastroesophageal reflux disease",
        "synonyms": ["GERD", "Acid reflux", "Heartburn"],
    },
    {
        "id": "4556007",
        "fsn": "Gastritis (disorder)",
        "preferred": "Gastritis",
        "synonyms": ["Stomach inflammation", "Gastric irritation"],
    },
    {
        "id": "13200003",
        "fsn": "Peptic ulcer (disorder)",
        "preferred": "Peptic ulcer",
        "synonyms": ["Stomach ulcer", "PUD", "Duodenal ulcer"],
    },
    {
        "id": "10743008",
        "fsn": "Irritable bowel syndrome (disorder)",
        "preferred": "Irritable bowel syndrome",
        "synonyms": ["IBS", "Spastic colon"],
    },
    {
        "id": "14760008",
        "fsn": "Constipation (disorder)",
        "preferred": "Constipation",
        "synonyms": ["Irregular bowel movement", "Costiveness"],
    },
    {
        "id": "236077008",
        "fsn": "Acute gastroenteritis (disorder)",
        "preferred": "Acute gastroenteritis",
        "synonyms": ["Food poisoning", "Stomach flu", "AGE", "Viral gastroenteritis"],
    },
    # Musculoskeletal
    {
        "id": "396275006",
        "fsn": "Osteoarthritis (disorder)",
        "preferred": "Osteoarthritis",
        "synonyms": ["OA", "Degenerative joint disease", "Wear-and-tear arthritis"],
    },
    {
        "id": "69896004",
        "fsn": "Rheumatoid arthritis (disorder)",
        "preferred": "Rheumatoid arthritis",
        "synonyms": ["RA", "Inflammatory arthritis"],
    },
    {
        "id": "279039007",
        "fsn": "Low back pain (finding)",
        "preferred": "Low back pain",
        "synonyms": ["Lumbago", "Backache", "Lumbar pain"],
    },
    {
        "id": "90560007",
        "fsn": "Gout (disorder)",
        "preferred": "Gout",
        "synonyms": ["Gouty arthritis", "Podagra"],
    },
    {
        "id": "64859006",
        "fsn": "Osteoporosis (disorder)",
        "preferred": "Osteoporosis",
        "synonyms": ["Brittle bone disease", "Low bone mineral density"],
    },
    # Neurological
    {
        "id": "37796009",
        "fsn": "Migraine (disorder)",
        "preferred": "Migraine",
        "synonyms": ["Sick headache", "Hemicrania", "Migraine with aura"],
    },
    {
        "id": "84757009",
        "fsn": "Epilepsy (disorder)",
        "preferred": "Epilepsy",
        "synonyms": ["Seizure disorder", "Convulsions"],
    },
    {
        "id": "230690007",
        "fsn": "Stroke (disorder)",
        "preferred": "Stroke",
        "synonyms": ["Cerebrovascular accident", "CVA", "Brain attack"],
    },
    {
        "id": "49049000",
        "fsn": "Parkinson disease (disorder)",
        "preferred": "Parkinson disease",
        "synonyms": ["Parkinson's", "Paralysis agitans"],
    },
    {
        "id": "26929004",
        "fsn": "Alzheimer disease (disorder)",
        "preferred": "Alzheimer disease",
        "synonyms": ["Alzheimer's dementia", "AD"],
    },
    # Mental Health
    {
        "id": "370143000",
        "fsn": "Major depressive disorder (disorder)",
        "preferred": "Major depressive disorder",
        "synonyms": ["Depression", "MDD", "Clinical depression"],
    },
    {
        "id": "21897009",
        "fsn": "Generalized anxiety disorder (disorder)",
        "preferred": "Generalized anxiety disorder",
        "synonyms": ["GAD", "Chronic anxiety neurosis"],
    },
    {
        "id": "193462001",
        "fsn": "Insomnia (disorder)",
        "preferred": "Insomnia",
        "synonyms": ["Sleeplessness", "Sleep disorder"],
    },
    # Infectious
    {
        "id": "68566005",
        "fsn": "Urinary tract infection (disorder)",
        "preferred": "Urinary tract infection",
        "synonyms": ["UTI", "Cystitis", "Bladder infection"],
    },
    {
        "id": "128045006",
        "fsn": "Cellulitis (disorder)",
        "preferred": "Cellulitis",
        "synonyms": ["Skin infection", "Bacterial skin cellulitis"],
    },
    {
        "id": "6142004",
        "fsn": "Influenza (disorder)",
        "preferred": "Influenza",
        "synonyms": ["Flu", "Grippe"],
    },
    {
        "id": "840539006",
        "fsn": "Disease caused by Severe acute respiratory syndrome coronavirus 2 (disorder)",
        "preferred": "COVID-19",
        "synonyms": ["Coronavirus disease 2019", "SARS-CoV-2 infection"],
    },
    {
        "id": "386661007",
        "fsn": "Dengue fever (disorder)",
        "preferred": "Dengue fever",
        "synonyms": ["Dengue", "Breakbone fever"],
    },
    # Key Symptoms & Clinical Findings
    {
        "id": "386661008",
        "fsn": "Fever (finding)",
        "preferred": "Fever",
        "synonyms": ["Pyrexia", "Elevated body temperature", "Febrile state"],
    },
    {
        "id": "49727002",
        "fsn": "Cough (finding)",
        "preferred": "Cough",
        "synonyms": ["Coughing", "Tussis"],
    },
    {
        "id": "25064002",
        "fsn": "Headache (finding)",
        "preferred": "Headache",
        "synonyms": ["Cephalalgia", "Head pain"],
    },
    {
        "id": "29857009",
        "fsn": "Chest pain (finding)",
        "preferred": "Chest pain",
        "synonyms": ["Thoracic pain", "Chest discomfort"],
    },
    {
        "id": "267036007",
        "fsn": "Dyspnea (finding)",
        "preferred": "Dyspnea",
        "synonyms": ["Shortness of breath", "Breathlessness", "SOB"],
    },
    {
        "id": "162397003",
        "fsn": "Pain in throat (finding)",
        "preferred": "Sore throat",
        "synonyms": ["Throat pain", "Pharyngeal pain"],
    },
    {
        "id": "64531003",
        "fsn": "Runny nose (finding)",
        "preferred": "Rhinorrhea",
        "synonyms": ["Runny nose", "Nasal discharge"],
    },
    {
        "id": "422587007",
        "fsn": "Nausea (finding)",
        "preferred": "Nausea",
        "synonyms": ["Feeling sick", "Queasiness"],
    },
    {
        "id": "422400008",
        "fsn": "Vomiting (finding)",
        "preferred": "Vomiting",
        "synonyms": ["Emesis", "Throwing up"],
    },
    {
        "id": "62315008",
        "fsn": "Diarrhea (finding)",
        "preferred": "Diarrhea",
        "synonyms": ["Loose stools", "Frequent watery bowel movements"],
    },
]

# ---------------------------------------------------------------------------
# 40 Common Singapore Drug Dictionary (SDD) Medications
# ---------------------------------------------------------------------------
SDD_SEED_MEDICATIONS = [
    # Analgesics & Antipyretics
    {
        "id": "SDD-000001",
        "name": "Panadol 500mg Tablet",
        "generic": "Paracetamol",
        "brand": "Panadol",
        "strength": "500mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12345P",
        "ingredients": [("Paracetamol", "500", "mg")],
    },
    {
        "id": "SDD-000002",
        "name": "Brufen 400mg Film-Coated Tablet",
        "generic": "Ibuprofen",
        "brand": "Brufen",
        "strength": "400mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12346P",
        "ingredients": [("Ibuprofen", "400", "mg")],
    },
    {
        "id": "SDD-000003",
        "name": "Voltaren 50mg Enteric-Coated Tablet",
        "generic": "Diclofenac Sodium",
        "brand": "Voltaren",
        "strength": "50mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12347P",
        "ingredients": [("Diclofenac Sodium", "50", "mg")],
    },
    {
        "id": "SDD-000004",
        "name": "Synflex 275mg Tablet",
        "generic": "Naproxen Sodium",
        "brand": "Synflex",
        "strength": "275mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12348P",
        "ingredients": [("Naproxen Sodium", "275", "mg")],
    },
    {
        "id": "SDD-000005",
        "name": "Tramal 50mg Capsule",
        "generic": "Tramadol Hydrochloride",
        "brand": "Tramal",
        "strength": "50mg",
        "form": "Capsule",
        "route": "Oral",
        "hsa": "SIN12349P",
        "ingredients": [("Tramadol Hydrochloride", "50", "mg")],
    },
    # Antibiotics
    {
        "id": "SDD-000006",
        "name": "Amoxicillin 500mg Capsule",
        "generic": "Amoxicillin",
        "brand": "Generic Amoxicillin",
        "strength": "500mg",
        "form": "Capsule",
        "route": "Oral",
        "hsa": "SIN12350P",
        "ingredients": [("Amoxicillin", "500", "mg")],
    },
    {
        "id": "SDD-000007",
        "name": "Augmentin 625mg Tablet",
        "generic": "Amoxicillin and Clavulanate Potassium",
        "brand": "Augmentin",
        "strength": "625mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12351P",
        "ingredients": [("Amoxicillin", "500", "mg"), ("Clavulanic Acid", "125", "mg")],
    },
    {
        "id": "SDD-000008",
        "name": "Zithromax 250mg Tablet",
        "generic": "Azithromycin",
        "brand": "Zithromax",
        "strength": "250mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12352P",
        "ingredients": [("Azithromycin", "250", "mg")],
    },
    {
        "id": "SDD-000009",
        "name": "Ciprobay 500mg Tablet",
        "generic": "Ciprofloxacin",
        "brand": "Ciprobay",
        "strength": "500mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12353P",
        "ingredients": [("Ciprofloxacin", "500", "mg")],
    },
    {
        "id": "SDD-000010",
        "name": "Vibramycin 100mg Capsule",
        "generic": "Doxycycline",
        "brand": "Vibramycin",
        "strength": "100mg",
        "form": "Capsule",
        "route": "Oral",
        "hsa": "SIN12354P",
        "ingredients": [("Doxycycline", "100", "mg")],
    },
    {
        "id": "SDD-000011",
        "name": "Flagyl 400mg Tablet",
        "generic": "Metronidazole",
        "brand": "Flagyl",
        "strength": "400mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12355P",
        "ingredients": [("Metronidazole", "400", "mg")],
    },
    {
        "id": "SDD-000012",
        "name": "Keflex 500mg Capsule",
        "generic": "Cephalexin",
        "brand": "Keflex",
        "strength": "500mg",
        "form": "Capsule",
        "route": "Oral",
        "hsa": "SIN12356P",
        "ingredients": [("Cephalexin", "500", "mg")],
    },
    # Cardiovascular & Antihypertensives
    {
        "id": "SDD-000013",
        "name": "Norvasc 5mg Tablet",
        "generic": "Amlodipine Besylate",
        "brand": "Norvasc",
        "strength": "5mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12357P",
        "ingredients": [("Amlodipine Besylate", "5", "mg")],
    },
    {
        "id": "SDD-000014",
        "name": "Cozaar 50mg Tablet",
        "generic": "Losartan Potassium",
        "brand": "Cozaar",
        "strength": "50mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12358P",
        "ingredients": [("Losartan Potassium", "50", "mg")],
    },
    {
        "id": "SDD-000015",
        "name": "Tenormin 50mg Tablet",
        "generic": "Atenolol",
        "brand": "Tenormin",
        "strength": "50mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12359P",
        "ingredients": [("Atenolol", "50", "mg")],
    },
    {
        "id": "SDD-000016",
        "name": "Betaloc 50mg Tablet",
        "generic": "Metoprolol Tartrate",
        "brand": "Betaloc",
        "strength": "50mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12360P",
        "ingredients": [("Metoprolol Tartrate", "50", "mg")],
    },
    {
        "id": "SDD-000017",
        "name": "Zocor 20mg Tablet",
        "generic": "Simvastatin",
        "brand": "Zocor",
        "strength": "20mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12361P",
        "ingredients": [("Simvastatin", "20", "mg")],
    },
    {
        "id": "SDD-000018",
        "name": "Lipitor 20mg Tablet",
        "generic": "Atorvastatin Calcium",
        "brand": "Lipitor",
        "strength": "20mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12362P",
        "ingredients": [("Atorvastatin Calcium", "20", "mg")],
    },
    {
        "id": "SDD-000019",
        "name": "Cardiprin 100mg Dispersible Tablet",
        "generic": "Aspirin (Acetylsalicylic Acid)",
        "brand": "Cardiprin",
        "strength": "100mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12363P",
        "ingredients": [("Aspirin", "100", "mg")],
    },
    {
        "id": "SDD-000020",
        "name": "Plavix 75mg Tablet",
        "generic": "Clopidogrel",
        "brand": "Plavix",
        "strength": "75mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12364P",
        "ingredients": [("Clopidogrel", "75", "mg")],
    },
    {
        "id": "SDD-000021",
        "name": "Marevan 5mg Tablet",
        "generic": "Warfarin Sodium",
        "brand": "Marevan",
        "strength": "5mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12365P",
        "ingredients": [("Warfarin Sodium", "5", "mg")],
    },
    # Diabetes Medications
    {
        "id": "SDD-000022",
        "name": "Glucophage 500mg Tablet",
        "generic": "Metformin Hydrochloride",
        "brand": "Glucophage",
        "strength": "500mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12366P",
        "ingredients": [("Metformin Hydrochloride", "500", "mg")],
    },
    {
        "id": "SDD-000023",
        "name": "Diamicron MR 60mg Modified-Release Tablet",
        "generic": "Gliclazide",
        "brand": "Diamicron MR",
        "strength": "60mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12367P",
        "ingredients": [("Gliclazide", "60", "mg")],
    },
    {
        "id": "SDD-000024",
        "name": "Januvia 100mg Tablet",
        "generic": "Sitagliptin Phosphate",
        "brand": "Januvia",
        "strength": "100mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12368P",
        "ingredients": [("Sitagliptin Phosphate", "100", "mg")],
    },
    {
        "id": "SDD-000025",
        "name": "Lantus 100IU/mL Solution for Injection",
        "generic": "Insulin Glargine",
        "brand": "Lantus",
        "strength": "100IU/mL",
        "form": "Injection",
        "route": "Subcutaneous",
        "hsa": "SIN12369P",
        "ingredients": [("Insulin Glargine", "100", "IU/mL")],
    },
    # Respiratory & Antihistamines
    {
        "id": "SDD-000026",
        "name": "Ventolin Evohaler 100mcg/dose",
        "generic": "Salbutamol Sulfate",
        "brand": "Ventolin",
        "strength": "100mcg/dose",
        "form": "Inhaler",
        "route": "Inhalation",
        "hsa": "SIN12370P",
        "ingredients": [("Salbutamol Sulfate", "100", "mcg")],
    },
    {
        "id": "SDD-000027",
        "name": "Pulmicort Turbuhaler 200mcg/dose",
        "generic": "Budesonide",
        "brand": "Pulmicort",
        "strength": "200mcg/dose",
        "form": "Inhaler",
        "route": "Inhalation",
        "hsa": "SIN12371P",
        "ingredients": [("Budesonide", "200", "mcg")],
    },
    {
        "id": "SDD-000028",
        "name": "Zyrtec 10mg Film-Coated Tablet",
        "generic": "Cetirizine Dihydrochloride",
        "brand": "Zyrtec",
        "strength": "10mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12372P",
        "ingredients": [("Cetirizine Dihydrochloride", "10", "mg")],
    },
    {
        "id": "SDD-000029",
        "name": "Clarityn 10mg Tablet",
        "generic": "Loratadine",
        "brand": "Clarityn",
        "strength": "10mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12373P",
        "ingredients": [("Loratadine", "10", "mg")],
    },
    {
        "id": "SDD-000030",
        "name": "Singulair 10mg Film-Coated Tablet",
        "generic": "Montelukast Sodium",
        "brand": "Singulair",
        "strength": "10mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12374P",
        "ingredients": [("Montelukast Sodium", "10", "mg")],
    },
    # Gastrointestinal
    {
        "id": "SDD-000031",
        "name": "Losec 20mg Capsule",
        "generic": "Omeprazole",
        "brand": "Losec",
        "strength": "20mg",
        "form": "Capsule",
        "route": "Oral",
        "hsa": "SIN12375P",
        "ingredients": [("Omeprazole", "20", "mg")],
    },
    {
        "id": "SDD-000032",
        "name": "Controloc 40mg Gastro-Resistant Tablet",
        "generic": "Pantoprazole Sodium",
        "brand": "Controloc",
        "strength": "40mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12376P",
        "ingredients": [("Pantoprazole Sodium", "40", "mg")],
    },
    {
        "id": "SDD-000033",
        "name": "Motilium 10mg Tablet",
        "generic": "Domperidone",
        "brand": "Motilium",
        "strength": "10mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12377P",
        "ingredients": [("Domperidone", "10", "mg")],
    },
    {
        "id": "SDD-000034",
        "name": "Imodium 2mg Capsule",
        "generic": "Loperamide Hydrochloride",
        "brand": "Imodium",
        "strength": "2mg",
        "form": "Capsule",
        "route": "Oral",
        "hsa": "SIN12378P",
        "ingredients": [("Loperamide Hydrochloride", "2", "mg")],
    },
    # Central Nervous System
    {
        "id": "SDD-000035",
        "name": "Zoloft 50mg Film-Coated Tablet",
        "generic": "Sertraline Hydrochloride",
        "brand": "Zoloft",
        "strength": "50mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12379P",
        "ingredients": [("Sertraline Hydrochloride", "50", "mg")],
    },
    {
        "id": "SDD-000036",
        "name": "Lexapro 10mg Film-Coated Tablet",
        "generic": "Escitalopram Oxalate",
        "brand": "Lexapro",
        "strength": "10mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12380P",
        "ingredients": [("Escitalopram Oxalate", "10", "mg")],
    },
    {
        "id": "SDD-000037",
        "name": "Valium 5mg Tablet",
        "generic": "Diazepam",
        "brand": "Valium",
        "strength": "5mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12381P",
        "ingredients": [("Diazepam", "5", "mg")],
    },
    {
        "id": "SDD-000038",
        "name": "Lyrica 75mg Capsule",
        "generic": "Pregabalin",
        "brand": "Lyrica",
        "strength": "75mg",
        "form": "Capsule",
        "route": "Oral",
        "hsa": "SIN12382P",
        "ingredients": [("Pregabalin", "75", "mg")],
    },
    # Endocrine & Anti-inflammatory
    {
        "id": "SDD-000039",
        "name": "Prednisolone 5mg Tablet",
        "generic": "Prednisolone",
        "brand": "Generic Prednisolone",
        "strength": "5mg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12383P",
        "ingredients": [("Prednisolone", "5", "mg")],
    },
    {
        "id": "SDD-000040",
        "name": "Euthyrox 50mcg Tablet",
        "generic": "Levothyroxine Sodium",
        "brand": "Euthyrox",
        "strength": "50mcg",
        "form": "Tablet",
        "route": "Oral",
        "hsa": "SIN12384P",
        "ingredients": [("Levothyroxine Sodium", "50", "mcg")],
    },
]


async def seed_data():
    """Seed synthetic development data into PostgreSQL."""
    logger.info("Starting synthetic development database seeding...")

    async with engine.begin() as conn:
        # Create all tables if not exist
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas verified.")

    async with async_session_factory() as session:
        # 1. Seed SNOMED CT Concepts and Descriptions
        snomed_count = 0
        for item in SNOMED_SEED_CONCEPTS:
            cid = item["id"]
            existing = await session.get(SnomedConcept, cid)
            if not existing:
                concept = SnomedConcept(
                    concept_id=cid,
                    effective_time=datetime.date(2024, 1, 1),
                    active=True,
                    module_id="900000000000207008",
                    definition_status_id="900000000000073002",
                )
                session.add(concept)

                # Add FSN
                fsn_desc = SnomedDescription(
                    description_id=f"{cid}01",
                    effective_time=datetime.date(2024, 1, 1),
                    active=True,
                    module_id="900000000000207008",
                    concept_id=cid,
                    language_code="en",
                    type_id="900000000000003001",  # FSN
                    term=item["fsn"],
                    case_significance_id="900000000000448009",
                )
                session.add(fsn_desc)

                # Add Preferred Term
                pref_desc = SnomedDescription(
                    description_id=f"{cid}02",
                    effective_time=datetime.date(2024, 1, 1),
                    active=True,
                    module_id="900000000000207008",
                    concept_id=cid,
                    language_code="en",
                    type_id="900000000000013009",  # Synonym / Preferred
                    term=item["preferred"],
                    case_significance_id="900000000000448009",
                )
                session.add(pref_desc)

                # Add Synonyms
                for s_idx, syn in enumerate(item.get("synonyms", [])):
                    syn_desc = SnomedDescription(
                        description_id=f"{cid}1{s_idx}",
                        effective_time=datetime.date(2024, 1, 1),
                        active=True,
                        module_id="900000000000207008",
                        concept_id=cid,
                        language_code="en",
                        type_id="900000000000013009",
                        term=syn,
                        case_significance_id="900000000000448009",
                    )
                    session.add(syn_desc)

                snomed_count += 1

        # Seed SNOMED metadata
        snomed_meta = SnomedReleaseMetadata(
            edition="Synthetic Dev Edition",
            version="2024-DEV-SEED",
            record_count=len(SNOMED_SEED_CONCEPTS),
        )
        session.add(snomed_meta)

        # 2. Seed SDD Medications and Ingredients
        sdd_count = 0
        for med_data in SDD_SEED_MEDICATIONS:
            mid = med_data["id"]
            existing_med = await session.get(SDDMedication, mid)
            if not existing_med:
                med = SDDMedication(
                    medication_id=mid,
                    name=med_data["name"],
                    generic_name=med_data["generic"],
                    brand_name=med_data["brand"],
                    strength=med_data["strength"],
                    dosage_form=med_data["form"],
                    route=med_data["route"],
                    hsa_reg_no=med_data["hsa"],
                    active=True,
                )
                session.add(med)

                for ing_name, str_val, str_unit in med_data.get("ingredients", []):
                    ing = SDDActiveIngredient(
                        medication_id=mid,
                        ingredient_name=ing_name,
                        strength_value=str_val,
                        strength_unit=str_unit,
                    )
                    session.add(ing)

                sdd_count += 1

        # Seed SDD metadata
        sdd_meta = SDDCatalogueMetadata(
            catalogue_version="2024-DEV-SEED",
            source="Synthetic Development Singapore Drug Dictionary",
            record_count=len(SDD_SEED_MEDICATIONS),
        )
        session.add(sdd_meta)

        await session.commit()

        # 3. Update PostgreSQL TSVectors for full text search if on PostgreSQL
        try:
            await session.execute(
                text("UPDATE snomed_descriptions SET search_vector = to_tsvector('english', term)")
            )
            await session.execute(
                text(
                    "UPDATE sdd_medications SET search_vector = "
                    "to_tsvector('english', coalesce(name, '') || ' ' || coalesce(generic_name, '') || ' ' || coalesce(brand_name, ''))"
                )
            )
            await session.commit()
            logger.info("Search tsvectors generated successfully.")
        except Exception as exc:
            logger.info(f"Note: PostgreSQL FTS index trigger skipped or not supported on this connection ({exc})")

        logger.info(f"Seeding complete! Added {snomed_count} SNOMED concepts and {sdd_count} SDD medications.")


if __name__ == "__main__":
    try:
        asyncio.run(seed_data())
    except Exception as exc:
        err_msg = str(exc)
        if "Connection refused" in err_msg or "CannotConnectNowError" in err_msg or "connect" in err_msg.lower():
            logger.error("\n" + "=" * 60)
            logger.error("DATABASE CONNECTION FAILED!")
            logger.error("PostgreSQL is not running on localhost:5432.")
            logger.error("Please start PostgreSQL first:")
            logger.error("  docker compose up -d")
            logger.error("Or start your local PostgreSQL service before running seed_dev_data.")
            logger.error("=" * 60 + "\n")
        else:
            logger.error(f"Seeding failed: {exc}", exc_info=True)


