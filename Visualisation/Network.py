import datetime
import os
from queue import PriorityQueue
from math import ceil
from pprint import pprint
import Station


class Network:
    def __init__(self, *PathNames):
        self.StopList = {}
        self.Service2Date = {}
        self.Trip2Service = {}
        self.Name2StopId = {}
        self.RouteId2MetroNum = {}
        self.numStop = 0

        StopVisited = []
        for path in PathNames:
            MetroNum = path.split(sep="_")[-1]

            PathStops = os.path.join(path, "stops.txt")
            # stop_id,stop_code,stop_name,stop_desc,stop_lat,stop_lon,location_type,parent_station
            with open(PathStops, "r", encoding="utf-8") as StopsFile:
                StopsFile.readline()
                for s in StopsFile.readlines():
                    s_split = s.strip().split(sep=",")
                    stop_id, stop_name, stop_desc, stop_lat, stop_lon = \
                        [int(s_split[0]), s_split[2][1:-1], s_split[3][1:-1], s_split[4], s_split[5]]
                    self.addStop([stop_id, stop_name, stop_desc, stop_lat, stop_lon])

                    if stop_name not in self.Name2StopId:
                        self.Name2StopId[stop_name] = [[stop_id, ]]
                        StopVisited.append((stop_name, MetroNum))
                    else:
                        if (stop_name, MetroNum) not in StopVisited:
                            self.Name2StopId[stop_name].append([stop_id, ])
                            StopVisited.append((stop_name, MetroNum))
                        else:
                            self.Name2StopId[stop_name][-1].append(stop_id)

            PathCalendar = os.path.join(path, "calendar_dates.txt")
            # service_id,date,exception_type
            with open(PathCalendar, "r", encoding="utf-8") as CalandarFile:
                CalandarFile.readline()
                for c in CalandarFile.readlines():
                    c_split = c.strip().split(sep=",")
                    service_id = c_split[0]
                    date = c_split[1]
                    if service_id in self.Service2Date:
                        self.Service2Date[service_id].append(
                            datetime.date(int(date[:4]), int(date[4:6]), int(date[6:8])))
                    else:
                        self.Service2Date[service_id] = [datetime.date(int(date[:4]), int(date[4:6]), int(date[6:8])), ]

            PathTrips = os.path.join(path, "trips.txt")
            # route_id,service_id,trip_id,trip_headsign,trip_short_name,direction_id,shape_id
            with open(PathTrips, "r", encoding="utf-8") as TripsFile:
                TripsFile.readline()
                for t in TripsFile.readlines():
                    t_split = t.strip().split(sep=",")
                    self.Trip2Service[t_split[2]] = [t_split[0], t_split[1]]  # [route_id, service_id]

            PathRoutes = os.path.join(path, "routes.txt")
            # route_id,agency_id,route_short_name,route_long_name,route_desc
            with open(PathRoutes, "r", encoding="utf-8") as RoutesFile:
                RoutesFile.readline()
                for r in RoutesFile.readlines():
                    r_split = r.strip().split(sep=",")
                    self.RouteId2MetroNum[r_split[0]] = r_split[2][1:-1]
                    self.RouteId2MetroNum["transfer"] = "transfer"

        for path in PathNames:
            # trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign,shape_dist_traveled
            PathStopTimes = os.path.join(path, "stop_times.txt")
            with open(PathStopTimes, "r", encoding="utf-8") as StopTimesFile:
                StopTimesFile.readline()
                st_old = StopTimesFile.readline().strip().split(sep=",")
                for st in StopTimesFile.readlines():
                    st_split = st.strip().split(sep=",")
                    if int(st_split[4]) - int(st_old[4]) == 1:
                        from_stop_id = int(st_old[3])
                        to_stop_id = int(st_split[3])
                        trip_id = st_old[0]
                        route_id, service_id = self.Trip2Service[trip_id]
                        vaild_dates = self.Service2Date[service_id]
                        depart_time = datetime.time(int(st_old[1][:2]) % 24,
                                                    int(st_old[1][3:5]),
                                                    int(st_old[1][6:]))
                        # arrive_time = datetime.time(int(st_split[1][:2]) % 24,
                        #                             int(st_split[1][3:5]),
                        #                             int(st_split[1][6:]))

                        duration = (int(st_split[1][:2]) - int(st_old[1][:2])) * 3600 + \
                                   (int(st_split[1][3:5]) - int(st_old[1][3:5])) * 60 + \
                                   (int(st_split[1][6:]) - int(st_old[1][6:]))
                        time_weight = datetime.timedelta(seconds=duration)

                        self.addEdge(from_stop_id, to_stop_id, route_id,
                                     vaild_dates, depart_time, time_weight)
                    st_old = st_split

            # from_stop_id,to_stop_id,transfer_type,min_transfer_time
            PathTransfers = os.path.join(path, "transfers.txt")
            with open(PathTransfers, "r", encoding="utf-8") as transfersFile:
                transfersFile.readline()
                for tr in transfersFile.readlines():
                    tr_split = tr.strip().split(sep=",")
                    from_stop_id = int(tr_split[0])
                    to_stop_id = int(tr_split[1])

                    if from_stop_id not in self.StopList or to_stop_id not in self.StopList:
                        continue

                    route_id = "transfer"
                    depart_time = None
                    time_weight = datetime.timedelta(seconds=int(tr_split[3]))

                    self.addEdge(from_stop_id, to_stop_id, route_id,
                                 None, depart_time, time_weight)

                    self.addEdge(to_stop_id, from_stop_id, route_id,
                                 None, depart_time, time_weight)

        for ident_name in self.Name2StopId.values():
            route_id = "transfer"
            depart_time = None
            time_weight = datetime.timedelta(seconds=0)

            for stops_group in ident_name:
                if len(stops_group) == 2:
                    self.addEdge(stops_group[0], stops_group[1], route_id,
                                 None, depart_time, time_weight)
                    self.addEdge(stops_group[1], stops_group[0], route_id,
                                 None, depart_time, time_weight)

    def addStop(self, stop_properties):
        """
        stop_properties = [stop_id, stop_name, stop_desc, stop_lat, stop_lon]
        """
        if stop_properties[0] not in self.StopList:
            self.numStop = self.numStop + 1
            newStop = Station.Station(*stop_properties)
            self.StopList[newStop.id] = newStop

    def getStop(self, stop_id):
        if stop_id in self.StopList:
            return self.StopList[stop_id]
        else:
            return None

    def getStops(self):
        return self.StopList.keys()

    def addEdge(self, from_stop_id, to_stop_id, route_id, vaild_dates, time, time_weight):

        if (from_stop_id not in self.StopList) or (to_stop_id not in self.StopList):
            return

        self.StopList[from_stop_id].add_trip(route_id, vaild_dates, time, to_stop_id, time_weight)

    # dijkstra algorithm to calculate the smallest route
    def dijkstra(self, start_stop_id, end_stop_id, dt):
        date = dt.date()
        time = dt.time()
        [self.StopList[s].setDuration(float("inf")) for s in self.StopList]
        itinerary = []

        startStop = self.StopList[start_stop_id]
        startStop.setDuration(0.0)
        startStop.currentMetro = "transfer"
        startStop.currentDate = date
        startStop.currentTime = time
        visited = []
        pq = PriorityQueue()
        [pq.put((self.StopList[s].getDuration(), self.StopList[s])) for s in self.StopList]
        while not pq.empty():
            mn = pq.get()
            currentStop = mn[1]
            if currentStop.id not in visited:
                visited.append(currentStop.id)
            else:
                continue

            for nextStopId in currentStop.getConnections():
                if nextStopId in visited:
                    continue
                timeWeight, arriveTime, finalRoute, waitTime, closestTime = \
                    currentStop.getTimeWeight(nextStopId, currentStop.currentDate, currentStop.currentTime)

                if timeWeight == float("inf"):
                    continue

                newDuration = currentStop.getDuration() + timeWeight
                nextStop = self.StopList[nextStopId]
                if newDuration < nextStop.getDuration():
                    nextStop.setDuration(newDuration)
                    nextStop.setPred(currentStop)
                    nextStop.currentDate = date
                    nextStop.currentTime = arriveTime
                    nextStop.currentMetro = finalRoute
                    pq.put((newDuration, nextStop))

                if nextStopId == end_stop_id:
                    endStop = nextStop
                    duration = endStop.getDuration()
                    itinerary.append(
                        (
                            int(endStop.getId()),
                            self.RouteId2MetroNum[endStop.currentMetro],
                            ceil(endStop.getDuration()/60),
                            str(endStop.getName()), 
                            float(endStop.getLat()),
                            float(endStop.getLon())
                        ))
                    predStop = endStop.getPred()
                    while True:
                        itinerary.append(
                            (
                                int(predStop.getId()), 
                                self.RouteId2MetroNum[predStop.currentMetro],
                                ceil(predStop.getDuration()/60),
                                str(predStop.getName()),
                                float(predStop.getLat()),
                                float(predStop.getLon())
                             ))
                        if predStop.id == startStop.id:
                            break
                        predStop = predStop.getPred()

                    return itinerary[::-1], duration

    def compute_shortest_path(self, from_desc, to_desc, dt):
        itiner = []
        durartion = float("inf")
        for i in self.Name2StopId[from_desc]:
            start_stop_id = i[0]
            for j in self.Name2StopId[to_desc]:
                end_stop_id = j[0]
                itiner_ij, durartion_ij = self.dijkstra(start_stop_id, end_stop_id, dt)
                if durartion_ij < durartion:
                    durartion = durartion_ij
                    itiner = itiner_ij

        del_lst = []
        for i in range(len(itiner) - 1):
            if (itiner[i][1] == "transfer") & (itiner[i + 1][1] == "transfer") & (itiner[i][2] == itiner[i + 1][2]):
                del_lst.append(i)

        for idx in sorted(del_lst, reverse=True):
            del itiner[idx]

        return itiner, ceil(durartion/60)

    def __contains__(self, stop_id):
        return stop_id in self.StopList

    def __iter__(self):
        return iter(self.StopList.values())
    
if __name__ == "__main__":
    l_routes = ["1", "2", "3", "3b", "4", "5", "6", "7", "7b", "8", "9", "10", "11", "12", "13", "14"]
    p = "metro/RATP_GTFS_METRO_"
    arg = [p + l for l in l_routes]
    net = Network(*arg)
    
    dt1 = datetime.datetime.strptime('20190321 15:25', '%Y%m%d %H:%M')
    itiner1, d1 = net.dijkstra(2153, 1898, dt1)
    pprint(itiner1)

    dt2 = datetime.datetime.strptime('20190321 15:25', '%Y%m%d %H:%M')
    itiner2, d2 = net.dijkstra(1898, 1742, dt2)
    pprint(d2)
    

    dt3 = datetime.datetime.strptime('20190321 15:25', '%Y%m%d %H:%M')
    itiner3, d3 = net.dijkstra(1804, 1718, dt3)
    pprint(d3)
    