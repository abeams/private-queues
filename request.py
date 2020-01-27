import numpy as np
import random

class Request:
	def __init__(self, process, turn=0, isDummy=False):
		self.process = process
		self.startTurn = turn
		self.insertionTurn = turn
		self.isDummy = isDummy
		
	def insert(self, turn):
		self.insertionTurn = turn
		self.subQueueWaitTime = self.insertionTurn - self.startTurn
		
	def accept(self, turn):
		self.finishTurn = turn
		self.waitTime = self.finishTurn - self.startTurn
		self.mainWaitTime = self.finishTurn - self.insertionTurn
		
class Process:
	def __init__(self, rate, isPrivate=False, dummyRate=0.0):
		self.rate = rate
		self.isPrivate = isPrivate
		self.dummyRate = dummyRate
		assert not isPrivate or dummyRate > rate
		self.subQueue = []
	
	def generateRequests(self, turn):
		n = np.random.poisson(self.rate)
		requests = []
		for i in range(n):
			requests.append(Request(self, turn, False))
		if not self.isPrivate:
			return requests
		self.subQueue.extend(requests)
		o = np.random.poisson(self.dummyRate)
		a = min(o, len(self.subQueue))
		requests = self.subQueue[:a]
		assert a == len(requests)
		self.subQueue = self.subQueue[a:]
		map(lambda p: p.insert(turn), requests)
		for i in range(a, o):
			requests.append(Request(self, turn, True))
		assert o == len(requests)
		return requests
		
class Stats:
	def __init__(self):
		self.QueueLength = [0.0, 0]
		self.AWait = [0.0, 0]
		self.AMainWait = [0.0, 0]
		self.ASubWait = [0.0, 0]
		self.ADummyWait = [0.0, 0]
		self.BWait = [0.0, 0]
		self.AInsertRate = [0.0, 0]
		self.AAllRate = [0.0, 0]
		

A = Process(.3, True, .4)
B = Process(.4)
#processes = [A]
processes = [A, B]

l = sum(map(lambda p: max(p.rate, p.dummyRate), processes))
u = 1
p = float(l)/u
uA = A.dummyRate
lA = A.rate

stats = Stats()

out = 1

queue = []

def updateAverage(stat, newValue):
	if(stat[1] == 0):
		stat[0] = newValue
		stat[1] = 1
		return
	stat[0] = ((float(stat[0]) * stat[1]) + newValue) / (stat[1] + 1.0)
	stat[1] += 1

for t in range(0, 20000000):
	updateAverage(stats.QueueLength, len(queue))
	
	if(len(queue)):
		accepted = queue[0]
		accepted.accept(t)
		if(accepted.process == A):
			updateAverage(stats.AAllRate, accepted.mainWaitTime)
			if(accepted.isDummy):
				updateAverage(stats.ADummyWait, accepted.waitTime)
			else:
				updateAverage(stats.AWait, accepted.waitTime)
				updateAverage(stats.AMainWait, accepted.mainWaitTime)
				updateAverage(stats.ASubWait, accepted.subQueueWaitTime)
		else:
			updateAverage(stats.BWait, accepted.waitTime)
		queue = queue[1:]
	
	toAdd = []
	for process in processes:
		toAdd.extend(process.generateRequests(t))
	updateAverage(stats.AInsertRate, len(filter(lambda r: r.process == A and not r.isDummy, toAdd)))
	queue.extend(toAdd)
	

#should be p + .5(p^2/1-p)	
expectedQueueLength = p + .5*(p**2/(1.0-p))
print("Expected main queue length: " + str(expectedQueueLength))
print(stats.QueueLength[0])


#should be 1/u + p/(2u(1-p)) + 1/(u-l) - 1/u
expectedWait = (1.0/u) + p/(2*u*(1.0 - p))
expectedAWait = 1.0/(uA - lA) - (1.0/uA)
print("Expected total A wait: " + str(expectedWait + expectedAWait))
print("Expected main A wait: " + str(expectedWait))
print("Expected sub A wait: " + str(expectedAWait))
print("A wait: " + str(stats.AWait))
print("A main wait: " + str(stats.AMainWait))
print("A sub wait: " + str(stats.ASubWait))

#should be 1/u + p/(2u(1-p))
print("Expected A dummy rate: " + str(expectedWait))
print("A dummy rate: " + str(stats.ADummyWait))

#should be 1/u + p/(2u(1-p))
print("Expected B wait: " + str(expectedWait))
print(stats.BWait[0], stats.BWait[1])

print("A all rate: " + str(stats.AAllRate))
print("A insert rate: " + str(stats.AInsertRate))

		

		
