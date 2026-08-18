EESchema Schematic File Version 4
LIBS:power
LIBS:device
LIBS:Timer
LIBS:Amplifier_Operational
LIBS:Connector_Generic
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
Sheet 1 1
Title "Classical Analog-Inspired Entanglement / Superposition Circuit"
Date "2026-08-18"
Rev "1.0"
Comp "Functional reconstruction from entanglement.pdf"
Comment1 "5 V signal path; values are an explicit behavioral abstraction"
Comment2 "Not a quantum processor or production-ready hardware design"
Comment3 "Input bus supports prioritized preemption in the companion simulator"
Comment4 "Open with KiCad 9 and save as .kicad_sch"
$EndDescr
Text Notes 650 650 0    100  ~ 20
5 V / 45 mA SUPPLY AND INPUT BUS
Text Notes 2800 650 0    100  ~ 20
ENTANGLEMENT UNIT: COUPLED OSCILLATORS
Text Notes 2800 3500 0    100  ~ 20
SUPERPOSITION UNIT: ANALOG AVERAGE
Text Notes 7000 3500 0    100  ~ 20
COLLAPSE UNIT: SAMPLE / THRESHOLD / DISPLAY
Text Notes 650 7350 0    65   ~ 12
The source PDF is an illustrative low-resolution drawing. This schematic preserves the visible signal blocks with explicit simulation values.

$Comp
L power:VCC #PWR01
U 1 1 1
P 850 850
F 0 "#PWR01" H 850 700 50  0001 C CNN
F 1 "VCC" H 865 1023 50  0000 C CNN
	1    850 850
	1    0    0    -1
$EndComp
$Comp
L power:GND #PWR02
U 1 1 2
P 850 2900
F 0 "#PWR02" H 850 2650 50  0001 C CNN
F 1 "GND" H 855 2727 50  0000 C CNN
	1    850 2900
	1    0    0    -1
$EndComp
$Comp
L Connector_Generic:Conn_01x10 J1
U 1 1 3
P 1350 1750
F 0 "J1" H 1430 1742 50  0000 L CNN
F 1 "INPUT_BUS" H 1430 1651 50  0000 L CNN
	1    1350 1750
	1    0    0    -1
$EndComp
Text Label 1550 1350 0    50   ~ 0
IN0
Text Label 1550 1450 0    50   ~ 0
IN1
Text Label 1550 1550 0    50   ~ 0
IN2
Text Label 1550 1650 0    50   ~ 0
IN3
Text Label 1550 1750 0    50   ~ 0
IN4
Text Label 1550 1850 0    50   ~ 0
IN5
Text Label 1550 1950 0    50   ~ 0
IN6
Text Label 1550 2050 0    50   ~ 0
IN7
Text Label 1550 2150 0    50   ~ 0
STROBE
Text Label 1550 2250 0    50   ~ 0
PREEMPT
Wire Wire Line
	1550 1350 1850 1350
Wire Wire Line
	1550 1450 1850 1450
Wire Wire Line
	1550 1550 1850 1550
Wire Wire Line
	1550 1650 1850 1650
Wire Wire Line
	1550 1750 1850 1750
Wire Wire Line
	1550 1850 1850 1850
Wire Wire Line
	1550 1950 1850 1950
Wire Wire Line
	1550 2050 1850 2050
Wire Wire Line
	1550 2150 1850 2150
Wire Wire Line
	1550 2250 1850 2250
Text Label 1850 1350 0    50   ~ 0
INPUT0
Text Label 1850 1450 0    50   ~ 0
INPUT1
Text Label 1850 1550 0    50   ~ 0
INPUT2
Text Label 1850 1650 0    50   ~ 0
INPUT3
Text Label 1850 1750 0    50   ~ 0
INPUT4
Text Label 1850 1850 0    50   ~ 0
INPUT5
Text Label 1850 1950 0    50   ~ 0
INPUT6
Text Label 1850 2050 0    50   ~ 0
INPUT7
Text Label 1850 2150 0    50   ~ 0
STROBE
Text Label 1850 2250 0    50   ~ 0
PREEMPT

$Comp
L Timer:NE555D U1
U 1 1 10
P 2400 1200
F 0 "U1" H 2400 1781 50  0000 C CNN
F 1 "NE555D / OSC_A" H 2400 1690 50  0000 C CNN
	1    2400 1200
	1    0    0    -1
$EndComp
$Comp
L Device:R R1
U 1 1 11
P 2050 2050
F 0 "R1" H 2120 2096 50  0000 L CNN
F 1 "1k" H 2120 2005 50  0000 L CNN
	1    2050 2050
	1    0    0    -1
$EndComp
$Comp
L Device:R R2
U 1 1 12
P 2400 2050
F 0 "R2" H 2470 2096 50  0000 L CNN
F 1 "10k" H 2470 2005 50  0000 L CNN
	1    2400 2050
	1    0    0    -1
$EndComp
$Comp
L Device:C C1
U 1 1 13
P 2750 2050
F 0 "C1" H 2865 2096 50  0000 L CNN
F 1 "10n" H 2865 2005 50  0000 L CNN
	1    2750 2050
	1    0    0    -1
$EndComp
Text Label 1950 950 2    50   ~ 0
OSC_A
Wire Wire Line
	1950 950 2050 950
Wire Wire Line
	2050 950 2050 1200
Wire Wire Line
	2050 1200 2000 1200
Wire Wire Line
	2050 1200 2050 1900
Wire Wire Line
	2050 1900 2050 1900
Wire Wire Line
	2050 2200 2050 2700
Wire Wire Line
	2400 2200 2400 2700
Wire Wire Line
	2750 2200 2750 2700
Wire Wire Line
	2050 2700 2750 2700
$Comp
L power:GND #PWR03
U 1 1 14
P 2400 2700
F 0 "#PWR03" H 2400 2450 50  0001 C CNN
F 1 "GND" H 2405 2527 50  0000 C CNN
	1    2400 2700
	1    0    0    -1
$EndComp
$Comp
L Device:Q_NMOS_DGS Q1
U 1 1 15
P 3200 1250
F 0 "Q1" H 3405 1296 50  0000 L CNN
F 1 "COUPLE_A" H 3405 1205 50  0000 L CNN
	1    3200 1250
	1    0    0    -1
$EndComp
$Comp
L Device:D D1
U 1 1 16
P 3700 1250
F 0 "D1" H 3700 1033 50  0000 C CNN
F 1 "1N4148" H 3700 1124 50  0000 C CNN
	1    3700 1250
	-1   0    0    1
$EndComp
Text Label 3850 1250 0    50   ~ 0
ENT_A
Wire Wire Line
	3400 1250 3550 1250
Wire Wire Line
	3850 1250 4300 1250

$Comp
L Timer:NE555D U2
U 1 1 20
P 2400 2450
F 0 "U2" H 2400 3031 50  0000 C CNN
F 1 "NE555D / OSC_B" H 2400 2940 50  0000 C CNN
	1    2400 2450
	1    0    0    -1
$EndComp
$Comp
L Device:R R3
U 1 1 21
P 3200 2450
F 0 "R3" V 2993 2450 50  0000 C CNN
F 1 "1k" V 3084 2450 50  0000 C CNN
	1    3200 2450
	0    1    1    0
$EndComp
$Comp
L Device:C C2
U 1 1 22
P 3500 2750
F 0 "C2" H 3615 2796 50  0000 L CNN
F 1 "10n" H 3615 2705 50  0000 L CNN
	1    3500 2750
	1    0    0    -1
$EndComp
$Comp
L Device:Q_NMOS_DGS Q2
U 1 1 23
P 4000 2450
F 0 "Q2" H 4205 2496 50  0000 L CNN
F 1 "COUPLE_B" H 4205 2405 50  0000 L CNN
	1    4000 2450
	1    0    0    -1
$EndComp
$Comp
L Device:D D2
U 1 1 24
P 4550 2450
F 0 "D2" H 4550 2233 50  0000 C CNN
F 1 "1N4148" H 4550 2324 50  0000 C CNN
	1    4550 2450
	-1   0    0    1
$EndComp
Text Label 4700 2450 0    50   ~ 0
ENT_B
Wire Wire Line
	3350 2450 3800 2450
Wire Wire Line
	4200 2450 4400 2450
Wire Wire Line
	4700 2450 5100 2450

$Comp
L Amplifier_Operational:LM358 U3
U 1 1 30
P 3600 4300
F 0 "U3" H 3600 4667 50  0000 C CNN
F 1 "LM358 / SUPERPOSITION" H 3600 4576 50  0000 C CNN
	1    3600 4300
	1    0    0    -1
$EndComp
$Comp
L Device:R R4
U 1 1 31
P 2850 4200
F 0 "R4" V 2643 4200 50  0000 C CNN
F 1 "10k" V 2734 4200 50  0000 C CNN
	1    2850 4200
	0    1    1    0
$EndComp
$Comp
L Device:R R5
U 1 1 32
P 2850 4400
F 0 "R5" V 2950 4400 50  0000 C CNN
F 1 "10k" V 3050 4400 50  0000 C CNN
	1    2850 4400
	0    1    1    0
$EndComp
$Comp
L Device:R R6
U 1 1 33
P 4100 4300
F 0 "R6" V 3893 4300 50  0000 C CNN
F 1 "10k" V 3984 4300 50  0000 C CNN
	1    4100 4300
	0    1    1    0
$EndComp
$Comp
L Device:C C3
U 1 1 34
P 4600 4650
F 0 "C3" H 4715 4696 50  0000 L CNN
F 1 "1n" H 4715 4605 50  0000 L CNN
	1    4600 4650
	1    0    0    -1
$EndComp
Text Label 2500 4200 2    50   ~ 0
ENT_A
Text Label 2500 4400 2    50   ~ 0
ENT_B
Text Label 4750 4300 0    50   ~ 0
SUPERPOSITION
Wire Wire Line
	2500 4200 2700 4200
Wire Wire Line
	2500 4400 2700 4400
Wire Wire Line
	3000 4200 3200 4200
Wire Wire Line
	3000 4400 3200 4400
Wire Wire Line
	3200 4300 3200 4400
Wire Wire Line
	3200 4300 3300 4300
Wire Wire Line
	3900 4300 3950 4300
Wire Wire Line
	4250 4300 4750 4300
Wire Wire Line
	4600 4300 4600 4500
$Comp
L power:GND #PWR04
U 1 1 35
P 4600 4900
F 0 "#PWR04" H 4600 4650 50  0001 C CNN
F 1 "GND" H 4605 4727 50  0000 C CNN
	1    4600 4900
	1    0    0    -1
$EndComp
Wire Wire Line
	4600 4800 4600 4900

$Comp
L Amplifier_Operational:LM358 U4
U 1 1 40
P 6000 4300
F 0 "U4" H 6000 4667 50  0000 C CNN
F 1 "LM358 / COLLAPSE" H 6000 4576 50  0000 C CNN
	1    6000 4300
	1    0    0    -1
$EndComp
$Comp
L Device:R R7
U 1 1 41
P 5400 4200
F 0 "R7" V 5193 4200 50  0000 C CNN
F 1 "1k" V 5284 4200 50  0000 C CNN
	1    5400 4200
	0    1    1    0
$EndComp
$Comp
L Device:C C4
U 1 1 42
P 5400 4700
F 0 "C4" H 5515 4746 50  0000 L CNN
F 1 "1u" H 5515 4655 50  0000 L CNN
	1    5400 4700
	1    0    0    -1
$EndComp
$Comp
L Device:R R8
U 1 1 43
P 6600 4300
F 0 "R8" V 6393 4300 50  0000 C CNN
F 1 "10k" V 6484 4300 50  0000 C CNN
	1    6600 4300
	0    1    1    0
$EndComp
Text Label 5000 4200 2    50   ~ 0
SUPERPOSITION
Text Label 6900 4300 0    50   ~ 0
COLLAPSE
Wire Wire Line
	5000 4200 5250 4200
Wire Wire Line
	5550 4200 5700 4200
Wire Wire Line
	5700 4200 5700 4300
Wire Wire Line
	5700 4300 5700 4400
Wire Wire Line
	5700 4400 5700 4700
Wire Wire Line
	5700 4300 5700 4300
Wire Wire Line
	6300 4300 6450 4300
Wire Wire Line
	6750 4300 7050 4300
Wire Wire Line
	5400 4350 5400 4550
$Comp
L power:GND #PWR05
U 1 1 44
P 5400 5000
F 0 "#PWR05" H 5400 4750 50  0001 C CNN
F 1 "GND" H 5405 4827 50  0000 C CNN
	1    5400 5000
	1    0    0    -1
$EndComp
Wire Wire Line
	5400 4850 5400 5000

$Comp
L Connector_Generic:Conn_01x08 J2
U 1 1 50
P 10000 4300
F 0 "J2" H 10080 4292 50  0000 L CNN
F 1 "LED_OUTPUT" H 10080 4201 50  0000 L CNN
	1    10000 4300
	1    0    0    -1
$EndComp
Text Label 9700 4000 2    50   ~ 0
LED0_COLLAPSED
Text Label 9700 4100 2    50   ~ 0
LED1_SUPERPOSED
Text Label 9700 4200 2    50   ~ 0
LED2_ENT_A
Text Label 9700 4300 2    50   ~ 0
LED3_ENT_B
Text Label 9700 4400 2    50   ~ 0
LED4_INPUT0
Text Label 9700 4500 2    50   ~ 0
LED5_INPUT1
Text Label 9700 4600 2    50   ~ 0
LED6_INPUT2
Text Label 9700 4700 2    50   ~ 0
LED7_INPUT3

$Comp
L Device:LED D3
U 1 1 53
P 7900 4000
F 0 "D3" H 7893 3745 50  0000 C CNN
F 1 "COLLAPSE" H 7893 3836 50  0000 C CNN
	1    7900 4000
	-1   0    0    1
$EndComp
$Comp
L Device:LED D4
U 1 1 54
P 7900 4300
F 0 "D4" H 7893 4045 50  0000 C CNN
F 1 "SUPERPOSITION" H 7893 4136 50  0000 C CNN
	1    7900 4300
	-1   0    0    1
$EndComp
$Comp
L Device:LED D5
U 1 1 55
P 7900 4600
F 0 "D5" H 7893 4345 50  0000 C CNN
F 1 "ENT_A" H 7893 4436 50  0000 C CNN
	1    7900 4600
	-1   0    0    1
$EndComp
$Comp
L Device:LED D6
U 1 1 56
P 7900 4900
F 0 "D6" H 7893 4645 50  0000 C CNN
F 1 "ENT_B" H 7893 4736 50  0000 C CNN
	1    7900 4900
	-1   0    0    1
$EndComp
$Comp
L Device:R R9
U 1 1 57
P 8400 4000
F 0 "R9" V 8193 4000 50  0000 C CNN
F 1 "1k" V 8284 4000 50  0000 C CNN
	1    8400 4000
	0    1    1    0
$EndComp
$Comp
L Device:R R10
U 1 1 58
P 8400 4300
F 0 "R10" V 8490 4300 50  0000 C CNN
F 1 "1k" V 8581 4300 50  0000 C CNN
	1    8400 4300
	0    1    1    0
$EndComp
$Comp
L Device:R R11
U 1 1 59
P 8400 4600
F 0 "R11" V 8193 4600 50  0000 C CNN
F 1 "1k" V 8284 4600 50  0000 C CNN
	1    8400 4600
	0    1    1    0
$EndComp
$Comp
L Device:R R12
U 1 1 60
P 8400 4900
F 0 "R12" V 8490 4900 50  0000 C CNN
F 1 "1k" V 8581 4900 50  0000 C CNN
	1    8400 4900
	0    1    1    0
$EndComp
Wire Wire Line
	7050 4300 7300 4300
Wire Wire Line
	7300 4300 7300 4000
Wire Wire Line
	7300 4000 7750 4000
Wire Wire Line
	7300 4300 7750 4300
Wire Wire Line
	7300 4300 7300 4600
Wire Wire Line
	7300 4600 7750 4600
Wire Wire Line
	7300 4600 7300 4900
Wire Wire Line
	7300 4900 7750 4900
Wire Wire Line
	8050 4000 8250 4000
Wire Wire Line
	8050 4300 8250 4300
Wire Wire Line
	8050 4600 8250 4600
Wire Wire Line
	8050 4900 8250 4900
Wire Wire Line
	8550 4000 9700 4000
Wire Wire Line
	8550 4300 9700 4100
Wire Wire Line
	8550 4600 9700 4200
Wire Wire Line
	8550 4900 9700 4300
Text Notes 7550 5550 0    60   ~ 12
LED0..LED7 are observation channels; the Python model exposes the same byte and analog features.
$EndSCHEMATC

