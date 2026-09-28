#!/usr/bin/env python3
"""
Compiles complete, authentic datasets for Manak-SpecEngine:
1. data/standards_catalog.json (55+ fully-detailed standards across Construction, IT, Electrical, Chemicals, PPE, Solar)
2. data/qco_registry.json (13 active Quality Control Orders across 8 Ministries)
3. data/normative_graph_edges.csv (Relational knowledge graph edge list)
4. data/gem_tender_samples/ (15 realistic GeM/CPP tender specification documents)
"""

import json
import csv
import os

STANDARDS = [
    # --- CONSTRUCTION & STRUCTURAL STEEL ---
    {
        "is_number": "IS 2062",
        "title": "Hot Rolled Medium and High Tensile Structural Steel - Specification",
        "year": 2011,
        "amendments": [1, 2, 3],
        "status": "ACTIVE",
        "scope": "Covers requirements for hot rolled medium and high tensile structural steel for use in structural work, bridges, transmission towers, and general engineering purposes. Grades include E250, E275, E300, E350, E410, E450, E550, and E650 with designated sub-qualities A, BR, B0, and C based on Charpy V-notch impact test temperatures.",
        "committee": "MTD 4 (Wrought Steel Products)",
        "normative_references": ["IS 808", "IS 1730", "IS 1732", "IS 1852", "IS 8910", "IS 228"],
        "test_standards": ["IS 1608 (Part 1)", "IS 1599", "IS 1757 (Part 1)"],
        "keywords": ["structural steel", "hot rolled steel", "E250", "E350", "E410", "E450", "fe 410", "tensile strength", "yield strength", "charpy impact", "flats", "angles", "channels", "beams", "plates", "bridges", "transmission towers"],
        "historical_revisions": ["IS 2062:1962", "IS 2062:1969", "IS 2062:1980", "IS 2062:1984", "IS 2062:1992", "IS 2062:1999", "IS 2062:2006"]
    },
    {
        "is_number": "IS 1786",
        "title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement - Specification",
        "year": 2008,
        "amendments": [1, 2, 3, 4],
        "status": "ACTIVE",
        "scope": "Covers the requirements for thermo-mechanically treated (TMT) high strength deformed steel bars and wires for concrete reinforcement in grades Fe 415, Fe 415D, Fe 500, Fe 500D, Fe 550, Fe 550D, and Fe 600. Specifies chemical composition, minimum 0.2 percent proof stress, tensile strength, elongation, and bend/rebend tests.",
        "committee": "CED 54 (Concrete Reinforcement)",
        "normative_references": ["IS 228", "IS 2062"],
        "test_standards": ["IS 1608 (Part 1)", "IS 1599"],
        "keywords": ["tmt bars", "rebar", "concrete reinforcement", "fe 415", "fe 415d", "fe 500", "fe 500d", "fe 550", "fe 550d", "fe 600", "ribbed bars", "high strength deformed bars", "elongation", "proof stress", "bridge foundation", "rcc", "bend rebend"],
        "historical_revisions": ["IS 1786:1966", "IS 1786:1979", "IS 1786:1985"]
    },
    {
        "is_number": "IS 456",
        "title": "Plain and Reinforced Concrete - Code of Practice",
        "year": 2000,
        "amendments": [1, 2, 3, 4, 5],
        "status": "ACTIVE",
        "scope": "Deals with the general structural use of plain and reinforced concrete in construction. Specifies requirements for materials, design criteria for limit state and working stress methods, workmanship, inspection, and testing of structural concrete members.",
        "committee": "CED 2 (Cement and Concrete)",
        "normative_references": ["IS 269", "IS 383", "IS 432 (Part 1)", "IS 1489 (Part 1)", "IS 1786", "IS 8112", "IS 12269"],
        "test_standards": ["IS 516 (Part 1/Sec 1)", "IS 1199 (Part 1)"],
        "keywords": ["plain concrete", "reinforced concrete", "rcc", "concrete mix", "characteristic compressive strength", "water cement ratio", "curing", "slump test", "cube testing", "limit state design", "beams", "columns", "foundations", "civil engineering"],
        "historical_revisions": ["IS 456:1953", "IS 456:1964", "IS 456:1978"]
    },
    {
        "is_number": "IS 800",
        "title": "General Construction in Steel - Code of Practice",
        "year": 2007,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Provides rules and guidelines for the structural design of steel buildings, trusses, and industrial sheds using limit state design methodology. Covers member tension, compression, bending, combined stresses, connections (bolted and welded), and fatigue.",
        "committee": "CED 7 (Structural Engineering and Structural Sections)",
        "normative_references": ["IS 2062", "IS 808", "IS 1363", "IS 1367", "IS 816", "IS 8910"],
        "test_standards": ["IS 1608 (Part 1)"],
        "keywords": ["steel construction", "structural steel design", "limit state design", "steel truss", "bolted connections", "welded connections", "gantry girder", "industrial building", "compression member", "tension member"],
        "historical_revisions": ["IS 800:1956", "IS 800:1962", "IS 800:1984"]
    },
    {
        "is_number": "IS 10262",
        "title": "Concrete Mix Proportioning - Guidelines",
        "year": 2019,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Provides guidelines for proportioning ordinary, standard, and high-strength concrete mixes including self-compacting concrete and mass concrete. Covers target mean strength calculation, selection of water-cement ratio, air content, and mineral admixtures.",
        "committee": "CED 2 (Cement and Concrete)",
        "normative_references": ["IS 269", "IS 383", "IS 456", "IS 9103", "IS 15388"],
        "test_standards": ["IS 516 (Part 1/Sec 1)", "IS 1199 (Part 1)"],
        "keywords": ["concrete mix design", "mix proportioning", "target mean strength", "water cement ratio", "admixtures", "fly ash", "micro silica", "self compacting concrete", "m25", "m30", "m40", "m50", "m60"],
        "historical_revisions": ["IS 10262:1982", "IS 10262:2009"]
    },
    {
        "is_number": "IS 383",
        "title": "Coarse and Fine Aggregate for Concrete - Specification",
        "year": 2016,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Covers requirements for natural, manufactured, and recycled coarse and fine aggregates for use in production of concrete. Specifies grading limits, flakiness index, elongation index, aggregate crushing value, and soundness.",
        "committee": "CED 2 (Cement and Concrete)",
        "normative_references": ["IS 456"],
        "test_standards": ["IS 2386 (Part 1)", "IS 2386 (Part 2)", "IS 2386 (Part 3)", "IS 2386 (Part 4)"],
        "keywords": ["aggregates", "coarse aggregate", "fine aggregate", "sand", "crushed stone", "gravel", "m-sand", "manufactured sand", "grading zones", "fineness modulus", "silt content", "flakiness", "soundness"],
        "historical_revisions": ["IS 383:1952", "IS 383:1963", "IS 383:1970"]
    },
    {
        "is_number": "IS 269",
        "title": "Ordinary Portland Cement - Specification",
        "year": 2015,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Covers the manufacture and chemical and physical requirements of 33, 43, and 53 grade ordinary Portland cement. Specifies fineness, setting times, compressive strength, soundness, and loss on ignition.",
        "committee": "CED 2 (Cement and Concrete)",
        "normative_references": ["IS 456", "IS 3535"],
        "test_standards": ["IS 4031 (Part 5)", "IS 4031 (Part 6)", "IS 4032"],
        "keywords": ["opc", "ordinary portland cement", "opc 43", "opc 53", "opc 33", "cement bag", "compressive strength", "initial setting time", "final setting time", "soundness", "le chatelier", "clinker"],
        "historical_revisions": ["IS 269:1951", "IS 269:1958", "IS 269:1967", "IS 269:1976", "IS 269:1989"]
    },
    {
        "is_number": "IS 1489 (Part 1)",
        "title": "Portland Pozzolana Cement - Specification - Part 1 Fly Ash Based",
        "year": 2015,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Covers manufacture and requirements of fly ash based Portland Pozzolana cement (PPC). Specifies fly ash proportion (15% to 35%), physical and chemical requirements, and compressive strength development.",
        "committee": "CED 2 (Cement and Concrete)",
        "normative_references": ["IS 456", "IS 3812 (Part 1)"],
        "test_standards": ["IS 4031 (Part 5)", "IS 4031 (Part 6)", "IS 4032"],
        "keywords": ["ppc", "portland pozzolana cement", "fly ash cement", "pozzolana", "cement", "hydration heat", "durability", "coastal construction", "mass concrete"],
        "historical_revisions": ["IS 1489:1962", "IS 1489:1976", "IS 1489 (Part 1):1991"]
    },
    {
        "is_number": "IS 432 (Part 1)",
        "title": "Specification for Mild Steel and Medium Tensile Steel Bars and Hard-Drawn Steel Wire for Concrete Reinforcement - Part 1 Mild Steel and Medium Tensile Steel Bars",
        "year": 1982,
        "amendments": [1, 2],
        "status": "SUPERSEDED",
        "scope": "Covers requirements for mild steel and medium tensile steel bars in plain round profile. For high-strength deformed rebars and contemporary structural concrete, this standard is superseded by IS 1786 and IS 2062.",
        "committee": "CED 54 (Concrete Reinforcement)",
        "normative_references": ["IS 228"],
        "test_standards": ["IS 1608 (Part 1)", "IS 1599"],
        "keywords": ["mild steel bars", "plain round bars", "grade 1 mild steel", "superseded rebar", "deprecated steel", "obsolete construction standard"],
        "historical_revisions": ["IS 432:1953", "IS 432:1960", "IS 432 (Part 1):1966"]
    },
    {
        "is_number": "IS 13920",
        "title": "Ductile Design and Detailing of Reinforced Concrete Structures Subjected to Seismic Forces - Code of Practice",
        "year": 2016,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Covers the requirements for designing and detailing of RC structures to withstand seismic forces without brittle catastrophic failure. Mandatory for earthquake-resistant buildings in seismic zones III, IV, and V.",
        "committee": "CED 39 (Earthquake Engineering)",
        "normative_references": ["IS 456", "IS 1786", "IS 1893 (Part 1)"],
        "test_standards": ["IS 1608 (Part 1)"],
        "keywords": ["ductile detailing", "earthquake resistance", "seismic zone", "reinforcement detailing", "shear stirrups", "beam column joint", "confinement reinforcement", "lateral load", "bms", "building code"],
        "historical_revisions": ["IS 13920:1993"]
    },
    {
        "is_number": "IS 1893 (Part 1)",
        "title": "Criteria for Earthquake Resistant Design of Structures - Part 1 General Provisions and Buildings",
        "year": 2016,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Deals with assessment of seismic forces for earthquake resistant design of structures. Details seismic zone maps of India (Zones II, III, IV, V), response spectra, and structural analysis procedures.",
        "committee": "CED 39 (Earthquake Engineering)",
        "normative_references": ["IS 456", "IS 800", "IS 13920"],
        "test_standards": [],
        "keywords": ["seismic design", "earthquake criteria", "seismic zone map", "response spectrum", "base shear", "response reduction factor", "structural analysis", "building safety"],
        "historical_revisions": ["IS 1893:1962", "IS 1893:1966", "IS 1893:1970", "IS 1893:1975", "IS 1893:1984", "IS 1893 (Part 1):2002"]
    },
    {
        "is_number": "IS 1077",
        "title": "Common Burnt Clay Building Bricks - Specification",
        "year": 1992,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Covers dimensions, compressive strength, water absorption, and efflorescence requirements for common burnt clay building bricks of classes 3.5 to 35.",
        "committee": "CED 30 (Clay and Stabilized Soil Products for Construction)",
        "normative_references": ["IS 3495 (Part 1)", "IS 3495 (Part 2)", "IS 3495 (Part 3)"],
        "test_standards": ["IS 3495 (Part 1)", "IS 3495 (Part 2)"],
        "keywords": ["clay bricks", "building bricks", "red bricks", "compressive strength class", "water absorption", "efflorescence", "masonry wall"],
        "historical_revisions": ["IS 1077:1957", "IS 1077:1970", "IS 1077:1976", "IS 1077:1986"]
    },
    {
        "is_number": "IS 2185 (Part 1)",
        "title": "Concrete Masonry Units - Specification - Part 1 Hollow and Solid Concrete Blocks",
        "year": 2005,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Specifies physical requirements, dimensions, tolerances, compressive strength, and drying shrinkage of hollow and solid concrete blocks used for load-bearing and non-load-bearing walls.",
        "committee": "CED 53 (Cement Matrix Products)",
        "normative_references": ["IS 269", "IS 383", "IS 456"],
        "test_standards": ["IS 2185 (Part 1)"],
        "keywords": ["concrete blocks", "hollow concrete blocks", "solid blocks", "cmu", "masonry blocks", "load bearing wall", "compressive strength"],
        "historical_revisions": ["IS 2185:1962", "IS 2185:1967", "IS 2185 (Part 1):1979"]
    },

    # --- TESTING & CHARACTERIZATION STANDARDS ---
    {
        "is_number": "IS 1608 (Part 1)",
        "title": "Metallic Materials - Tensile Testing - Part 1 Method of Test at Room Temperature",
        "year": 2018,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Specifies the method for tensile testing of metallic materials at room temperature and defines the mechanical properties (yield strength, 0.2% proof stress, tensile strength, percentage elongation). Identical to ISO 6892-1.",
        "committee": "MTD 3 (Mechanical Testing of Metals)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["tensile testing", "tensile test method", "yield stress", "proof stress", "ultimate tensile strength", "elongation", "gauge length", "universal testing machine", "utm"],
        "historical_revisions": ["IS 1608:1960", "IS 1608:1972", "IS 1608:1995", "IS 1608:2005"]
    },
    {
        "is_number": "IS 1599",
        "title": "Metallic Materials - Bend Test",
        "year": 2019,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Specifies the method for determining the ability of metallic materials to undergo plastic deformation in bending. Applicable to test pieces from metallic products.",
        "committee": "MTD 3 (Mechanical Testing of Metals)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["bend test", "rebend test", "plastic deformation", "mandrel diameter", "crack formation", "ductility test", "metals testing"],
        "historical_revisions": ["IS 1599:1960", "IS 1599:1974", "IS 1599:1985"]
    },
    {
        "is_number": "IS 1757 (Part 1)",
        "title": "Metallic Materials - Charpy Pendulum Impact Test - Part 1 Test Method",
        "year": 2020,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Specifies the Charpy pendulum impact (V-notch and U-notch) test method for determining the energy absorbed in an impact test of metallic materials. Crucial for assessing toughness at low temperatures.",
        "committee": "MTD 3 (Mechanical Testing of Metals)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["charpy test", "impact test", "v-notch", "absorbed energy", "joules", "impact toughness", "brittle fracture", "sub-zero testing"],
        "historical_revisions": ["IS 1757:1961", "IS 1757:1973", "IS 1757:1988"]
    },
    {
        "is_number": "IS 1852",
        "title": "Rolling and Cutting Tolerances for Hot Rolled Steel Products - Specification",
        "year": 1985,
        "amendments": [1, 2, 3],
        "status": "ACTIVE",
        "scope": "Prescribes rolling and cutting tolerances for hot rolled structural steel sections (beams, columns, channels, angles, tee bars), plates, sheets, strips, and round and square bars.",
        "committee": "MTD 4 (Wrought Steel Products)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["rolling tolerances", "cutting tolerances", "dimensional tolerances", "thickness tolerance", "length tolerance", "camber", "out of squareness", "structural sections"],
        "historical_revisions": ["IS 1852:1962", "IS 1852:1973", "IS 1852:1979"]
    },
    {
        "is_number": "IS 8910",
        "title": "General Technical Delivery Requirements for Steel and Steel Products",
        "year": 2010,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Specifies general technical delivery requirements for all steel products specified in Indian Standards, covering ordering information, manufacturing process, inspection, testing, certificate of compliance, and marking.",
        "committee": "MTD 4 (Wrought Steel Products)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["technical delivery conditions", "inspection documents", "test certificate", "marking", "traceability", "mill test report", "heat number"],
        "historical_revisions": ["IS 8910:1978"]
    },
    {
        "is_number": "IS 228 (Part 1)",
        "title": "Methods of Chemical Analysis of Steels - Part 1 Determination of Carbon by Volumetric Method",
        "year": 1987,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Prescribes volumetric method for determination of carbon in plain carbon and low alloy steels in the range 0.05% to 2.50%.",
        "committee": "MTD 2 (Chemical Analysis of Metals)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["chemical analysis of steel", "carbon content", "spectroscopy", "combustion method", "ladle analysis", "carbon equivalent"],
        "historical_revisions": ["IS 228:1952", "IS 228:1959"]
    },
    {
        "is_number": "IS 808",
        "title": "Dimensions for Hot Rolled Steel Beam, Column, Channel and Angle Sections",
        "year": 1989,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Specifies nominal dimensions, mass, and sectional properties of hot rolled steel beams, columns, channels, equal angles, and unequal angles.",
        "committee": "CED 7 (Structural Engineering and Structural Sections)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["steel sections", "isjc", "islc", "ismb", "iswb", "ishb", "isjc beam", "channel section", "equal angle", "unequal angle", "moment of inertia", "section modulus"],
        "historical_revisions": ["IS 808:1957", "IS 808:1964"]
    },
    {
        "is_number": "IS 516 (Part 1/Sec 1)",
        "title": "Hardened Concrete - Methods of Test - Part 1 Testing of Strength - Section 1 Compressive, Flexural and Split Tensile Strength",
        "year": 2021,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Specifies procedures for testing compressive strength of concrete cubes and cylinders, flexural strength of beams, and splitting tensile strength of cylinders.",
        "committee": "CED 2 (Cement and Concrete)",
        "normative_references": ["IS 456"],
        "test_standards": [],
        "keywords": ["compressive strength of concrete", "cube test", "cube testing", "flexural strength", "split tensile test", "compression testing machine", "ctm", "28 days strength"],
        "historical_revisions": ["IS 516:1959"]
    },
    {
        "is_number": "IS 1199 (Part 1)",
        "title": "Fresh Concrete - Methods of Sampling, Testing and Analysis - Part 1 Sampling of Fresh Concrete",
        "year": 2018,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Prescribes procedures for obtaining composite samples of fresh concrete from transit mixers, stationary mixers, or agitating trucks for consistency and strength testing.",
        "committee": "CED 2 (Cement and Concrete)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["fresh concrete", "sampling concrete", "slump cone", "workability", "compaction factor", "flow table"],
        "historical_revisions": ["IS 1199:1959"]
    },
    {
        "is_number": "IS 2386 (Part 1)",
        "title": "Methods of Test for Aggregates for Concrete - Part 1 Particle Size and Shape",
        "year": 1963,
        "amendments": [1, 2, 3],
        "status": "ACTIVE",
        "scope": "Covers sieve analysis of fine and coarse aggregates, determination of flakiness index, elongation index, and angularity number.",
        "committee": "CED 2 (Cement and Concrete)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["sieve analysis", "aggregate testing", "flakiness index", "elongation index", "fineness modulus", "particle size"],
        "historical_revisions": []
    },
    {
        "is_number": "IS 3495 (Part 1)",
        "title": "Methods of Tests of Burnt Clay Building Bricks - Part 1 Determination of Compressive Strength",
        "year": 1992,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Covers the procedure for determining compressive strength of burnt clay building bricks using frog-filled prepared brick specimens.",
        "committee": "CED 30 (Clay and Stabilized Soil Products)",
        "normative_references": ["IS 1077"],
        "test_standards": [],
        "keywords": ["brick testing", "brick compressive strength", "frog filling", "clay brick test"],
        "historical_revisions": ["IS 3495:1966", "IS 3495 (Part 1):1973", "IS 3495 (Part 1):1976"]
    },
    {
        "is_number": "IS 4031 (Part 5)",
        "title": "Methods of Physical Tests for Hydraulic Cement - Part 5 Determination of Initial and Final Setting Times",
        "year": 1988,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Prescribes method of determining initial and final setting times of hydraulic cement using the Vicat apparatus.",
        "committee": "CED 2 (Cement and Concrete)",
        "normative_references": ["IS 269", "IS 1489 (Part 1)"],
        "test_standards": [],
        "keywords": ["cement setting time", "vicat apparatus", "initial setting time", "final setting time", "normal consistency"],
        "historical_revisions": ["IS 4031:1968"]
    },

    # --- ELECTRONICS, IT & APPLIANCES (MeitY CRS & DPIIT) ---
    {
        "is_number": "IS 13252 (Part 1)",
        "title": "Information Technology Equipment - Safety - Part 1 General Requirements",
        "year": 2010,
        "amendments": [1, 2, 3],
        "status": "ACTIVE",
        "scope": "Specifies safety requirements for mains-powered or battery-powered information technology equipment, including computer hardware, laptops, servers, power adapters, and peripherals. Covers electrical shock, thermal hazards, fire resistance, and mechanical hazards.",
        "committee": "LITD 08 (Information Technology Equipment)",
        "normative_references": ["IS 616", "IS 1293", "IS 302-1"],
        "test_standards": ["IS 13252 (Part 1)"],
        "keywords": ["it equipment", "computers", "laptops", "notebooks", "tablets", "servers", "power adapters", "smps", "safety requirements", "electric shock", "creepage distance", "fire enclosure", "crs registration", "meity mandate"],
        "historical_revisions": ["IS 13252:2003"]
    },
    {
        "is_number": "IS 16046 (Part 1)",
        "title": "Secondary Cells and Batteries Containing Alkaline or Other Non-Acid Electrolytes - Safety Requirements - Part 1 Nickel Systems",
        "year": 2018,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Specifies requirements and tests for the safe operation of secondary nickel cells and batteries for portable applications.",
        "committee": "ETD 11 (Secondary Cells and Batteries)",
        "normative_references": [],
        "test_standards": ["IS 16046 (Part 1)"],
        "keywords": ["nickel batteries", "ni-mh cells", "portable batteries", "crs scheme", "battery safety"],
        "historical_revisions": ["IS 16046:2012", "IS 16046:2015"]
    },
    {
        "is_number": "IS 16046 (Part 2)",
        "title": "Secondary Cells and Batteries Containing Alkaline or Other Non-Acid Electrolytes - Safety Requirements - Part 2 Lithium Systems",
        "year": 2018,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Specifies requirements and tests for the safe operation of portable sealed secondary lithium cells and batteries (Li-ion, Li-polymer) used in electronic devices, laptops, smartphones, and power banks. Covers overcharge, short circuit, thermal abuse, and crushing tests.",
        "committee": "ETD 11 (Secondary Cells and Batteries)",
        "normative_references": [],
        "test_standards": ["IS 16046 (Part 2)"],
        "keywords": ["lithium ion batteries", "li-ion battery", "battery pack", "power bank", "smartphones", "thermal runaway", "short circuit test", "overcharge test", "crs battery mandate", "portable electronics"],
        "historical_revisions": ["IS 16046:2012", "IS 16046:2015"]
    },
    {
        "is_number": "IS 616",
        "title": "Audio, Video and Similar Electronic Apparatus - Safety Requirements",
        "year": 2017,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Applies to electronic apparatus designed to be fed from mains, supply apparatus, batteries, or remote feeding, for reception, generation, recording, or reproduction of audio, video, and associated signals (TVs, monitors, amplifiers, audio systems).",
        "committee": "LITD 07 (Audio, Video and Multimedia Systems)",
        "normative_references": ["IS 1293"],
        "test_standards": ["IS 616"],
        "keywords": ["audio video", "television", "led tv", "smart tv", "amplifiers", "sound systems", "video monitors", "dielectric strength", "radiation hazard", "meity crs"],
        "historical_revisions": ["IS 616:1957", "IS 616:1981", "IS 616:2003", "IS 616:2010"]
    },
    {
        "is_number": "IS 302-2-25",
        "title": "Safety of Household and Similar Electrical Appliances - Part 2 Particular Requirements - Section 25 Microwave Ovens, Including Combination Microwave Ovens",
        "year": 2014,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Deals with the safety of microwave ovens for household and similar use, their rated voltage being not more than 250 V single phase. Mandatory under MeitY Compulsory Registration Scheme.",
        "committee": "ETD 32 (Electrical Appliances)",
        "normative_references": ["IS 302-1", "IS 1293"],
        "test_standards": ["IS 302-2-25"],
        "keywords": ["microwave ovens", "combination microwave", "microwave radiation leakage", "interlocks", "household safety", "meity crs"],
        "historical_revisions": ["IS 302-2-25:1994"]
    },
    {
        "is_number": "IS 1293",
        "title": "Plugs and Socket-Outlets for Domestic and Similar Purposes of Rated Voltage up to and Including 250 V and Rated Current up to and Including 16 A - Specification",
        "year": 2019,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Applies to plugs and fixed or portable socket-outlets for a.c. only, with or without earthing contact, with rated voltage not exceeding 250 V and rated current up to 16 A, intended for household and commercial use. Mandatory under DPIIT QCO.",
        "committee": "ETD 14 (Electrical Wiring Accessories)",
        "normative_references": [],
        "test_standards": ["IS 1293"],
        "keywords": ["plugs", "socket outlets", "power cords", "3 pin plug", "6a plug", "16a socket", "power strip", "extension cord", "shutter safety", "earthing pin", "dpiit qco"],
        "historical_revisions": ["IS 1293:1967", "IS 1293:1988", "IS 1293:2005"]
    },
    {
        "is_number": "IS 15885 (Part 2/Sec 13)",
        "title": "Lamp Controlgear - Part 2 Particular Requirements - Section 13 DC or AC Supplied Electronic Controlgear for LED Modules",
        "year": 2012,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Covers particular safety requirements for electronic controlgear (LED drivers) for use on d.c. supplies up to 250 V and a.c. supplies up to 1000 V at 50 Hz or 60 Hz.",
        "committee": "ETD 23 (Electric Lamps and Luminaires)",
        "normative_references": ["IS 15885 (Part 1)"],
        "test_standards": ["IS 15885 (Part 2/Sec 13)"],
        "keywords": ["led driver", "lamp controlgear", "electronic controlgear", "led lighting", "power supply for led", "crs scheme"],
        "historical_revisions": []
    },
    {
        "is_number": "IS 16102 (Part 1)",
        "title": "Self-Ballasted LED Lamps for General Lighting Services - Part 1 Safety Requirements",
        "year": 2012,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Specifies the safety and interchangeability requirements, together with test methods and conditions required to show compliance of LED lamps with integrated means for controlling, intended for domestic lighting.",
        "committee": "ETD 23 (Electric Lamps and Luminaires)",
        "normative_references": ["IS 16102 (Part 2)"],
        "test_standards": ["IS 16102 (Part 1)"],
        "keywords": ["led bulb", "led lamp", "self ballasted led", "lighting", "b22 cap", "e27 cap", "cree led", "crs registration"],
        "historical_revisions": []
    },

    # --- ELECTRICAL CABLES, TRANSFORMERS & POWER ---
    {
        "is_number": "IS 694",
        "title": "Polyvinyl Chloride Insulated Unsheathed and Sheathed Cables/Cords with Rigid and Flexible Conductor for Rated Voltages up to and Including 450/750 V",
        "year": 2010,
        "amendments": [1, 2, 3],
        "status": "ACTIVE",
        "scope": "Covers requirements for single-core and multi-core PVC insulated unsheathed and sheathed cables with copper or aluminium conductors for electric power and lighting in residential, commercial, and industrial installations.",
        "committee": "ETD 9 (Power Cables)",
        "normative_references": ["IS 8130", "IS 5831"],
        "test_standards": ["IS 10810 (Part 43)", "IS 10810 (Part 45)"],
        "keywords": ["pvc wire", "house wiring", "electric cable", "copper conductor", "flexible wire", "fr cable", "frls wire", "450/750v", "isi mark cable", "heavy industries qco"],
        "historical_revisions": ["IS 694:1960", "IS 694:1977", "IS 694:1990"]
    },
    {
        "is_number": "IS 1554 (Part 1)",
        "title": "PVC Insulated (Heavy Duty) Electric Cables - Specification - Part 1 For Working Voltages up to and Including 1100 V",
        "year": 1988,
        "amendments": [1, 2, 3, 4],
        "status": "ACTIVE",
        "scope": "Covers requirements of PVC insulated armoured and unarmoured heavy duty cables for working voltages up to and including 1100 V for electricity distribution.",
        "committee": "ETD 9 (Power Cables)",
        "normative_references": ["IS 8130", "IS 5831", "IS 3975"],
        "test_standards": ["IS 10810 (Part 43)"],
        "keywords": ["armoured cable", "power cable", "heavy duty cable", "lt cable", "1.1 kv cable", "pvc armoured", "underground cable"],
        "historical_revisions": ["IS 1554:1964", "IS 1554 (Part 1):1976"]
    },
    {
        "is_number": "IS 7098 (Part 1)",
        "title": "Cross-linked Polyethylene Insulated Thermoplastic Sheathed Cables - Specification - Part 1 For Working Voltage up to and Including 1100 V",
        "year": 1988,
        "amendments": [1, 2, 3],
        "status": "ACTIVE",
        "scope": "Covers requirements of cross-linked polyethylene (XLPE) insulated armoured and unarmoured cables for electric supply at voltages up to 1100 V.",
        "committee": "ETD 9 (Power Cables)",
        "normative_references": ["IS 8130", "IS 5831"],
        "test_standards": ["IS 10810 (Part 43)"],
        "keywords": ["xlpe cable", "cross linked polyethylene", "lt xlpe", "power cable", "high thermal capacity", "underground distribution"],
        "historical_revisions": ["IS 7098 (Part 1):1977"]
    },
    {
        "is_number": "IS 1180 (Part 1)",
        "title": "Outdoor Type Oil Immersed Distribution Transformers up to and Including 2500 kVA, 33 kV - Specification",
        "year": 2014,
        "amendments": [1, 2, 3, 4],
        "status": "ACTIVE",
        "scope": "Covers requirements for outdoor type oil immersed distribution transformers up to and including 2500 kVA, 33 kV, with standard energy efficiency levels (Level 1, Level 2, Level 3). Mandatory under Ministry of Heavy Industries QCO.",
        "committee": "ETD 16 (Transformers)",
        "normative_references": ["IS 335", "IS 2026 (Part 1)", "IS 3639"],
        "test_standards": ["IS 1180 (Part 1)"],
        "keywords": ["distribution transformer", "oil immersed transformer", "2500 kva", "11kv transformer", "33kv transformer", "energy efficiency star rating", "bee star rating", "isi mark transformer", "heavy industries qco"],
        "historical_revisions": ["IS 1180:1958", "IS 1180 (Part 1):1989"]
    },

    # --- PIPES, POLYMERS & CHEMICALS ---
    {
        "is_number": "IS 4984",
        "title": "High Density Polyethylene Pipes for Water Supply - Specification",
        "year": 2016,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Covers requirements for high density polyethylene (HDPE) pipes made from PE 63, PE 80, and PE 100 materials for buried water mains and distribution lines, carrying potable water under pressure.",
        "committee": "PCD 20 (Plastics Piping Systems)",
        "normative_references": ["IS 7328", "IS 2530"],
        "test_standards": ["IS 12235 (Part 1)", "IS 12235 (Part 2)"],
        "keywords": ["hdpe pipe", "polyethylene pipe", "pe 100", "pe 80", "water supply pipe", "potable water distribution", "butt fusion", "pn 6", "pn 10", "pn 16", "chemicals qco"],
        "historical_revisions": ["IS 4984:1968", "IS 4984:1972", "IS 4984:1987", "IS 4984:1995"]
    },
    {
        "is_number": "IS 4985",
        "title": "Unplasticized Polyvinyl Chloride (uPVC) Pipes for Potable Water Supplies - Specification",
        "year": 2021,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Covers requirements for plain and socket-ended uPVC pipes for potable water conveyance, agricultural irrigation, and civil water networks.",
        "committee": "PCD 20 (Plastics Piping Systems)",
        "normative_references": ["IS 7634 (Part 3)"],
        "test_standards": ["IS 12235 (Part 1)", "IS 12235 (Part 2)"],
        "keywords": ["upvc pipe", "pvc water pipe", "potable water supply", "plumbing pipe", "solvent weld", "ring fit", "pn 4", "pn 6", "pn 10"],
        "historical_revisions": ["IS 4985:1968", "IS 4985:1981", "IS 4985:1988", "IS 4985:2000"]
    },
    {
        "is_number": "IS 7328",
        "title": "High Density Polyethylene Materials for Moulding and Extrusion - Specification",
        "year": 2020,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Covers requirements and test methods for virgin and recycled HDPE raw material granules used for extrusion of pipes, sheets, and blow moulding.",
        "committee": "PCD 12 (Plastics)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["hdpe granules", "raw material", "melt flow rate", "density", "extrusion compound", "virgin polymer", "chemicals qco"],
        "historical_revisions": ["IS 7328:1974", "IS 7328:1992"]
    },
    {
        "is_number": "IS 12235 (Part 1)",
        "title": "Thermoplastics Pipes and Fittings - Methods of Test - Part 1 Measurement of Dimensions",
        "year": 2004,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Specifies methods for measuring dimensions (outside diameter, wall thickness, ovality, length) of thermoplastic pipes and fittings.",
        "committee": "PCD 20 (Plastics Piping Systems)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["pipe testing", "wall thickness measurement", "pipe diameter", "thermoplastics testing", "ovality test"],
        "historical_revisions": ["IS 12235 (Part 1):1986"]
    },
    {
        "is_number": "IS 12235 (Part 2)",
        "title": "Thermoplastics Pipes and Fittings - Methods of Test - Part 2 Determination of Density",
        "year": 2004,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Prescribes method for determining the density of non-cellular thermoplastic pipes and fittings using immersion method.",
        "committee": "PCD 20 (Plastics Piping Systems)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["density test", "pipe density", "immersion method", "polymer density"],
        "historical_revisions": ["IS 12235 (Part 2):1986"]
    },
    {
        "is_number": "IS 252",
        "title": "Caustic Soda, Pure and Technical - Specification",
        "year": 2013,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Prescribes requirements and methods of sampling and test for caustic soda (sodium hydroxide), solid, flakes, pellets, and lye. Mandatory under Ministry of Chemicals QCO.",
        "committee": "CHD 1 (Inorganic Chemicals)",
        "normative_references": [],
        "test_standards": [],
        "keywords": ["caustic soda", "sodium hydroxide", "naoh", "caustic flakes", "caustic lye", "industrial chemicals", "chemicals qco"],
        "historical_revisions": ["IS 252:1950", "IS 252:1962", "IS 252:1973", "IS 252:1991"]
    },

    # --- PERSONAL PROTECTIVE EQUIPMENT (PPE) & CONSUMER SAFETY ---
    {
        "is_number": "IS 2925",
        "title": "Specification for Industrial Safety Helmets",
        "year": 1984,
        "amendments": [1, 2, 3],
        "status": "ACTIVE",
        "scope": "Covers physical and performance requirements, methods of test, and marking of helmets for protection of workers in industrial workplaces against falling objects and mechanical impact.",
        "committee": "CHD 8 (Occupational Safety and Health)",
        "normative_references": [],
        "test_standards": ["IS 2925"],
        "keywords": ["safety helmet", "industrial helmet", "hard hat", "construction helmet", "head protection", "shock absorption test", "penetration resistance", "ppe"],
        "historical_revisions": ["IS 2925:1964", "IS 2925:1975"]
    },
    {
        "is_number": "IS 15298 (Part 2)",
        "title": "Personal Protective Equipment - Safety Footwear - Specification",
        "year": 2016,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Specifies basic and additional requirements for safety footwear used for commercial and industrial purposes, equipped with toecaps designed to provide protection against impact of 200 Joules and compression of 15 kN. Mandatory under DPIIT Footwear QCO.",
        "committee": "CHD 8 (Occupational Safety and Health)",
        "normative_references": ["IS 15298 (Part 1)"],
        "test_standards": ["IS 15298 (Part 2)"],
        "keywords": ["safety shoes", "safety footwear", "steel toe shoes", "safety boots", "slip resistance", "toe impact 200j", "puncture resistance", "dpiit footwear qco", "ppe"],
        "historical_revisions": ["IS 15298 (Part 2):2002", "IS 15298 (Part 2):2011"]
    },
    {
        "is_number": "IS 4151",
        "title": "Protective Helmets for Two Wheeler Riders - Specification",
        "year": 2015,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Specifies requirements for helmets for riders of two-wheel motor vehicles. Covers peripheral vision, impact absorption, retention system strength, and audibility. Mandatory under MORTH QCO.",
        "committee": "TED 26 (Automotive Safety)",
        "normative_references": [],
        "test_standards": ["IS 4151"],
        "keywords": ["motorcycle helmet", "two wheeler helmet", "rider helmet", "isi mark helmet", "impact absorption", "morth qco"],
        "historical_revisions": ["IS 4151:1967", "IS 4151:1976", "IS 4151:1982", "IS 4151:1993"]
    },
    {
        "is_number": "IS 9873 (Part 1)",
        "title": "Safety of Toys - Part 1 Safety Aspects Related to Mechanical and Physical Properties",
        "year": 2019,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Specifies acceptable criteria for the structural and mechanical characteristics of toys for children up to 14 years. Mandatory under DPIIT Safety of Toys QCO.",
        "committee": "CHD 33 (Toys)",
        "normative_references": [],
        "test_standards": ["IS 9873 (Part 1)"],
        "keywords": ["toy safety", "children toys", "mechanical hazards", "choking hazard", "sharp edges", "dpiit toys qco"],
        "historical_revisions": ["IS 9873 (Part 1):2001", "IS 9873 (Part 1):2012"]
    },
    {
        "is_number": "IS 15644",
        "title": "Safety of Electric Toys",
        "year": 2006,
        "amendments": [1, 2],
        "status": "ACTIVE",
        "scope": "Specifies safety requirements for electric toys having at least one function dependent on electricity, operated by battery or transformer. Mandatory under DPIIT Safety of Toys QCO.",
        "committee": "CHD 33 (Toys)",
        "normative_references": ["IS 9873 (Part 1)"],
        "test_standards": ["IS 15644"],
        "keywords": ["electric toys", "battery operated toys", "toy electronics", "electrical safety", "dpiit toys qco"],
        "historical_revisions": []
    },
    {
        "is_number": "IS 303",
        "title": "Plywood for General Purposes - Specification",
        "year": 1989,
        "amendments": [1, 2, 3, 4, 5, 6],
        "status": "ACTIVE",
        "scope": "Covers requirements for BWR (Boiling Water Resistant) and MR (Moisture Resistant) grades of general-purpose plywood. Mandatory under DPIIT Plywood QCO.",
        "committee": "CED 20 (Wood and Other Lignocellulosic Based Building Products)",
        "normative_references": ["IS 1734"],
        "test_standards": ["IS 1734"],
        "keywords": ["plywood", "bwr plywood", "mr plywood", "commercial plywood", "timber products", "dpiit plywood qco", "furniture board"],
        "historical_revisions": ["IS 303:1951", "IS 303:1960", "IS 303:1975"]
    },
    {
        "is_number": "IS 710",
        "title": "Marine Plywood - Specification",
        "year": 2010,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Specifies requirements for marine plywood manufactured from selected hardwood veneers bonded with phenol formaldehyde synthetic resin adhesive. Suitable for shipbuilding and extreme moisture applications.",
        "committee": "CED 20 (Wood and Other Lignocellulosic Products)",
        "normative_references": ["IS 1734"],
        "test_standards": ["IS 1734"],
        "keywords": ["marine plywood", "boiling waterproof", "bwp", "shipbuilding plywood", "exterior wood", "phenol resin", "dpiit plywood qco"],
        "historical_revisions": ["IS 710:1957", "IS 710:1976"]
    },

    # --- SOLAR & RENEWABLE ENERGY (MNRE) ---
    {
        "is_number": "IS 14286",
        "title": "Crystalline Silicon Terrestrial Photovoltaic (PV) Modules - Design Qualification and Type Approval",
        "year": 2010,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Lays down requirements for design qualification and type approval of terrestrial crystalline silicon photovoltaic modules for long-term outdoor operation. Mandatory under MNRE Solar CRS Order.",
        "committee": "ETD 28 (Solar Photovoltaic Energy Systems)",
        "normative_references": ["IS/IEC 61730 (Part 1)", "IS/IEC 61730 (Part 2)"],
        "test_standards": ["IS 14286"],
        "keywords": ["solar pv module", "photovoltaic panels", "solar panels", "crystalline silicon", "type approval", "thermal cycling test", "hail test", "damp heat test", "mnre solar crs"],
        "historical_revisions": []
    },
    {
        "is_number": "IS/IEC 61730 (Part 1)",
        "title": "Photovoltaic (PV) Module Safety Qualification - Part 1 Requirements for Construction",
        "year": 2004,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Describes the fundamental construction requirements for photovoltaic modules in order to provide safe electrical and mechanical operation during their expected lifetime.",
        "committee": "ETD 28 (Solar Photovoltaic Energy Systems)",
        "normative_references": ["IS 14286"],
        "test_standards": ["IS/IEC 61730 (Part 1)"],
        "keywords": ["solar module safety", "pv safety qualification", "solar panel construction", "electrical insulation", "mnre solar crs"],
        "historical_revisions": []
    },
    {
        "is_number": "IS 16221 (Part 2)",
        "title": "Safety of Power Converters for Use in Photovoltaic Power Systems - Part 2 Particular Requirements for Inverters",
        "year": 2015,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Gives particular safety requirements for grid-connected and standalone inverters used in photovoltaic power systems. Mandatory under MNRE Solar Order.",
        "committee": "ETD 28 (Solar Photovoltaic Energy Systems)",
        "normative_references": [],
        "test_standards": ["IS 16221 (Part 2)"],
        "keywords": ["solar inverter", "grid tie inverter", "pv inverter", "power converter", "mnre solar crs"],
        "historical_revisions": []
    },

    # --- WATER & PUBLIC HEALTH ---
    {
        "is_number": "IS 14543",
        "title": "Packaged Drinking Water (Other than Packaged Natural Mineral Water) - Specification",
        "year": 2016,
        "amendments": [1, 2, 3],
        "status": "ACTIVE",
        "scope": "Prescribes requirements and methods of sampling and test for packaged drinking water other than packaged natural mineral water. Must be treated by filtration, demineralization, and disinfection before packaging. Mandatory under Food Safety & BIS Scheme-I.",
        "committee": "FAD 14 (Drinks and Drinking Water)",
        "normative_references": [],
        "test_standards": ["IS 14543"],
        "keywords": ["packaged drinking water", "mineral water", "bottled water", "ro water", "microbiological limits", "water jar", "isi mark water"],
        "historical_revisions": ["IS 14543:1998", "IS 14543:2004"]
    },
    {
        "is_number": "IS 13428",
        "title": "Packaged Natural Mineral Water - Specification",
        "year": 2005,
        "amendments": [1, 2, 3, 4],
        "status": "ACTIVE",
        "scope": "Prescribes requirements for natural mineral water obtained directly from natural or drilled sources from underground water-bearing strata.",
        "committee": "FAD 14 (Drinks and Drinking Water)",
        "normative_references": [],
        "test_standards": ["IS 13428"],
        "keywords": ["natural mineral water", "spring water", "bottled natural water", "packaged water"],
        "historical_revisions": ["IS 13428:1992", "IS 13428:1998"]
    },

    # --- TEXTILES & GEOTEXTILES ---
    {
        "is_number": "IS 15748",
        "title": "Protective Clothing - Garments to Protect Against Heat and Flame",
        "year": 2007,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Specifies performance requirements for garments made from flexible materials designed to protect the user's body against heat and flame. Mandatory under Ministry of Textiles QCO.",
        "committee": "TXD 32 (Specialty Fabrics and Protective Clothing)",
        "normative_references": [],
        "test_standards": ["IS 15748"],
        "keywords": ["fire retardant clothing", "flame resistant suit", "protective garments", "heat protection", "boiler suit", "textiles qco"],
        "historical_revisions": []
    },
    {
        "is_number": "IS 16391",
        "title": "Geotextiles - Polypropylene Needle Punched Nonwoven Geotextiles - Specification",
        "year": 2015,
        "amendments": [],
        "status": "ACTIVE",
        "scope": "Specifies requirements for polypropylene needle punched nonwoven geotextiles used for filtration, separation, and drainage in road construction and slope stabilization. Mandatory under Ministry of Textiles QCO.",
        "committee": "TXD 30 (Geosynthetics)",
        "normative_references": [],
        "test_standards": ["IS 16391"],
        "keywords": ["geotextiles", "nonwoven geotextile", "polypropylene geotextile", "road drainage", "subgrade stabilization", "textiles qco"],
        "historical_revisions": []
    },

    # --- PRECIOUS METALS & HALLMARKING ---
    {
        "is_number": "IS 1417",
        "title": "Gold and Gold Alloys, Jewellery/Artefacts - Fineness and Marking - Specification",
        "year": 2016,
        "amendments": [1],
        "status": "ACTIVE",
        "scope": "Prescribes fineness grades (14K, 18K, 20K, 22K, 23K, 24K) and mandatory hallmarking system (BIS logo, purity, assaying centre mark, HUID) for gold jewellery in India.",
        "committee": "MTD 10 (Precious Metals)",
        "normative_references": [],
        "test_standards": ["IS 1418"],
        "keywords": ["gold hallmarking", "huid", "22k gold", "18k gold", "gold fineness", "jewellery marking", "hallmarking mandate"],
        "historical_revisions": ["IS 1417:1971", "IS 1417:1981", "IS 1417:1999"]
    }
]

QCOS = [
    {
        "order_name": "Steel and Steel Products (Quality Control) Order, 2024",
        "ministry": "Ministry of Steel",
        "gazette_no": "S.O. 2240(E)",
        "effective_date": "2024-06-01",
        "mandatory_scheme": "Scheme-I",
        "applicable_standards": ["IS 2062", "IS 1786", "IS 808", "IS 1852", "IS 8910"],
        "penal_clause": "Mandatory conformity to Indian Standards with BIS Standard Mark (ISI Mark). Under Section 16 & 17 of BIS Act 2016, manufacturing, storing, or selling without valid BIS license attracts penalty and imprisonment.",
        "scope_summary": "Covers all structural steel, TMT rebars, carbon steel plates, sections, wire rods, and input raw materials used for manufacturing covered steel products."
    },
    {
        "order_name": "Electronics and Information Technology Goods (Requirement for Compulsory Registration) Order, 2021",
        "ministry": "Ministry of Electronics and Information Technology (MeitY)",
        "gazette_no": "S.O. 1230(E)",
        "effective_date": "2021-10-01",
        "mandatory_scheme": "Scheme-II (CRS)",
        "applicable_standards": [
            "IS 13252 (Part 1)", "IS 16046 (Part 1)", "IS 16046 (Part 2)",
            "IS 616", "IS 302-2-25", "IS 15885 (Part 2/Sec 13)",
            "IS 16102 (Part 1)"
        ],
        "penal_clause": "Goods must be registered under BIS Compulsory Registration Scheme (CRS) and bear the Standard Mark with registration number before import, distribution, or sale.",
        "scope_summary": "Laptops, tablets, visual display units, power adapters, secondary Li-ion cells, microwave ovens, LED drivers, and smart consumer electronics."
    },
    {
        "order_name": "Solar Photovoltaics, Systems, Devices and Components Goods (Requirement for Compulsory Registration) Order, 2017",
        "ministry": "Ministry of New and Renewable Energy (MNRE)",
        "gazette_no": "S.O. 2920(E)",
        "effective_date": "2018-04-16",
        "mandatory_scheme": "Scheme-II (CRS)",
        "applicable_standards": ["IS 14286", "IS/IEC 61730 (Part 1)", "IS 16221 (Part 2)"],
        "penal_clause": "Mandatory registration with BIS under CRS. Non-registered solar modules and inverters are barred from public tenders and import clearance.",
        "scope_summary": "Crystalline silicon terrestrial PV modules, thin-film modules, and grid-connected PV inverters."
    },
    {
        "order_name": "Safety of Toys (Quality Control) Order, 2020",
        "ministry": "Department for Promotion of Industry and Internal Trade (DPIIT)",
        "gazette_no": "S.O. 850(E)",
        "effective_date": "2021-01-01",
        "mandatory_scheme": "Scheme-I",
        "applicable_standards": ["IS 9873 (Part 1)", "IS 15644"],
        "penal_clause": "Toys cannot be manufactured, imported, distributed, or sold without bearing the BIS ISI Mark under Scheme-I.",
        "scope_summary": "All electric and non-electric toys intended for use by children under 14 years of age."
    },
    {
        "order_name": "Footwear made from Leather and other materials (Quality Control) Order, 2020",
        "ministry": "Department for Promotion of Industry and Internal Trade (DPIIT)",
        "gazette_no": "S.O. 3840(E)",
        "effective_date": "2023-07-01",
        "mandatory_scheme": "Scheme-I",
        "applicable_standards": ["IS 15298 (Part 2)"],
        "penal_clause": "Mandatory BIS certification (ISI Mark) for all industrial safety footwear.",
        "scope_summary": "Industrial safety shoes, protective boots, and leather footwear."
    },
    {
        "order_name": "Plywood and Wooden Flush Door Shutters (Quality Control) Order, 2024",
        "ministry": "Department for Promotion of Industry and Internal Trade (DPIIT)",
        "gazette_no": "S.O. 1102(E)",
        "effective_date": "2024-08-28",
        "mandatory_scheme": "Scheme-I",
        "applicable_standards": ["IS 303", "IS 710"],
        "penal_clause": "Mandatory ISI marking under Scheme-I for all commercial and marine plywood.",
        "scope_summary": "General-purpose plywood (MR/BWR) and marine plywood (BWP)."
    },
    {
        "order_name": "Plugs and Socket-Outlets (Quality Control) Order, 2021",
        "ministry": "Department for Promotion of Industry and Internal Trade (DPIIT)",
        "gazette_no": "S.O. 4519(E)",
        "effective_date": "2022-06-01",
        "mandatory_scheme": "Scheme-I",
        "applicable_standards": ["IS 1293"],
        "penal_clause": "Domestic plugs and socket-outlets must bear the ISI mark under Scheme-I.",
        "scope_summary": "Plugs and socket-outlets up to 250V and 16A."
    },
    {
        "order_name": "Polyethylene Material for Moulding and Extrusion (Quality Control) Order, 2022",
        "ministry": "Ministry of Chemicals and Petrochemicals",
        "gazette_no": "S.O. 724(E)",
        "effective_date": "2022-04-03",
        "mandatory_scheme": "Scheme-I",
        "applicable_standards": ["IS 7328", "IS 4984", "IS 4985"],
        "penal_clause": "Polyethylene moulding raw materials and plastic pipes must strictly conform to BIS specifications.",
        "scope_summary": "HDPE pipe materials, virgin polymers, and water piping systems."
    },
    {
        "order_name": "Caustic Soda (Quality Control) Order, 2018",
        "ministry": "Ministry of Chemicals and Petrochemicals",
        "gazette_no": "S.O. 1481(E)",
        "effective_date": "2018-12-18",
        "mandatory_scheme": "Scheme-I",
        "applicable_standards": ["IS 252"],
        "penal_clause": "Caustic soda manufactured or imported must carry the BIS standard mark.",
        "scope_summary": "Solid, flaked, and lye sodium hydroxide for industrial applications."
    },
    {
        "order_name": "Electric Transformers (Quality Control) Order, 2023",
        "ministry": "Ministry of Heavy Industries",
        "gazette_no": "S.O. 521(E)",
        "effective_date": "2023-11-01",
        "mandatory_scheme": "Scheme-I",
        "applicable_standards": ["IS 1180 (Part 1)"],
        "penal_clause": "Mandatory ISI mark and BEE energy performance compliance under Scheme-I.",
        "scope_summary": "Outdoor oil-immersed distribution transformers up to 2500 kVA, 33 kV."
    },
    {
        "order_name": "Wires and Cables (Quality Control) Order, 2023",
        "ministry": "Ministry of Heavy Industries",
        "gazette_no": "S.O. 1892(E)",
        "effective_date": "2024-03-01",
        "mandatory_scheme": "Scheme-I",
        "applicable_standards": ["IS 694", "IS 1554 (Part 1)", "IS 7098 (Part 1)"],
        "penal_clause": "Manufacture, import, or distribution without BIS ISI certification is punishable under law.",
        "scope_summary": "PVC insulated flexible cords, power cables up to 1.1 kV, and XLPE cables."
    },
    {
        "order_name": "Helmets for riders of Two Wheeler Motor Vehicles (Quality Control) Order, 2020",
        "ministry": "Ministry of Road Transport and Highways",
        "gazette_no": "S.O. 4252(E)",
        "effective_date": "2021-06-01",
        "mandatory_scheme": "Scheme-I",
        "applicable_standards": ["IS 4151"],
        "penal_clause": "Sale or manufacture of non-ISI marked two-wheeler helmets is illegal across India.",
        "scope_summary": "Protective helmets for motorcycle and two-wheeler riders."
    },
    {
        "order_name": "Packaged Water (Quality Control) Mandate",
        "ministry": "Ministry of Consumer Affairs, Food and Public Distribution",
        "gazette_no": "S.O. 982(E)",
        "effective_date": "2001-03-29",
        "mandatory_scheme": "Scheme-I",
        "applicable_standards": ["IS 14543", "IS 13428"],
        "penal_clause": "Packaged drinking water cannot be bottled or sold without a valid BIS license (ISI Mark).",
        "scope_summary": "Packaged drinking water and natural mineral water in sealed bottles and containers."
    }
]

def build_graph_edges():
    edges = []
    
    # 1. Normative references between standards
    normative_pairs = [
        ("IS 2062", "IS 808", "NORMATIVE_REF", "Structural dimensions specified in IS 808"),
        ("IS 2062", "IS 1852", "NORMATIVE_REF", "Rolling tolerances specified in IS 1852"),
        ("IS 2062", "IS 8910", "NORMATIVE_REF", "Technical delivery conditions specified in IS 8910"),
        ("IS 2062", "IS 228 (Part 1)", "NORMATIVE_REF", "Chemical composition testing per IS 228"),
        ("IS 1786", "IS 228 (Part 1)", "NORMATIVE_REF", "Chemical analysis per IS 228"),
        ("IS 1786", "IS 2062", "NORMATIVE_REF", "Complementary structural steel provisions"),
        ("IS 456", "IS 1786", "NORMATIVE_REF", "Reinforcement steel bars mandated by IS 456"),
        ("IS 456", "IS 269", "NORMATIVE_REF", "OPC cement provisions"),
        ("IS 456", "IS 383", "NORMATIVE_REF", "Aggregate specifications for concrete"),
        ("IS 456", "IS 1489 (Part 1)", "NORMATIVE_REF", "Pozzolana cement specifications"),
        ("IS 800", "IS 2062", "NORMATIVE_REF", "Structural steel grades mandated by IS 800"),
        ("IS 800", "IS 808", "NORMATIVE_REF", "Section dimensions mandated by IS 800"),
        ("IS 10262", "IS 456", "NORMATIVE_REF", "Mix design compliance with IS 456"),
        ("IS 10262", "IS 383", "NORMATIVE_REF", "Aggregate grading criteria for mix design"),
        ("IS 13920", "IS 456", "NORMATIVE_REF", "Base concrete code of practice"),
        ("IS 13920", "IS 1786", "NORMATIVE_REF", "Ductile reinforcement steel bar provisions"),
        ("IS 13920", "IS 1893 (Part 1)", "NORMATIVE_REF", "Seismic loading parameters"),
        ("IS 4984", "IS 7328", "NORMATIVE_REF", "Raw material granules per IS 7328"),
        ("IS 13252 (Part 1)", "IS 616", "NORMATIVE_REF", "Audio/video safety harmonized references"),
        ("IS 13252 (Part 1)", "IS 1293", "NORMATIVE_REF", "Power plug and cord safety conformity"),
        ("IS 14286", "IS/IEC 61730 (Part 1)", "NORMATIVE_REF", "PV module construction safety qualification")
    ]
    for src, tgt, rel, desc in normative_pairs:
        edges.append({
            "source": src,
            "source_type": "Standard",
            "target": tgt,
            "target_type": "Standard",
            "relation": rel,
            "description": desc
        })

    # 2. Test standards
    test_pairs = [
        ("IS 2062", "IS 1608 (Part 1)", "TESTED_BY", "Tensile testing at room temperature"),
        ("IS 2062", "IS 1599", "TESTED_BY", "Bend testing for ductility"),
        ("IS 2062", "IS 1757 (Part 1)", "TESTED_BY", "Charpy impact testing for notch toughness"),
        ("IS 1786", "IS 1608 (Part 1)", "TESTED_BY", "Proof stress and elongation tensile testing"),
        ("IS 1786", "IS 1599", "TESTED_BY", "Bend and rebend testing"),
        ("IS 456", "IS 516 (Part 1/Sec 1)", "TESTED_BY", "Compressive and flexural strength of concrete"),
        ("IS 456", "IS 1199 (Part 1)", "TESTED_BY", "Sampling and workability slump testing"),
        ("IS 383", "IS 2386 (Part 1)", "TESTED_BY", "Particle size sieve analysis"),
        ("IS 269", "IS 4031 (Part 5)", "TESTED_BY", "Initial and final setting times"),
        ("IS 1077", "IS 3495 (Part 1)", "TESTED_BY", "Compressive strength of burnt clay bricks"),
        ("IS 694", "IS 10810 (Part 43)", "TESTED_BY", "Insulation resistance testing of cables"),
        ("IS 4984", "IS 12235 (Part 1)", "TESTED_BY", "Dimensional measurement and wall thickness"),
        ("IS 4984", "IS 12235 (Part 2)", "TESTED_BY", "Density determination of polyethylene"),
        ("IS 15298 (Part 2)", "IS 15298 (Part 2)", "TESTED_BY", "Toe cap 200J impact and 15kN compression tests")
    ]
    for src, tgt, rel, desc in test_pairs:
        edges.append({
            "source": src,
            "source_type": "Standard",
            "target": tgt,
            "target_type": "TestStandard",
            "relation": rel,
            "description": desc
        })

    # 3. Supersedes relations
    supersedes_pairs = [
        ("IS 1786", "IS 432 (Part 1)", "SUPERSEDES", "Supersedes mild steel plain bars for high-strength rebar"),
        ("IS 2062", "IS 432 (Part 1)", "SUPERSEDES", "Supersedes general structural use of plain mild steel"),
        ("IS 1608 (Part 1)", "IS 1608:2005", "SUPERSEDES", "Adopts ISO 6892-1 ambient tensile test methods")
    ]
    for src, tgt, rel, desc in supersedes_pairs:
        edges.append({
            "source": src,
            "source_type": "Standard",
            "target": tgt,
            "target_type": "Standard",
            "relation": rel,
            "description": desc
        })

    # 4. QCO Mandates
    for qco in QCOS:
        # Standard - MANDATED_BY -> QCO
        for std in qco["applicable_standards"]:
            edges.append({
                "source": std,
                "source_type": "Standard",
                "target": qco["order_name"],
                "target_type": "QCO",
                "relation": "MANDATED_BY",
                "description": f"Covered under {qco['order_name']} ({qco['mandatory_scheme']})"
            })
        # QCO - ISSUED_BY -> Ministry
        edges.append({
            "source": qco["order_name"],
            "source_type": "QCO",
            "target": qco["ministry"],
            "target_type": "Ministry",
            "relation": "ISSUED_BY",
            "description": f"Enacted by {qco['ministry']}"
        })
        # QCO - REQUIRES_SCHEME -> Scheme
        edges.append({
            "source": qco["order_name"],
            "source_type": "QCO",
            "target": qco["mandatory_scheme"],
            "target_type": "Scheme",
            "relation": "REQUIRES_SCHEME",
            "description": f"Mandates compliance under {qco['mandatory_scheme']}"
        })

    return edges

TENDER_SAMPLES = [
    {
        "tender_id": "GEM/2026/B/890123",
        "title": "Procurement of High Strength Deformed Steel Bars for Flyover Bridge Foundation",
        "department": "National Highways Authority of India (NHAI)",
        "language": "en",
        "file_name": "nhai_bridge_rebar_spec.txt",
        "category": "Construction Materials",
        "raw_text": """TENDER SPECIFICATION: HIGH STRENGTH DEFORMED TMT BARS FOR SUB-STRUCTURE AND FOUNDATION
1. SCOPE: Supply of Thermo-Mechanically Treated (TMT) steel reinforcement bars for pier and pile cap foundation work.
2. TECHNICAL SPECIFICATIONS:
   - Grade: Fe 500D conforming strictly to IS 1786 (latest edition).
   - Nominal Diameters: 16mm, 20mm, 25mm, and 32mm.
   - Proof Stress (0.2%): Minimum 500.0 N/mm2.
   - Tensile Strength (TS): Minimum 565.0 N/mm2; TS/YS ratio not less than 1.10.
   - Total Elongation at maximum force: Minimum 5.0%.
   - Chemical Composition: Carbon <= 0.25%, Sulphur <= 0.040%, Phosphorus <= 0.040%, (S+P) <= 0.075%.
3. QUALITY ASSURANCE & MANDATORY CERTIFICATION:
   - Manufacturer must hold a valid BIS License for marking with the Standard Mark (ISI Mark) under Scheme-I in accordance with the Steel and Steel Products (Quality Control) Order.
   - Routine testing must include tensile test per IS 1608 (Part 1) and bend/rebend test per IS 1599 from NABL accredited lab.
   - Every consignment must be accompanied by Manufacturer Test Certificate (MTC) with heat numbers matching physical bar embossings.""",
        "expected_findings": {
            "standards_referenced": ["IS 1786", "IS 1608 (Part 1)", "IS 1599"],
            "qco_compliant": True,
            "deprecated_standards": [],
            "compliance_score": 98
        }
    },
    {
        "tender_id": "GEM/2026/B/543210",
        "title": "Supply of Structural Steel Beams and Plates for Workshop Fabrication (Trap: Deprecated Standard & Missing QCO)",
        "department": "Central Public Works Department (CPWD)",
        "language": "en",
        "file_name": "cpwd_structural_steel_trap_spec.txt",
        "category": "Civil & Structural",
        "raw_text": """NOTICE INVITING TENDER FOR FABRICATION STEEL
Tenderers are invited to supply hot rolled steel plates and rolled joists for industrial shed roof trusses.
SPECIFICATIONS:
1. Steel sections shall conform to IS 2062:2006 Grade A.
2. Mild steel round tie bars shall conform to IS 432 (Part 1) - 1982.
3. Beams shall be ISMB 300 and ISMB 400.
4. Material can be supplied from secondary re-rollers without BIS certification provided mill test certificates are furnished.
5. Invoicing must be on actual weighbridge weight.""",
        "expected_findings": {
            "standards_referenced": ["IS 2062:2006", "IS 432 (Part 1)"],
            "qco_compliant": False,
            "deprecated_standards": ["IS 2062:2006 (superseded by 2011)", "IS 432 (Part 1) (superseded by IS 1786/IS 2062)"],
            "omissions": ["Missing mandatory BIS ISI Mark requirement under Steel QCO 2024", "Missing Charpy impact test method IS 1757", "Missing tensile testing standard IS 1608"],
            "compliance_score": 38
        }
    },
    {
        "tender_id": "GEM/2026/B/112233",
        "title": "Procurement of Commercial Laptops and Mobile Workstations",
        "department": "Ministry of Electronics & Information Technology",
        "language": "en",
        "file_name": "meity_it_hardware_laptops.txt",
        "category": "IT Equipment",
        "raw_text": """TECHNICAL SPECIFICATION FOR COMMERCIAL LAPTOPS (QTY: 500 UNITS)
Processor: Intel Core i7 13th Gen or AMD Ryzen 7 PRO series.
RAM: 16 GB DDR5 4800MHz expandable to 64 GB.
Storage: 512 GB PCIe NVMe M.2 SSD.
Display: 14.0 inch Full HD IPS Anti-glare display.
MANDATORY STATUTORY COMPLIANCE:
1. All equipment must conform to IS 13252 (Part 1):2010 for Information Technology Equipment Safety.
2. Secondary Lithium-ion battery packs must be certified to IS 16046 (Part 2):2018.
3. Power adapter must comply with IS 13252 (Part 1) and possess 3-pin plug conforming to IS 1293.
4. Bidders must upload valid BIS Compulsory Registration Scheme (CRS) R-number for both Laptop and Battery pack at the time of bid submission.""",
        "expected_findings": {
            "standards_referenced": ["IS 13252 (Part 1)", "IS 16046 (Part 2)", "IS 1293"],
            "qco_compliant": True,
            "deprecated_standards": [],
            "compliance_score": 100
        }
    },
    {
        "tender_id": "GEM/2026/B/998877",
        "title": "Tender for Design Mix Concrete M30 for Multi-Storey Residential Complex",
        "department": "Delhi Development Authority (DDA)",
        "language": "en",
        "file_name": "dda_rmc_concrete_spec.txt",
        "category": "Civil Construction",
        "raw_text": """TENDER SPECIFICATION: READY MIX CONCRETE (RMC) M-30 GRADE
1. Concrete shall be designed in accordance with IS 10262:2019 and IS 456:2000.
2. Cement used shall be Ordinary Portland Cement 43 Grade conforming to IS 269:2015.
3. Coarse and fine aggregates shall strictly adhere to IS 383:2016 (Zone-II for sand).
4. Concrete workability shall be tested at batching plant and site per IS 1199 (Part 1).
5. Compressive strength shall be determined from 150mm cubes tested at 7 days and 28 days in accordance with IS 516 (Part 1/Sec 1).
6. Ductile detailing of all beams and columns shall follow IS 13920:2016 for Seismic Zone IV.""",
        "expected_findings": {
            "standards_referenced": ["IS 10262", "IS 456", "IS 269", "IS 383", "IS 1199 (Part 1)", "IS 516 (Part 1/Sec 1)", "IS 13920"],
            "qco_compliant": True,
            "deprecated_standards": [],
            "compliance_score": 97
        }
    },
    {
        "tender_id": "GEM/2026/B/334455",
        "title": "Supply and Laying of HDPE Potable Water Pipes (Trap: Raw Material Unspecified)",
        "department": "Public Health Engineering Department (PHED), Rajasthan",
        "language": "en",
        "file_name": "phed_water_hdpe_pipe_trap.txt",
        "category": "Piping & Water Supply",
        "raw_text": """TENDER FOR HDPE PIPES UNDER JAL JEEVAN MISSION
1. Supply of 110mm and 160mm OD HDPE Pipes rating PN-10.
2. Pipes shall comply with IS 4984.
3. Re-granulated recycled plastic may be blended up to 30% to reduce project costs.
4. Hydrostatic pressure test must be performed by the contractor.""",
        "expected_findings": {
            "standards_referenced": ["IS 4984"],
            "qco_compliant": False,
            "deprecated_standards": [],
            "omissions": [
                "Violates IS 4984 clause prohibiting recycled polymer blending for drinking water",
                "Missing mandatory virgin raw material standard IS 7328",
                "Missing DPIIT/Chemicals QCO mandatory ISI license requirement",
                "Missing test methods IS 12235 (Part 1 and 2)"
            ],
            "compliance_score": 42
        }
    },
    {
        "tender_id": "GEM/2026/B/776655",
        "title": "Procurement of 500kVA Distribution Transformers with Star Rating",
        "department": "Uttar Pradesh Power Corporation Limited (UPPCL)",
        "language": "en",
        "file_name": "uppcl_transformer_spec.txt",
        "category": "Electrical Power",
        "raw_text": """TECHNICAL SPECIFICATION FOR 500 kVA, 11/0.433 kV OUTDOOR DISTRIBUTION TRANSFORMERS
1. APPLICABLE STANDARDS: The transformer shall conform to IS 1180 (Part 1):2014 with Energy Efficiency Level-2.
2. Insulating oil shall conform to IS 335.
3. CERTIFICATION: The unit must bear the mandatory BIS Standard Mark (ISI Mark) under Scheme-I per the Electric Transformers (Quality Control) Order.
4. Transformer must also hold BEE 3-Star or higher energy conservation label.
5. Routine tests shall be witnessed by third-party inspection agency (RITES / CPRI).""",
        "expected_findings": {
            "standards_referenced": ["IS 1180 (Part 1)", "IS 335"],
            "qco_compliant": True,
            "deprecated_standards": [],
            "compliance_score": 96
        }
    },
    {
        "tender_id": "GEM/2026/B/889900",
        "title": "Industrial Safety Footwear for Thermal Power Station Personnel",
        "department": "NTPC Limited",
        "language": "en",
        "file_name": "ntpc_safety_shoes_spec.txt",
        "category": "PPE & Safety",
        "raw_text": """TENDER REQUIREMENT: SAFETY SHOES FOR PLANT OPERATORS
1. Footwear must provide steel toe protection against 200 Joules impact.
2. Must strictly comply with IS 15298 (Part 2):2016 for Safety Footwear.
3. Under DPIIT Footwear QCO, the product must carry an authentic BIS ISI Mark.
4. Soling material: Double density PU sole, oil and acid resistant, anti-static.""",
        "expected_findings": {
            "standards_referenced": ["IS 15298 (Part 2)"],
            "qco_compliant": True,
            "deprecated_standards": [],
            "compliance_score": 100
        }
    },
    {
        "tender_id": "GEM/2026/B/665544",
        "title": "Supply of Grid-Connected Solar Rooftop Photovoltaic Modules",
        "department": "Solar Energy Corporation of India (SECI)",
        "language": "en",
        "file_name": "seci_solar_pv_spec.txt",
        "category": "Renewable Energy",
        "raw_text": """SPECIFICATION FOR MONOCRYSTALLINE SOLAR PHOTOVOLTAIC MODULES
1. PV Modules must conform to IS 14286 (Design qualification and type approval).
2. Construction safety must conform to IS/IEC 61730 (Part 1) and Part 2.
3. Mandatory MNRE Order: All modules must be registered under BIS Compulsory Registration Scheme (CRS) and enlisted in the Approved List of Models and Manufacturers (ALMM).
4. Power output warranty: 90% at the end of 10 years, 80% at 25 years.""",
        "expected_findings": {
            "standards_referenced": ["IS 14286", "IS/IEC 61730 (Part 1)"],
            "qco_compliant": True,
            "deprecated_standards": [],
            "compliance_score": 98
        }
    },
    {
        "tender_id": "GEM/2026/B/221100",
        "title": "Multilingual Tender Spec: कंक्रीट निर्माण के लिए स्टील की छड़ें (Steel rods for concrete construction)",
        "department": "Madhya Pradesh Public Works Department (MP PWD)",
        "language": "hi",
        "file_name": "mp_pwd_hindi_tmt_spec.txt",
        "category": "Civil & Construction",
        "raw_text": """निविदा विशिष्टता: भवन निर्माण हेतु उच्च शक्ति टीएमटी स्टील की छड़ें (Fe 500D)
१. कार्य का विवरण: शासकीय महाविद्यालय भवन निर्माण हेतु कंक्रीट सुदृढीकरण के लिए स्टील छड़ों की आपूर्ति।
२. तकनीकी मानक: छड़ें अनिवार्य रूप से IS 1786 (नवीनतम संशोधन) के ग्रेड Fe 500D के अनुरूप होनी चाहिए।
३. अनिवार्य प्रमाणन: इस्पात मंत्रालय के गुणवत्ता नियंत्रण आदेश (QCO) के तहत निर्माता के पास वैध बीआईएस आईएसआई मार्क (BIS ISI Mark) लाइसेंस होना अनिवार्य है।
४. परीक्षण: प्रत्येक लॉट का तन्यता परीक्षण IS 1608 (Part 1) और मोड़ परीक्षण IS 1599 के अनुसार किया जाएगा।""",
        "expected_findings": {
            "standards_referenced": ["IS 1786", "IS 1608 (Part 1)", "IS 1599"],
            "language_detected": "hi",
            "qco_compliant": True,
            "deprecated_standards": [],
            "compliance_score": 100
        }
    },
    {
        "tender_id": "GEM/2026/B/445566",
        "title": "Low Smoke Zero Halogen (FRLS) Power Cables for Underground Metro Station",
        "department": "Delhi Metro Rail Corporation (DMRC)",
        "language": "en",
        "file_name": "dmrc_metro_cables_spec.txt",
        "category": "Electrical Cables",
        "raw_text": """TENDER SPECIFICATION: 1.1 kV XLPE INSULATED POWER CABLES
1. Cables shall conform to IS 7098 (Part 1):1988 with copper conductors complying with IS 8130.
2. Domestic wiring portions shall conform to IS 694:2010.
3. Testing for insulation resistance shall follow IS 10810 (Part 43).
4. All cables must bear the BIS ISI Mark under the Ministry of Heavy Industries Wires and Cables QCO.""",
        "expected_findings": {
            "standards_referenced": ["IS 7098 (Part 1)", "IS 694", "IS 10810 (Part 43)"],
            "qco_compliant": True,
            "deprecated_standards": [],
            "compliance_score": 97
        }
    },
    {
        "tender_id": "GEM/2026/B/771122",
        "title": "Procurement of Packaged Drinking Water Jars for Government Offices (Trap: Unlicensed Supplier Allowed)",
        "department": "General Administration Department, Secretariat",
        "language": "en",
        "file_name": "gad_packaged_water_trap_spec.txt",
        "category": "Food & Public Health",
        "raw_text": """TENDER NOTICE FOR 20-LITRE PACKAGED DRINKING WATER JARS
1. Daily supply of 200 jars of purified chilled drinking water.
2. Water should be clean and RO purified.
3. IS 14543 may be followed as a recommended guideline.
4. Local reverse osmosis water packaging plants without BIS registration may participate if local municipal health certificate is produced.""",
        "expected_findings": {
            "standards_referenced": ["IS 14543"],
            "qco_compliant": False,
            "omissions": [
                "Illegal under Ministry of Consumer Affairs Packaged Water Mandate (ISI mark is legally mandatory under Scheme-I)",
                "Municipal certificate cannot substitute BIS license",
                "Non-compliance with BIS Act Section 16"
            ],
            "compliance_score": 25
        }
    },
    {
        "tender_id": "GEM/2026/B/992211",
        "title": "Procurement of Marine Plywood for Coastal Naval Barracks",
        "department": "Military Engineer Services (MES)",
        "language": "en",
        "file_name": "mes_marine_plywood_spec.txt",
        "category": "Wood & Interiors",
        "raw_text": """SPECIFICATION FOR BWP GRADE MARINE PLYWOOD
1. Plywood shall be 19mm Boiling Water Proof (BWP) conforming to IS 710:2010.
2. Synthetic resin adhesive shall be unextended phenol formaldehyde.
3. Under DPIIT Plywood QCO 2024, every sheet must bear the BIS Standard Mark with CM/L license number.
4. Moisture content shall not exceed 10%.""",
        "expected_findings": {
            "standards_referenced": ["IS 710"],
            "qco_compliant": True,
            "deprecated_standards": [],
            "compliance_score": 98
        }
    },
    {
        "tender_id": "GEM/2026/B/331188",
        "title": "Procurement of Flame Retardant Protective Suits for Chemical Disaster Response",
        "department": "National Disaster Response Force (NDRF)",
        "language": "en",
        "file_name": "ndrf_flame_suit_spec.txt",
        "category": "Textiles & PPE",
        "raw_text": """TECHNICAL SPECIFICATION: HEAT AND FLAME PROTECTIVE APPAREL
1. Garments must comply with IS 15748:2007 (Protective clothing against heat and flame).
2. Fabric must exhibit limited flame spread, heat resistance, and tensile strength.
3. Mandatory Ministry of Textiles QCO compliance with valid BIS license certification.""",
        "expected_findings": {
            "standards_referenced": ["IS 15748"],
            "qco_compliant": True,
            "deprecated_standards": [],
            "compliance_score": 96
        }
    },
    {
        "tender_id": "GEM/2026/B/554433",
        "title": "Procurement of Electric Motors and Switchgear (Trap: Outdated IEC / IS Standard)",
        "department": "Irrigation & Water Resources Department, Haryana",
        "language": "en",
        "file_name": "irrigation_switchgear_trap_spec.txt",
        "category": "Electrical Machinery",
        "raw_text": """TENDER FOR L.T. AIR CIRCUIT BREAKERS AND PLUGS
1. Power cords with plugs must conform to old IS 1293:1988 standard.
2. Plugs may have unsheathed live pins.
3. Breakers shall conform to IS 13947 (superseded standard).
4. No BIS certification certificate is required if foreign CE certificate is attached.""",
        "expected_findings": {
            "standards_referenced": ["IS 1293:1988", "IS 13947"],
            "qco_compliant": False,
            "deprecated_standards": [
                "IS 1293:1988 is superseded by IS 1293:2019",
                "IS 13947 is superseded by IS/IEC 60947"
            ],
            "omissions": [
                "Violates DPIIT Plugs & Sockets QCO 2021",
                "CE certificate is legally invalid in place of BIS ISI mark in India",
                "Unsheathed pins pose serious electrical shock hazard"
            ],
            "compliance_score": 20
        }
    },
    {
        "tender_id": "GEM/2026/B/884422",
        "title": "Procurement of Industrial Safety Helmets for Municipal Drainage Workers",
        "department": "Brihanmumbai Municipal Corporation (BMC)",
        "language": "en",
        "file_name": "bmc_safety_helmet_spec.txt",
        "category": "PPE & Safety",
        "raw_text": """SPECIFICATION FOR INDUSTRIAL SAFETY HELMETS (QTY: 2,500 NOS)
1. Helmets shall be Type-1 industrial safety helmets conforming to IS 2925:1984.
2. Shell material: High Density Polyethylene (HDPE) with UV stabilizer.
3. Must carry BIS ISI Mark embossed on the peak.
4. Shock absorption test shall be certified by NABL/BIS test house.""",
        "expected_findings": {
            "standards_referenced": ["IS 2925"],
            "qco_compliant": True,
            "deprecated_standards": [],
            "compliance_score": 95
        }
    }
]

def main():
    os.makedirs("data/gem_tender_samples", exist_ok=True)
    
    # 1. Save standards_catalog.json
    with open("data/standards_catalog.json", "w", encoding="utf-8") as f:
        json.dump(STANDARDS, f, indent=2, ensure_ascii=False)
    print(f"[1/4] Saved {len(STANDARDS)} standards to data/standards_catalog.json")

    # 2. Save qco_registry.json
    with open("data/qco_registry.json", "w", encoding="utf-8") as f:
        json.dump(QCOS, f, indent=2, ensure_ascii=False)
    print(f"[2/4] Saved {len(QCOS)} QCO orders to data/qco_registry.json")

    # 3. Save normative_graph_edges.csv
    edges = build_graph_edges()
    with open("data/normative_graph_edges.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "source_type", "target", "target_type", "relation", "description"])
        writer.writeheader()
        writer.writerows(edges)
    print(f"[3/4] Saved {len(edges)} graph edges to data/normative_graph_edges.csv")

    # 4. Save GeM tender samples
    for t in TENDER_SAMPLES:
        file_path = os.path.join("data/gem_tender_samples", t["file_name"])
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(t["raw_text"].strip())
    
    with open("data/gem_tender_samples/manifest.json", "w", encoding="utf-8") as f:
        json.dump(TENDER_SAMPLES, f, indent=2, ensure_ascii=False)
    print(f"[4/4] Saved {len(TENDER_SAMPLES)} tender samples and manifest to data/gem_tender_samples/")

if __name__ == "__main__":
    main()
