exemptions={'Z':.0,'S/ME':5e4,'ME1/S1':75e3,'ME2/S2':1e5,'ME3/S3':125e3,'ME4/S4':15e4}
def fcmp(a,limit,tax,tax_over,tax_over_pct):A='%s + (%s-%s) * %s'%(tax,a,tax_over,tax_over_pct);return'IF(%s <= %0.2f, %s, %%s)'%(a,limit,A)
def tax_formula(a,tax_code='Z'):
	B=tax_code
	if B=='15P':return'0.15 * %s'%a
	elif B=='2P':return'0.02 * %s'%a
	elif B=='10P':return'0.1 * %s'%a
	A=[];A.append('IF(%s <= 0, 0.0, %%s)'%a);A.append('IF(%s <= 10000.0, %s * 0.05, %%s)'%(a,a));A.append(fcmp(a,3e4,5e2,1e4,.1));A.append(fcmp(a,7e4,25e2,3e4,.15));A.append(fcmp(a,14e4,85e2,7e4,.2));A.append(fcmp(a,25e4,225e2,14e4,.25));A.append(fcmp(a,5e5,5e4,25e4,.3));A.append('125000 + (%s-500000.0) * 0.32'%a);C='%s'
	for D in A:C=C%D
	return C
def compute_income_tax(amount,year='2022'):
	A=amount;B=int(year)
	if B>=2023:
		if not A:return .0
		elif A<=25e4:return .0
		elif A<=4e5:return(A-25e4)*.15
		elif A<=8e5:return 225e2+(A-4e5)*.2
		elif A<=2e6:return 1025e2+(A-8e5)*.25
		elif A<=8e6:return 4025e2+(A-2e6)*.3
		else:return 22025e2+(A-8e6)*.35
	elif not A:return .0
	elif A<=25e4:return .0
	elif A<=4e5:return(A-25e4)*.2
	elif A<=8e5:return 3e4+(A-4e5)*.25
	elif A<=2e6:return 13e4+(A-8e5)*.3
	elif A<=8e6:return 49e4+(A-2e6)*.32
	else:return 241e4+(A-8e6)*.35