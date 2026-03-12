from __future__ import print_function
from.timepairs import TimePairs
cases=[[[TimePairs('6a','12p')],[TimePairs('1p','6p')]],[[TimePairs('6a','1p')],[TimePairs('1p','6p')]],[[TimePairs('6a','1p')],[TimePairs('10a','6p')]],[[TimePairs('6a','7p')],[TimePairs('10a','3p')]],[[TimePairs('10a','3p')],[TimePairs('7a','8p')]],[[TimePairs('10a','4p')],[TimePairs('5a','3p')]],[[TimePairs('11:30a','4p')],[TimePairs('5a','10a')]],[[TimePairs('5a','10a'),TimePairs('11a','2p'),TimePairs('2:30p','10p')],[TimePairs('4a','4:30a'),TimePairs('10:05a','11:30'),TimePairs('11p','11:30p')]],[[TimePairs('5a','10a'),TimePairs('11a','2p'),TimePairs('2:30p','10p')],[TimePairs('4a','4:30a'),TimePairs('5:30a','6:30a'),TimePairs('10:05a','11:30'),TimePairs('2p','3:00p'),TimePairs('9:30p','10:00p'),TimePairs('11p','11:30p')]]]
def test_add():
	print('TEST ADD');E=0
	for A in cases:
		B=TimePairs()
		for D in A[0]:B+=D
		C=TimePairs()
		for D in A[1]:C+=D
		E+=1;print();print('----------------------------------------------');print(('CASE',E));print('A:',B);print('B:',C);B.debug=True;C.debug=True;A=B+C;print();print('C:',A)
def test_sub():
	print('TEST SUB');E=0
	for C in cases:
		A=TimePairs()
		for D in C[0]:A+=D
		B=TimePairs()
		for D in C[1]:B+=D
		E+=1;print();print('----------------------------------------------');print('CASE',E);print('A:',A);print('B:',B);A.debug=True;B.debug=True;C=A-B;print();print('A:',A);print('B:',B);print('C:',C)
def test_and():
	print('TEST AND');E=0
	for C in cases:
		A=TimePairs()
		for D in C[0]:A+=D
		B=TimePairs()
		for D in C[1]:B+=D
		E+=1;print();print('----------------------------------------------');print('CASE',E);print('A:',A);print('B:',B);A.debug=True;B.debug=True;C=A&B;print();print('A:',A);print('B:',B);print('C:',C)
if __name__=='__main__':test_add();test_sub();test_and();print(tp)