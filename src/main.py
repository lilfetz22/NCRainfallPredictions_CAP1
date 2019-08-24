#!/usr/bin/python

# Main program
def main():
	print("[MAIN] Calling Data_Wrangling_CAP1...")
	import Data_Wrangling_CAP1
	print("[MAIN] Calling Exogenous_Variables...")
	# import 'Exogenous_Variables'
	import importlib  
	importlib.import_module("Exogenous_Variables-Copy1")	#because of hyphen

main()
