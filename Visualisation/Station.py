import datetime


class Station:
    def __init__(self, stop_id, stop_name, stop_desc, stop_lat, stop_lon):
        self.id = stop_id
        self.name = stop_name
        self.desc = stop_desc
        self.lat = stop_lat
        self.lon = stop_lon
        self.connectedTo = {}
        self.connectedGroup = {}
        self.duration = float("inf")
        self.predStop = None
        self.currentTime = None
        self.currentDate = None
        self.currentMetro = None

    def add_trip(self, route_id, valid_dates, time, nbr_stop_id, time_weight):
        """
        Add adjacent subway stations
        :param route_id: Each subway has two trip ids, corresponding to the go and return
        :param valid_dates:  datetime.date
        :param time:  datetime.time
        :param nbr_stop_id: adjacent station
        :param time_weight:  time interval which is timedelta
        :return: connectedTo
        """
        if nbr_stop_id in self.connectedGroup:
            if route_id == "transfer":
                return

            if [route_id, valid_dates, time_weight] in self.connectedGroup[nbr_stop_id]:
                idx = self.connectedGroup[nbr_stop_id].index([route_id, valid_dates, time_weight])
                self.connectedTo[(nbr_stop_id, idx)][2].append(time)
            else:
                self.connectedGroup[nbr_stop_id].append([route_id, valid_dates, time_weight])
                numGroupe = len(self.connectedGroup[nbr_stop_id])
                self.connectedTo[(nbr_stop_id, numGroupe-1)] = [route_id, valid_dates, [time, ], time_weight]
        else:
            self.connectedTo[(nbr_stop_id, 0)] = [route_id, valid_dates, [time, ], time_weight]
            self.connectedGroup[nbr_stop_id] = [[route_id, valid_dates, time_weight], ]

    def __str__(self):
        return str(self.id) + "connectedTo: " + str([x.id for x in self.connectedTo])

    def getConnections(self):
        return {c[0] for c in self.connectedTo.keys()}

    def getId(self):
        return self.id
    
    def getName(self):
        return self.name
    
    def getLat(self):
        return self.lat
    
    def getLon(self):
        return self.lon
    

    def setDuration(self, d):
        self.duration = d

    def getDuration(self):
        return self.duration

    def setPred(self, p):
        self.predStop = p

    def getPred(self):
        return self.predStop

    def __lt__(self, other):
        if int(self.id) <= int(other.id):
            return True
        else:
            return False

    def __gt__(self, other):
        if int(self.id) > int(other.id):
            return True
        else:
            return False

    def getTimeWeight(self, nbr_stop_id, date, time):
        finalClosestTime = None
        finalWaitTime = None
        finalArriveTime = None
        finalRoute = None
        # finalC = None
        finalTimeWeight = float("inf")

        for c in self.connectedTo:
            if nbr_stop_id in c:
                if self.connectedTo[c][1]:  # self.connectedTo[c][1] isn't None
                    if date in self.connectedTo[c][1]:
                        acceptTime = [t for t in self.connectedTo[c][2] if t >= time]
                        if not acceptTime:
                            continue
                        closestTime = min(acceptTime)
                        closestDateTime = datetime.datetime.combine(date, closestTime)
                        waitTime = closestDateTime - datetime.datetime.combine(date, time)
                        timeWeight = (waitTime + self.connectedTo[c][3]).total_seconds()
                        if timeWeight < finalTimeWeight:
                            finalClosestTime = closestTime
                            finalWaitTime = waitTime
                            finalTimeWeight = timeWeight
                            finalArriveTime = (closestDateTime + self.connectedTo[c][3]).time()
                            finalRoute = self.connectedTo[c][0]
                            # finalC = c
                else:  # transfer
                    closestTime = time
                    closestDateTime = datetime.datetime.combine(date, closestTime)
                    waitTime = datetime.timedelta(seconds=0)
                    timeWeight = self.connectedTo[c][3].total_seconds()
                    if timeWeight < finalTimeWeight:
                        finalClosestTime = closestTime
                        finalWaitTime = waitTime
                        finalTimeWeight = timeWeight
                        finalArriveTime = (closestDateTime + self.connectedTo[c][3]).time()
                        finalRoute = self.connectedTo[c][0]
                        # finalC = c

        return finalTimeWeight, finalArriveTime, finalRoute, finalWaitTime, finalClosestTime  # finalC



