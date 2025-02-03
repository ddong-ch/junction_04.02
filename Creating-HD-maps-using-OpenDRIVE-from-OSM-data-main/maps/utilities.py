'''
Created on 19.07.2024

@author: abdelmaw
'''


import os #, math
from os import listdir
from os.path import isfile, join
from tqdm import tqdm
import requests 
import struct
import   cv2 
from pathlib import Path
import ctypes, sys
import numpy as np
from math import isclose 
import random
from pyproj import Proj, Transformer  #conda install conda-forge::pyproj
from math import factorial
import math as math
import copy
from PIL import Image

import itertools
import operator


 
from typing import Tuple, Optional
from math import isclose ,atan2 , sqrt
#from shapely.geometry import LineString
import random 

from shapely  import intersection_all ,intersection,  convex_hull ,MultiPoint ,is_ccw
import shapely as shapely

from centerline.geometry import Centerline  #pip install centerline
from shapely.geometry.polygon import LinearRing 
from shapely.geometry import Polygon#pip install shapely 
from shapely.geometry import LineString, Point
 


def intersectionPoint(Poly1  ,Poly2):
    
    line1 = LineString(Poly1)
    line2 = LineString(Poly2)
    
    
    inter  = intersection(line1,line2 )
    
    x, y = inter.coords.xy  
    
 
    
    if len(x) > 0:
    
        inter = [*zip(x , y)] 
 
        return centroid(inter)
    
    

def point_between_twoPoints(point1 ,point2 , distance):
    
    x0 = point1[0] 
    y0 = point1[1]



    deltaXPointCenter = point1[0] - point2[0]
    deltaYPointCenter = point1[1] - point2[1]
    
    
    hdg = np.arctan2(deltaYPointCenter, deltaXPointCenter)    
    
    
    deltaS = np.array(distance).astype(float)
    deltaT = 0        
    x = deltaS * np.cos(hdg) - deltaT * np.sin(hdg) + x0
    y = deltaS * np.sin(hdg) + deltaT * np.cos(hdg) + y0    
    return (x, y)    




def multiline_to_single_line(geometry ) -> LineString:
    if isinstance(geometry, LineString):
        return geometry
    coords = list(map(lambda part: list(part.coords), geometry.geoms))
    flat_coords = [Point(*point) for segment in coords for point in segment]
    return LineString(flat_coords)


def reduce_polygon(polygon, angle_th=0, distance_th=0):
    
    
 
    
    polygon = np.array(polygon)
    
    angle_th_rad = np.deg2rad(angle_th)
    points_removed = [0]
    i_while = 0
    
    while len(points_removed ) and i_while  < 100*len(points_removed ):
        
        i_while = i_while + 1
        points_removed = list()
        for i in range(0, len(polygon)-2, 2):
            v01 = polygon[i-1] - polygon[i]
            v12 = polygon[i] - polygon[i+1]
            d01 = np.linalg.norm(v01)
            d12 = np.linalg.norm(v12)
            if d01 < distance_th and d12 < distance_th:
                points_removed.append(i)
                continue
            angle = np.arccos(np.sum(v01*v12) / (d01 * d12 +.000000000000000000000000000000000000000000000000000000000000000000000000000001))
            if angle < angle_th_rad:
                points_removed.append(i)
        polygon = np.delete(polygon, points_removed, axis=0)
        
    
    reduced = polygon.tolist()
    
 
        
    return reduced


def order_points(points ):
    
    # xs = []
    #
    # for point in points:
    #     xs.append(point[0])
    #
    # xs = np.array(xs)
    # ind    = xs.argmin()
    
    center  = list( centroid(points) )
    #print(center)
    point0 = find_farest_point(points,center  )
    
    points_new = [ point0 ]  # initialize a new list of points with the known first point
    pcurr      = points_new[-1] 
    
    
    
    i_while = 0# initialize the current point (as the known point)
    while len(points)>0  and i_while  < 100*len(points ):
        i_while = i_while + 1
        d      = np.linalg.norm(np.array(points) - np.array(pcurr), axis=1)  # distances between pcurr and all other remaining points
        ind    = d.argmin()                   # index of the closest point
        points_new.append( points.pop(ind) )  # append the closest point to points_new
        pcurr  = points_new[-1]               # update the current point
    return points_new



def sort_counterclockwise(points, centre = None):
    if centre:
        centre_x, centre_y = centre
    else:
        centre_x, centre_y = sum([x for x,_ in points])/len(points), sum([y for _,y in points])/len(points)
    angles = [atan2(y - centre_y, x - centre_x) for x,y in points]
    counterclockwise_indices = sorted(range(len(points)), key=lambda i: angles[i])
    counterclockwise_points = [points[i] for i in counterclockwise_indices]
    return counterclockwise_points



def is_clockwise(poly):
    # """
    # returns True if the polygon is clockwise ordered, false if not
    # expects a sequence of tuples, or something like it (Nx2 array for instance),
    # of the points:
    # [ (x1, y1), (x2, y2), (x3, y3), ...(xi, yi) ]
    # See: http://paulbourke.net/geometry/clockwise/
    # """
    #
    # total = poly[-1][0] * poly[0][1] - poly[0][0] * poly[-1][1]  # last point to first point
    # for i in range(len(poly) - 1):
    #     total += poly[i][0] * poly[i + 1][1] - poly[i + 1][0] * poly[i][1]
    #
    # if total <= 0:
    #     return True
    # else: 
    #     return False 
    
    if len(poly) < 3:
        return True
    
    elif len(poly) == 3   :
        poly = poly + [poly[0]] 
        
    
    
    return not is_ccw( LinearRing(poly   ))
    
    
def is_clockwise3d(poly3d):
    """
    returns True if the polygon is clockwise ordered, false if not
    expects a sequence of tuples, or something like it (Nx2 array for instance),
    of the points:
    [ (x1, y1), (x2, y2), (x3, y3), ...(xi, yi) ]
    See: http://paulbourke.net/geometry/clockwise/
    """
    
    poly1 =[]
    poly2 = []
    poly3 =[]
    
    for point in poly3d:
        
        poly1.append([point[0] , point[1]])
        poly2.append([point[1] , point[2]])        
        poly3.append([point[0] , point[2]])          
        
        
    
        
        
    if is_clockwise(poly1)  and is_clockwise(poly2) and is_clockwise(poly3):
        return True
    else: 
        return False 
 
    
    
    
def download_url(url, save_path, chunk_size=128):
    #print("Downloading: " + url)
    r = requests.get(url, stream=True)
    path = Path(save_path)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        #print(f"Error creating directory: {e}")
        return
    
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)
 
def is_inside_polygon(polygon, point):
    
    try:
        Point_X = point[0]
        Point_Y = point[1]
        
        line =  LineString(polygon)
        sh_point =  Point(Point_X, Point_Y)
        polygon =  Polygon(line)    
        
        
        return polygon.contains(sh_point)

    except:
        cnt = 0
        point0 = polygon[0]
        xp = point[0]
        yp = point[1]
                
        for point in polygon[1:] + [polygon[0]]:
            x1, y1 = point0
            x2, y2 = point
        
            if (yp < y1) != (yp < y2) and xp < x1 + ((yp - y1) / (y2 - y1)) * (x2 - x1):
                cnt += 1
        
            point0 = point
        return cnt % 2 == 1


def PolygonArea(vertices):
    
    
    if len(vertices ) < 3:
        return 0
    
    elif len(vertices ) == 3:
        vertices = vertices + [vertices[0]]
          
    return Polygon(vertices).area

def centroid(vertices):
    
    
    if len(vertices) == 0:
        raise ValueError( " len(vertices) == 0 ")
    
    elif len(vertices) == 1:
        return vertices[0]
    
    elif len(vertices) <= 3:
        x = [p[0] for p in vertices]
        y = [p[1] for p in vertices]
        centroid = (sum(x) / len(vertices), sum(y) / len(vertices))

        return centroid
    
    else:
        x,y = shapely.centroid(Polygon(vertices) ).xy 
        x = x[0]
        y =y[0]
        return x, y 
    
    # try:
    #     x, y = 0 , 0
    #     n = len(vertices)
    #     signed_area = 0.0
    #     for i in range(n):
    #         x0, y0 = vertices[i]
    #         x1, y1 = vertices[(i + 1) % n]
    #         area = (x0 * y1) - (x1 * y0)
    #         signed_area += area
    #         x += (x0 + x1) * area
    #         y += (y0 + y1) * area
    #     signed_area *= 0.5
    #     x /= (6 * signed_area )
    #     y /= (6 * signed_area )
    #
    #
    #     return x, y
    #
    # except:
    #
    #     # #print(len(vertices))
    #     #
    #     # point = Polygon(vertices + [vertices[0] ]).centroid
    #     #
    #     # x,y = point.xy
    #
    #     if len(vertices) >  0:
    #         x = [p[0] for p in vertices]
    #         y = [p[1] for p in vertices]
    #         centroid = (sum(x) / len(vertices), sum(y) / len(vertices))
    #
    #         return centroid
    #
    #     else:
    #
    #         return (0,0)

def is_convex_polygon(points_cord):
    def cross_product_orientation(p, q, r):
        """ Returns the cross product of the vector pq and qr.
            >0 for counter-clockwise turn,
            <0 for clockwise turn,
            0 if the points are collinear.
        """
        (px, py), (qx, qy), (rx, ry) = p, q, r
        return (qy - py) * (rx - qx) - (qx - px) * (ry - qy)
    
    n = len(points_cord)
    if n < 3:
        return False  # A polygon must have at least 3 vertices

    prev_orientation = 0

    for i in range(n):
        p = points_cord[i]
        q = points_cord[(i + 1) % n]
        r = points_cord[(i + 2) % n]

        orientation = cross_product_orientation(p, q, r)

        if orientation != 0:
            if prev_orientation == 0:
                prev_orientation = orientation
            elif prev_orientation * orientation < 0:
                return False

    return True




 
def gbs_Degrees2Decimal(gps_arrey):
    if not isinstance(gps_arrey, list):
        return gps_arrey
    
    if len(gps_arrey) == 3:
        return gps_arrey[0] + gps_arrey[1] / 60.0 + gps_arrey[2] / 3600.0
    elif len(gps_arrey) == 2:
        return gps_arrey[0] + gps_arrey[1] / 60.0
    elif len(gps_arrey) == 1:
        return gps_arrey[0]
    else:
        return gps_arrey

def gbs_Decimal2Degrees(gps):
    Degrees = int(gps)
    Minutes_Seconds = abs(gps - Degrees)
    
    Minutes = int(60.0 * Minutes_Seconds)
    Seconds = int(3600.0 * (Minutes_Seconds - Minutes / 60.0))
    
    return [Degrees, Minutes, Seconds]

def projection_fromGeographic(latitude, longitude, referenceLat=0, referenceLon=0):
    radius = 6378137
    k = 1
    
    BuildingObJ_lon = referenceLon
    BuildingObJ_lat = referenceLat
    BuildingObJ_latInRadians = np.radians(BuildingObJ_lat)
    lat = np.radians(latitude)
    lon = np.radians(longitude - BuildingObJ_lon)
    B = np.sin(lon) * np.cos(lat)
    x = 0.5 * k * radius * np.log((1 + B) / (1 - B))
    y = k * radius * (np.arctan2(np.tan(lat), np.cos(lon)) - BuildingObJ_latInRadians)
    
    return (x, y)


# def ccw(A, B, C):
#
#     return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
#
# def intersect(A, B, C, D):
#
#     return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

 
def intersect(line1: Tuple[Tuple[float, float], Tuple[float, float]], 
                      line2: Tuple[Tuple[float, float], Tuple[float, float]]) -> Tuple[Optional[float], Optional[float]]:
    #Calculate the differences in x and y coordinates
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])
    
    # Function to calculate the determinant of a 2x2 matrix
    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]  
    
    
    x =  line2[0][0]
    y =  line2[0][1]
    
    if   x == line1[0][0] and  y == line1[0][1]:
        return True
    
    elif x == line1[1][0] and  y == line1[1][1]:
        return True
    
    
    point = (x,y)
    
    if min(line1[0][0], line1[1][0])  <= point[0]  <= max(line1[0][0], line1[1][0]) and  \
       min(line1[0][1] , line1[1][1]) <= point[1]  <= max(line1[0][1] , line1[1][1])  and  \
       min(line2[0][0], line2[1][0])  <= point[0]  <= max(line2[0][0], line2[1][0]) and   \
       min(line2[0][1] , line2[1][1]) <= point[1]  <= max(line2[0][1] , line2[1][1]):
        return True    
    
 
    x =  line2[1][0]
    y =  line2[1][1]
    
    if   x == line1[0][0] and  y == line1[0][1]:
        return True
    
    elif x == line1[1][0] and  y == line1[1][1]:
        return True    
 
 
 
    point = (x,y)
    
    if min(line1[0][0], line1[1][0])  <= point[0]  <= max(line1[0][0], line1[1][0]) and  \
       min(line1[0][1] , line1[1][1]) <= point[1]  <= max(line1[0][1] , line1[1][1])  and  \
       min(line2[0][0], line2[1][0])  <= point[0]  <= max(line2[0][0], line2[1][0]) and   \
       min(line2[0][1] , line2[1][1]) <= point[1]  <= max(line2[0][1] , line2[1][1]):
        return True  
 
    
    # Calculate the determinant of the x and y differences
    div = det(xdiff, ydiff)  
    if div == 0:
        return False
    
    # Calculate the determinants for the individual lines
    d = (det(*line1), det(*line2))
    
    # Calculate the x and y coordinates of the intersection point
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    
    point = (x,y)
    
    
    ##print(point)
    if   x == line1[0][0] and  y == line1[0][1]:
        return True
    
    elif x == line1[1][0] and  y == line1[1][1]:
        return True
    
    elif x == line2[0][0] and  y == line2[0][1]:
        return True
    
    
    elif x == line2[1][0] and  y == line2[1][1]:
        return True
    
    
    
    if min(line1[0][0], line1[1][0])  <= point[0]  <= max(line1[0][0], line1[1][0]) and  \
       min(line1[0][1] , line1[1][1]) <= point[1]  <= max(line1[0][1] , line1[1][1])  and  \
       min(line2[0][0], line2[1][0])  <= point[0]  <= max(line2[0][0], line2[1][0]) and   \
       min(line2[0][1] , line2[1][1]) <= point[1]  <= max(line2[0][1] , line2[1][1]):
        return True
    else:
        return False

 
def getValueFromTags(key, tags):
    if key in tags :
        index =  tags.index(key)
        return   tags[index+1]      
    else:
        return None
        

def ccworder(A):
    A= A- np.mean(A, 1)[:, None]
    return np.argsort(np.arctan2(A[1, :], A[0, :])) 





def simplify_polygon(PolygonPoints , tolerance = .1):
    
    
    
    if len(PolygonPoints) <=  6:
        return PolygonPoints
    polygon = Polygon(PolygonPoints)
    #tolerance = .1
    poly_line_offset = polygon.simplify(tolerance=tolerance)
    x, y = poly_line_offset.exterior.coords.xy           
    #PolygonPoints =  zip(x , y) 
    PolygonPoints = []
    
    for i in range(0, len(x)):
        PolygonPoints.append((x[i] , y[i]))
        
    
    
    return  PolygonPoints  
 


def polygon_offset(PolygonPoints, distance ):

    PolygonPointcopy = PolygonPoints.copy()
    i =0
    while len(PolygonPointcopy) < 4 and i < 10:
        i = i+1
        PolygonPointcopy = insertPoints(PolygonPointcopy)
        
        
        
    
    #PolygonPointcopy =  simplify_polygon(PolygonPointcopy, .1)   
  
    # PolygonPointcopy = order_points(PolygonPointcopy )
    # PolygonPoints =  reduce_polygon(PolygonPointcopy, 2, 2)
    # PolygonPointcopy = order_points(PolygonPointcopy )
    # PolygonPointcopy = sort_counterclockwise(PolygonPointcopy)
    poly_line = LinearRing(PolygonPointcopy)
    poly_line_offset = poly_line.offset_curve(distance ,  quad_segs=25, join_style= 2, mitre_limit=.1)
    x, y = poly_line_offset.xy
    #PolygonPoints =  simplify_polygon( [*zip(x , y)] , tolerance = .1)
    PolygonPoints_offset = [*zip(x , y)] 
    #PolygonPoints =  reduce_polygon(PolygonPoints_offset, 1, 3)
    
    if len(PolygonPoints_offset) > 0:
        if PolygonPoints_offset[0] != PolygonPoints_offset[-1]:
            PolygonPoints_offset.append(PolygonPoints_offset[0])
    else:
        PolygonPoints_offset = PolygonPointcopy
        
    
    
   
    # if len(PolygonPoints_offset)  <= 3 or PolygonPoints_offset[0] != PolygonPoints_offset[-1]:
    #
    #     PolygonPointorg = PolygonPoints.copy()
    #     PolygonPointorg.reverse()
    #
    #     poly_line = LinearRing(PolygonPoints)
    #     poly_line_offset = poly_line.offset_curve(-distance ,  quad_segs=16, join_style= 2, mitre_limit=5.0)
    #     x, y = poly_line_offset.xy
    #     #PolygonPoints =  simplify_polygon( [*zip(x , y)] , tolerance = .1)
    #     PolygonPoints_offset2 = [*zip(x , y)]     
    #     PolygonPoints_offset2.reverse()
    #     PolygonPoints_offset = PolygonPoints_offset+PolygonPoints_offset2
    
    return PolygonPoints_offset









"""



def CenterlinePoints(PolygonPoints  ): 

 
    #print("#######********** CenterlinePoints")
    PolygonPoints   =  reduce_polygon(PolygonPoints, angle_th= 5, distance_th= 2)
         
    polygon = Polygon(PolygonPoints)
    r =  sqrt( polygon.area )
    polygon_ext = LineString(list(polygon.exterior.coords))
    
    attributes = {"id": 1, "name": "polygon", "valid": True}
    centerline = Centerline(polygon,interpolation_distance= r /100.0, **attributes)
    
 
    geoms = centerline.geometry.geoms



    intesectiondict= dict()
    pointsdict = dict()
    
    for point in PolygonPoints:
        pointsdict[str(point)] = point
        
    

    for geom in  geoms:


        xs, ys = geom.xy 

        point1 = [ xs[0] , ys[0] ]
        point2 = [ xs[1] , ys[1]]


        for point in [point1 , point2]:
            if intesectiondict.get(str(point) , None) is None:
                intesectiondict[str(point)] = []
                pointsdict[str(point)] = point

            
        if str(point2 ) not in intesectiondict[str(point1)]:
            intesectiondict[str(point1)].append(str(point2 ))   
            
        if str(point1 ) not in intesectiondict[str(point2)]: 
            intesectiondict[str(point2)].append(str(point1))     
    
        centerpoints1 =[]
        centerpoints2 =[]
        centerpoints3 =[]
        
        
        
    centerLines = []
    
    for key in intesectiondict.keys():
    
        N = len(intesectiondict[key])
    
        point = pointsdict[key]
            
        if  N == 1:
            if point not in centerpoints1:
                centerpoints1.append( point )
    
    
        elif  N == 2:
            if point not in centerpoints2:
                centerpoints2.append( point ) 
    
        elif  N >= 3:
            if point not in centerpoints3:
                centerpoints3.append( point )    
                    
    
    
    
    print(len(centerpoints2)/20)
    
    rand_centerpoints2 = random.choices(centerpoints2 , k =  int(len(centerpoints2)/100) )  
    
    for centerpoints in [   centerpoints3  + rand_centerpoints2   ,  centerpoints1 + rand_centerpoints2 + centerpoints3       ]:
    
        coverd = []            
        notconected = []
        
        for Start in  centerpoints:
     
            coverd.append(Start)
        
            for End  in  centerpoints:
     
                if End not in coverd:
        
                    way    = Dijkstra_ShortestPath(centerLines , Start ,End )
        
                    if len(way) == 0  :
                        notconected.append([Start ,End])
        
        
        
        if len(notconected) !=0:
        
            while len(notconected) != 0 :
        
                shortest_notconected = None
                len_shortest =  None
        
        
                for noconection in notconected:
        
                    Start = noconection[0] 
                    End = noconection[1]
        
                    deltaX= np.array(Start[0] - End[0]  ).astype(float)
                    deltaY= np.array(Start[1] - End[1]  ).astype(float)
                    len_noconection  =   np.sqrt(  deltaX * deltaX    + deltaY *deltaY  )            
                    
                    point_a = Point(Start[0], Start[1])
                    point_b = Point(End[0], End[1])
                    
                    segment = LineString([point_a, point_b])
                    intersections = polygon_ext.intersection(segment)
                    
                    if   shortest_notconected is None  :
                        
                        if  intersections.is_empty:
                            len_shortest = len_noconection
                            shortest_notconected = noconection                    
                    else:
                        if len_noconection < len_shortest  and intersections.is_empty:
                            len_shortest = len_noconection
                            shortest_notconected = noconection
                        
                
 
        
                centerLines.append(shortest_notconected) 
        
                coverd = []            
        
                notconected = []
        
                for Start in  centerpoints:
             
                    coverd.append(Start)
                
                    for End  in  centerpoints:
             
                        if End not in coverd:
        
                            way   = Dijkstra_ShortestPath(centerLines , Start ,End )
        
                            if len(way) == 0  :
                                notconected.append([Start ,End])

                            
                            
    
    
    centerLinesnew = []
    for line in centerLines:  
        
        if line[0] in centerpoints1:
            PolygonPoint = find_closest_point(PolygonPoints ,line[0]  )
            
            centerLinesnew.append(   [PolygonPoint] + line )
            
        elif line[-1] in centerpoints1:
            PolygonPoint = find_closest_point(PolygonPoints ,line[-1]  )
            
            centerLinesnew.append(   line + [PolygonPoint] )
 
            
        else:
            centerLinesnew.append(  line)  

    centerLines =   centerLinesnew     
    
    Action = True
    
    while  Action:
        Action = False
    
        pointliesdict = dict()
        
        for index, line in  enumerate ( centerLines ):
        
            for point in [line[0] ,  line[-1]]:
        
                if point not in PolygonPoints:
        
                    if pointliesdict.get(str(point) , None) is None:
                        pointliesdict[str(point)] = []
        
        
        
                    if index not in pointliesdict[str(point)]:
                        pointliesdict[str(point)].append( index ) 
        
        
        
        line2remove= []
        newlines = []    
        
        for point_key in  pointliesdict.keys():
        
                N = len(pointliesdict[point_key])
        
                if N  ==  1  :
                    print("################ 1 ############--->" ,point_key )
        
                    indexLine1  = pointliesdict[point_key][0]
        
                    line1 =  centerLines[ indexLine1 ]
        
        
        
        
        
        
                elif N  ==  2  :
        
        
                    indexLine1  = pointliesdict[point_key][0]
                    indexLine2  = pointliesdict[point_key][1]
        
        
        
                    line1 =  centerLines[ indexLine1 ]
                    line2 =  centerLines[ indexLine2 ]
                    
                    if line1 not in line2remove and line2 not in line2remove :
                    
                        if line1[-1] == line2[0]:
         
                            newline = line1 + line2
                            
                        elif line1[0] == line2[-1]:
        
                            newline = line2 +line1 
                            
                        else:
                            line2copy = line2.copy()
                            line2copy.reverse()                  
                            newline = line1 + line2copy
                              
                                
                        line2remove.append(line1)
                        line2remove.append(line2)
                        newline = order_points(newline)
                        newline = [newline[0]] +reduce_polygon(newline, angle_th=10, distance_th=2)  +[newline[-1]]
                        newlines.append(newline)
                        Action = True
                    
        for line in  line2remove:
        
            if  line in centerLines:
                centerLines.remove(line) 
        
        centerLines = centerLines + newlines                

    return centerLines


""" 
def CenterlinePoints(PolygonPoints  ): 

 
    #print("#######********** CenterlinePoints")
    #PolygonPoints   =  reduce_polygon(PolygonPoints, angle_th= 5, distance_th= 2)
         
    polygon = Polygon(PolygonPoints)
    r =  sqrt( polygon.area )
    polygon_ext = LineString(list(polygon.exterior.coords))
    
    attributes = {"id": 1, "name": "polygon", "valid": True}
    centerline = Centerline(polygon,interpolation_distance= r /100.0, **attributes)
    
 
    geoms = centerline.geometry.geoms



    intesectiondict= dict()
    pointsdict = dict()
    
    for point in PolygonPoints:
        pointsdict[str(point)] = point
        
    

    for geom in  geoms:


        xs, ys = geom.xy 

        point1 = [ xs[0] , ys[0] ]
        point2 = [ xs[1] , ys[1]]


        for point in [point1 , point2]:
            if intesectiondict.get(str(point) , None) is None:
                intesectiondict[str(point)] = []
                pointsdict[str(point)] = point

            
        if str(point2 ) not in intesectiondict[str(point1)]:
            intesectiondict[str(point1)].append(str(point2 ))   
            
        if str(point1 ) not in intesectiondict[str(point2)]: 
            intesectiondict[str(point2)].append(str(point1))     
    
        centerpoints1 =[]
        #centerpoints2 =[]
        centerpoints3 =[]
        
        centerLines = []
        for key in intesectiondict.keys():
    
            N = len(intesectiondict[key])
            if N  !=  2  :
 
                point = pointsdict[key]
                
                if  N == 1:
                    if point not in centerpoints1:
                        centerpoints1.append( point )


                elif  N >= 3:
                    if point not in centerpoints3:
                        centerpoints3.append( point )    
                        
            # else:
            #
            #     centerpoints2.append( point )
                
  
    for point in centerpoints1 :
        
        line = []
        
        line.append(point)
        
        next_pointkey  = intesectiondict.get(str(point))[0]
        intesectiondict[str(point)] = []
        next_point = pointsdict[next_pointkey]
        i_while = 0
        
        while next_point not in centerpoints1  and  next_point not in centerpoints3  and i_while <100:
            i_while = i_while +1
            
            ##print(next_point)
            line.append(next_point)
            next_point_key_list  = intesectiondict.get(str(next_point)).copy()
            
            next_point_key_list.remove(str(line[-2]))
            
            #intesectiondict[str(next_point)] = next_point_key_list
            
            next_pointkey  = next_point_key_list[0]
            next_point = pointsdict[next_pointkey]
            
            
            
  
        line.append(next_point)      
        centerLines.append(line)
        
 
    for point in centerpoints3 :
        
        line = []
        
        line.append(point)
 
        next_point_key_list  = intesectiondict.get(str(point)).copy()

        
        for oldline in centerLines:
            
            lineend = oldline[-1]
            
            if lineend ==  point and str(oldline[-2])  in next_point_key_list :
                next_point_key_list.remove(str(oldline[-2]))
                #intesectiondict[ str(oldline[-2]) ] = next_point_key_list
                
                
            
 
        if len(next_point_key_list) > 0:
            
            for next_pointkey in next_point_key_list:
                    
 
 
                next_point = pointsdict[next_pointkey]
                
                i_while = 0 
                
                while next_point not in centerpoints1  and  next_point not in centerpoints3 and i_while <100 :
                    ##print(next_point)
                    
                    i_while = i_while +1
                    line.append(next_point)
                    next_point_key_list  = intesectiondict.get(str(next_point)).copy()
                    
                    if str(line[-2]) in next_point_key_list:
                    
                        next_point_key_list.remove( str(line[-2]))
                        intesectiondict[ str(line[-2]) ] = next_point_key_list
                        next_pointkey  = next_point_key_list[0]
                        next_point = pointsdict[next_pointkey]
                    
                    else:
                        break      
                    
                        
                line.append(next_point)      
                centerLines.append(line)
                
                
    
    # NodesDict = dict()
    # Pointsdict = dict()
    #
    #
    #
    #
    # for index, line in  enumerate ( centerLines ):
    #
    #     for point in [line[0] ,  line[-1]]:
    #
    #         if NodesDict.get(str(point) , None) is None:
    #             NodesDict[str(point)] = []
    #             Pointsdict[str(point)] = point
    #
    #
    #
    #         if str(point ) not in NodesDict[str(point)]:
    #             NodesDict[str(point)].append( index )     
    #
    #
    # nodekeys = list(NodesDict.keys())
    #
    # for nodekey  in nodekeys:
    #     node = Pointsdict[nodekey]
    #     nodes = []
    #
    #     for other_nodekey  in nodekeys:
    #         if  nodekey != other_nodekey:
    #             nodes.append(Pointsdict[other_nodekey])
    #
    #     PolygonPointsarray = np.array(nodes)
    #     Point = np.array(node)
    #     distances = np.linalg.norm(PolygonPointsarray-Point, axis=1)        
    #
    #     mergednodes = [node]
    #
    #     for i in range(0, len(nodes)) :
    #         if  distances[i] < r/1000:
    #             mergednodes.append(nodes[i])
    #
    #     if len(mergednodes) > 1:
    #         center = centroid(mergednodes)
    #
    #         for node in mergednodes:
    #             Pointsdict[str(node)] = center
    #
    #
    #
    # for index, line in  enumerate ( centerLines ):
    #
    #     line[0]  = Pointsdict[str(line[0])]   
    #     line[-1]  = Pointsdict[str(line[-1])]              
    #
    #     centerLines[index] = line
    
    
    centerLinesnew = []
    for line in centerLines:  
        add = True
        if line[0] in centerpoints1  and line[0] in centerpoints3  : 
            add = False  
        if line[-1] in centerpoints1  and line[-1] in centerpoints3  : 
            
            add = False            
    
        if add:
            centerLinesnew.append(  line)  
    centerLines =   centerLinesnew
    
    
    centerLinesnew = []
    for line in centerLines:  
        
        if line[0] in centerpoints1:
            PolygonPoint = find_closest_point(PolygonPoints ,line[0]  )
            
            centerLinesnew.append(   [PolygonPoint] + line )
            
        elif line[-1] in centerpoints1:
            PolygonPoint = find_closest_point(PolygonPoints ,line[-1]  )
            
            centerLinesnew.append(   line + [PolygonPoint] )
 
            
        else:
            centerLinesnew.append(  line)  

    centerLines =   centerLinesnew     
    
    
 

    
    centerLinesnew = []
    for line in centerLines:
    
        if len(line)  > 0:
    
            centerLinesnew.append( order_points(line)    )    
    
    centerLines =   centerLinesnew  
    
    
   
    
    
    


    
    for line in centerLines:
        for point in line:
            pointsdict[str(point)] = point
            
 

    found = True
    i_while = 0
    while found and i_while <  100:
        found = False
        i_while =   i_while + 1
        pointliesdict = dict()
    
        for index, line in  enumerate ( centerLines ):
    
            for point in [line[0] ,  line[-1]]:
    
                if point not in PolygonPoints:
    
                    if pointliesdict.get(str(point) , None) is None:
                        pointliesdict[str(point)] = []
    
    
    
                    if index not in pointliesdict[str(point)]:
                        pointliesdict[str(point)].append( index )   
    
    
    
        for key in  pointliesdict.keys():
    
            if len(pointliesdict[key]) == 1:
    
                line=centerLines[pointliesdict[key][0]]
                point=   pointsdict[key]
    
    
                if point not in PolygonPoints:    
                    line.remove(point)
    
                    centerLines[pointliesdict[key][0]] = line
    
                    found = True





    centerLinesnew = []
    for line in centerLines:
        line = order_points(line)
        
        if len(line) >=4:
            simpleline =   simplify_polygon(line.copy())
 
        
        else:
            simpleline  = line
            
        simpleline =  reduce_polygon(simpleline , angle_th=10, distance_th=2) 
 
 
        if simpleline[0] != line[0]:
            simpleline[0] =  line[0]  
            
        if simpleline[-1] != line[-1]:
            simpleline[-1] = line[-1]
              
                
        centerLinesnew.append(simpleline)
    
    centerLines =   centerLinesnew


    centerLinesnew = []
    for line in centerLines:
        
       
        if len(line) > 0:
    
            centerLinesnew.append(line)
    
    centerLines =   centerLinesnew   
    
       



    pointliesdict = dict()
    
    for index, line in  enumerate ( centerLines ):
    
        for point in [line[0] ,  line[-1]]:
    
            if point not in PolygonPoints:
    
                if pointliesdict.get(str(point) , None) is None:
                    pointliesdict[str(point)] = []
    
    
    
                if index not in pointliesdict[str(point)]:
                    pointliesdict[str(point)].append( index ) 
    
    
    
    for point_key in  pointliesdict.keys():
    
            N = len(pointliesdict[point_key])
    
            if N  ==  1  :
                #print("################ 1 ############--->" ,point_key )
    
                indexLine1  = pointliesdict[point_key][0]
    
                line1 =  centerLines[ indexLine1 ]
    
    
    
    
    
    
            elif N  ==  2  :
    
                try:
                    indexLine1  = pointliesdict[point_key][0]
                    indexLine2  = pointliesdict[point_key][1]
        
        
        
                    line1 =  centerLines[ indexLine1 ]
                    line2 =  centerLines[ indexLine2 ]
        
        
        
                    newline = line1 + line2
        
                    centerLines.remove(line1)
                    centerLines.remove(line2)
                    newline = order_points(newline)
                    newline = [newline[0]] +reduce_polygon(newline, angle_th=10, distance_th=2)  +[newline[-1]]
                    centerLines.append(newline)
                    
                except:
                    pass
    
    
    
    line2remove= []
    
    newlines = []
    
    
    for line in  centerLines:
        for other_line in  centerLines:
    
            if line != other_line :
                linestart = line[0]
                lineend = line[-1]
    
                if linestart in other_line and linestart != other_line[0] and linestart != other_line[-1]:
    
                    line2remove.append(other_line)
    
                    split_index = other_line.index(linestart)
    
                    newlines.append(other_line[0:split_index])
                    newlines.append(other_line[ split_index:])
    
    
                elif lineend in other_line and lineend != other_line[0] and lineend != other_line[-1]:
    
                    line2remove.append(other_line)
    
                    split_index = other_line.index(lineend)
    
                    newlines.append(other_line[0:split_index])
                    newlines.append(other_line[ split_index:])            
    
    
    
    
    
    for line in  line2remove:
    
        if  line in centerLines:
            centerLines.remove(line) 
    
    centerLines = centerLines + newlines
    

                
                
                
                
                
    #     for otherpoint_key in  pointliesdict.keys():
    #
    #         if point_key !=  otherpoint_key:
    #
    #             point1 = pointsdict[point_key]
    #             point2 = pointsdict[point_key]
    #
    #             deltax = point1[0] - point2[0]
    #             deltay = point1[1] - point2[1] 
    #
    #             dist = np.sqrt( deltax*deltax   +  deltay *deltay  )   
    #
    #
    #             if  dist < r /10:
    #
    #                 newpoint = [(point1[0] + point2[0]) / 2.0  , (point1[1] + point2[1]) / 2.0 ]
    #
    #                 for line_index in   pointliesdict.get(point_key) + pointliesdict.get(otherpoint_key) :
    #
    #                     line = centerLines[line_index]
    #
    #                     if line[0] ==  point1 or line[0] ==  point2:
    #                         line[0] = newpoint
    #
    #                     if line[-1] ==  point1 or line[-1] ==  point2:
    #                         line[-1] = newpoint                                
    #



   


    pointliesdict = dict()
    
    for index, line in  enumerate ( centerLines ):
    
        for point in [line[0] ,  line[-1]]:
    
            if point not in PolygonPoints:
    
                if pointliesdict.get(str(point) , None) is None:
                    pointliesdict[str(point)] = []
                    pointsdict[str(point)] = point
                    
 
                if index not in pointliesdict[str(point)]:
                    pointliesdict[str(point)].append( index ) 
    
    
    
    hasconections = []
    
    
    for point_key in  pointliesdict.keys():

        N = len(pointliesdict[point_key])
        
        if N >  2 and pointsdict[point_key] not in  hasconections:
            hasconections.append(pointsdict[point_key])
                
    centerLinesnew = []
    for line in centerLines:
        
        if line[0] == line[-1] :
            
            point = line[0]
            hasconectionscopy = hasconections.copy()
            for otherpoint in line:
                if otherpoint in hasconectionscopy:
                    hasconectionscopy.remove(otherpoint)
            
            
            if len(hasconectionscopy) > 0:
                otherpoint = find_closest_point(hasconectionscopy ,point ) 
                
                line[-1] = otherpoint
                           
        
    
        #if line[0] != line[-1] and len(line) >= 2   :
    
        centerLinesnew.append(line)
    
    centerLines =   centerLinesnew 



    centerLinesnew = []
    for line in centerLines:
    
        if line[0] != line[-1] and len(line) >= 2   :
    
            centerLinesnew.append(line)
    
    centerLines =   centerLinesnew  


    # pointliesdict = dict()
    #
    # for index, line in  enumerate ( centerLines ):
    #
    #     for point in [line[0] ,  line[-1]]:
    #
    #         if point not in PolygonPoints:
    #
    #             if pointliesdict.get(str(point) , None) is None:
    #                 pointliesdict[str(point)] = []
    #                 pointsdict[str(point)] = point
    #
    #             if index not in pointliesdict[str(point)]:
    #                 pointliesdict[str(point)].append( index ) 
    #
    # hasconections = []
    #
    #
    # for point_key in  pointliesdict.keys():
    #
    #     N = len(pointliesdict[point_key])
    #
    #     if N > 2 and pointsdict[point_key] not in  hasconections:
    #         hasconections.append(pointsdict[point_key])
    #
    #
    # for point_key in  pointliesdict.keys():
    #
    #         N = len(pointliesdict[point_key])
    #
    #         if N == 1:
    #             point = pointsdict[point_key]
    #
    #             #print("#################" , point)
    #
    #             hasconectionscopy = hasconections.copy()
    #             lineindex = pointliesdict[point_key][0]
    #             line = centerLines[lineindex]
    #
    #             for otherpoint in line:
    #                 if otherpoint in hasconectionscopy:
    #                     hasconectionscopy.remove(otherpoint)
    #
    #             otherpoint = find_closest_point(hasconectionscopy ,point )            
    #
    #
    #
    #             if otherpoint not in line:
    #                 if line[0] ==  point:
    #                     line[0] = otherpoint
    #
    #                 elif  line[-1] ==  point:
    #                     line[-1] = otherpoint
    #
    #             centerLines[lineindex] = line


    pointliesdict = dict()
    centerpoints =[]
    
    for index, line in  enumerate ( centerLines ):
    
        for point in [line[0] ,  line[-1]]:
    
            if point not in PolygonPoints:
    
                if pointliesdict.get(str(point) , None) is None:
                    pointliesdict[str(point)] = []
                    pointsdict[str(point)] = point
                    if point not in centerpoints:
                        centerpoints.append(point)
                    
 
                if index not in pointliesdict[str(point)]:
                    pointliesdict[str(point)].append( index )
    
    coverd = []            
    
    notconected = []
    
    
    for point_key in  pointliesdict.keys():
    
        Start = pointsdict[str(point_key)] 
    
        coverd.append(Start)
    
        for other_poit  in  pointliesdict.keys():
    
            End = pointsdict[str(other_poit)] 
    
            if End not in coverd:
    
                way    = Dijkstra_ShortestPath(centerLines , Start ,End )
    
                if len(way) == 0  :
                    notconected.append([Start ,End])
    
    
    
    if len(notconected) !=0:
        i_while = 0 
        while len(notconected) != 0 and i_while < 100 :
            i_while = i_while+1
            shortest_notconected = None
            len_shortest =  None
            
            
            for noconection in notconected:
            
                Start = noconection[0] 
                End = noconection[1]
            
                deltaX= np.array(Start[0] - End[0]  ).astype(float)
                deltaY= np.array(Start[1] - End[1]  ).astype(float)
                len_noconection  =   np.sqrt(  deltaX * deltaX    + deltaY *deltaY  )            
                
                point_a = Point(Start[0], Start[1])
                point_b = Point(End[0], End[1])
                
                segment = LineString([point_a, point_b])
                intersections = polygon_ext.intersection(segment)
                
                if   shortest_notconected is None  :
                    
                    if  intersections.is_empty:
                        len_shortest = len_noconection
                        shortest_notconected = noconection                    
                else:
                    if len_noconection < len_shortest  and intersections.is_empty:
                        len_shortest = len_noconection
                        shortest_notconected = noconection
                    
            
            
            
            centerLines.append(shortest_notconected) 
            
            coverd = []            
            
            notconected = []
            
            for Start in  centerpoints:
            
                coverd.append(Start)
            
                for End  in  centerpoints:
            
                    if End not in coverd:
            
                        way   = Dijkstra_ShortestPath(centerLines , Start ,End )
            
                        if len(way) == 0  :
                            notconected.append([Start ,End])
        



        
  
                   
    return centerLines






def polygon_convex_hull(PolygonPoints): 
    
    convex  = convex_hull(MultiPoint(PolygonPoints)) 
    
    x,y = convex.exterior.coords.xy    
    
    ##print(convex.__dict__)
        
    PolygonPoints =  simplify_polygon( zip(x , y) , tolerance = .1)
    
    
    PolygonPoints = sort_counterclockwise(PolygonPoints)
    
    PolygonPoints.reverse()
    
    return PolygonPoints





def  find_closest_point(PolygonPoints ,Point , MinDist = None ):

    PolygonPointsarray = np.array(PolygonPoints)
 
 
    Point = np.array(Point)
 
    
    distances = np.linalg.norm(PolygonPointsarray-Point, axis=1)
    min_index = np.argmin(distances)
    
    dist = distances[min_index]
    
    if MinDist is not None:
        
        if MinDist >= dist:
            return PolygonPoints[min_index]
        
        else:
            return None
            
    

    else:
        return PolygonPoints[min_index]


def  find_closest_two_points(PolygonPoints ,Point1 , Point2):

    PolygonPointsarray = np.array(PolygonPoints)
    Point1 = np.array(Point1)
    Point2 = np.array(Point2)
    distances = np.linalg.norm(PolygonPointsarray-Point1, axis=1)+np.linalg.norm(PolygonPointsarray-Point2, axis=1)
    min_index = np.argmin(distances)

    return PolygonPoints[min_index]

def  find_farest_point(PolygonPoints ,Point ):

    PolygonPointsarray = np.array(PolygonPoints)
    Point = np.array(Point)
    distances = np.linalg.norm(PolygonPointsarray-Point, axis=1)
    min_index = np.argmax(distances)

    return PolygonPoints[min_index]


def   polygons_intersected(PolygonPoints1 ,PolygonPoints2 ):

    p = Polygon(PolygonPoints1)
    q = Polygon(PolygonPoints2)
    print(p.intersects(q))  # True
    print(p.intersection(q).area)  # 1.0
    x = p.intersection(q)

    x, y = x.exterior.coords.xy           
    #PolygonPoints =  zip(x , y) 
    PolygonPoints = []
    
    for i in range(0, len(x)):
        PolygonPoints.append((x[i] , y[i]))
        
    
    
    return  PolygonPoints 


def insertPoints(PolygonPoints , minDistance =None): 
    
    
    added = True
    
    i_while = 0
    while added and i_while < 100:
        i_while = i_while +1 
        added = False
        newnods = [] 
        for node in  PolygonPoints :
        
            if len(newnods) > 0:
                startnode = newnods[-1]
        
        
                deltax = node[0] - startnode[0]
                deltay = node[1] - startnode[1] 
        
                length = np.sqrt( deltax*deltax   +  deltay *deltay  ) 
                
                
                if minDistance is not None:
                    if length >  minDistance:
                        added = True
            
                        x = (node[0] + startnode[0])/2
                        y = (node[1] + startnode[1])/2                            
            
            
                        newnode =  [x,y]
                
                        newnods.append( newnode)
                else:
                    
                    x = (node[0] + startnode[0])/2
                    y = (node[1] + startnode[1])/2                            
        
        
                    newnode =  [x,y]
            
                    newnods.append( newnode)            
                
                
            newnods.append(node)
        
        PolygonPoints = newnods  
    return PolygonPoints
 
# def get_roof_points(points_cord, roof_hight =   1):
#
#     roof_points = [] 
#
#
#
#     # newnods = [] 
#     # for node in  points_cord :
#     #
#     #     if len(newnods) > 0:
#     #         startnode = newnods[-1]
#     #
#     #
#     #         deltax = node[0] - startnode[0]
#     #         deltay = node[1] - startnode[1] 
#     #
#     #         length = np.sqrt( deltax*deltax   +  deltay *deltay  ) 
#     #
#     #         if length >  1:
#     #
#     #             x = (node[0] + startnode[0])/2
#     #             y = (node[1] + startnode[1])/2                            
#     #
#     #
#     #             newnode =  [x,y]
#     #
#     #             newnods.append( newnode)
#     #
#     #     newnods.append(node)
#     #
#     # points_cord = newnods  
#
#
#     x_center_all , y_center_all = centroid(points_cord)
#
#
#     indexList  =[]
#
#     if  not is_convex_polygon(points_cord):
#
#         x, y = centroid(points_cord)
#
#
#         for index , point in enumerate(points_cord):
#
#             X = point[0] 
#             Y = point[1]
#
#             deltaX= np.array(X - x  ).astype(float)
#             deltaY= np.array(Y - y  ).astype(float)
#             L = np.sqrt(  deltaX * deltaX    + deltaY *deltaY  )
#
#
#             hdg =  np.arctan2( deltaY ,deltaX )
#
#             if L > 2:
#
#                 for step in np.arange(0, L, 2):
#
#
#                     xp = step * np.cos( hdg)   + x
#                     yp = step * np.sin( hdg)   + y               
#
#                     if not is_inside_polygon(points_cord, xp, yp):
#
#                         indexList.append(index)
#
#                         break             
#
#
#
#
#         indexList.reverse()
#         for index in   indexList:
#             points_cord.remove(points_cord[index])
#
#
#
#
#         x_center_all , y_center_all =centroid(points_cord)
#
#
#     centerpoints =   CenterlinePoints(points_cord)
#
#     x_center = None
#     y_center = None
#
#
#     neerstCenterIndexOld = None
#
#     usedcenters = []            
#
#     for index , point in enumerate( points_cord ): 
#
#         ditarray =[]
#         for  center  in  centerpoints :
#
#
#             deltaX= np.array(center[0] - point[0]  ).astype(float)
#             deltaY= np.array(center[1] - point[1] ).astype(float)
#             dist= np.sqrt(  deltaX * deltaX    + deltaY *deltaY  )
#
#
#
#
#             ditarray.append(dist)     
#
#         ##print(ditarray)       
#         neerstCenterIndex = np.argsort(ditarray)[0] 
#
#         if neerstCenterIndexOld is None:
#             neerstCenterIndexOld = neerstCenterIndex
#
#
#
#         if neerstCenterIndex not in usedcenters:
#             usedcenters.append(neerstCenterIndex)
#
#         center = centerpoints[neerstCenterIndex]
#         x_center = center[0]
#         y_center = center[1]
#
#         if index <  len(points_cord ) -1:
#             pointssegment = []            
#             pointssegment.append( [point[0] , point[1],  0 ]  )
#             pointssegment.append( [points_cord[index+1][0] , points_cord[index+1][1] ,  0 ]) 
#             pointssegment.append( [x_center , y_center ,  roof_hight ]  ) 
#
#
#             if is_clockwise([[point[0] , point[1]],
#                               [points_cord[index+1][0] ,  points_cord[index+1][1]] ,
#                               [x_center , y_center ]]):
#                 pointssegment.reverse()
#
#
#             roof_points.append(pointssegment)
#
#         if neerstCenterIndexOld != neerstCenterIndex:
#
#             centerold = centerpoints[neerstCenterIndexOld]
#             x_center_old = centerold[0]
#             y_center_old = centerold[1]
#
#             pointssegment = []            
#             pointssegment.append( [point[0] , point[1],  0 ]  )
#             pointssegment.append( [x_center_old , y_center_old ,  roof_hight ]) 
#             pointssegment.append( [x_center , y_center ,  roof_hight ]  ) 
#
#             if is_clockwise([ [point[0] , point[1]] , 
#                              [x_center_old , y_center_old ] ,
#                              [x_center , y_center]]):
#                 pointssegment.reverse()            
#
#
#
#             roof_points.append(pointssegment) 
#
#
#             pointssegment = []            
#             pointssegment.append( [x_center_all , y_center_all ,  roof_hight]   )
#             pointssegment.append( [x_center_old , y_center_old ,  roof_hight ]  ) 
#             pointssegment.append( [x_center     , y_center     ,  roof_hight ]  ) 
#
#             if is_clockwise([  [x_center_all , y_center_all] , 
#                              [x_center_old , y_center_old]  ,
#                              [x_center     , y_center ] ]):
#                 pointssegment.reverse()   
#
#
#             roof_points.append(pointssegment)            
#
#
#
#             neerstCenterIndexOld = neerstCenterIndex
#
#
#
#
#
#
#     # if len(usedcenters ) < len(points_cord):
#     #     #print(len(usedcenters ) ," > " , len(points_cord))
#
#
#
#
#
#
#
#
#
#     return roof_points   
#
#
#
#
#
#
#
#
#
    
      
def connect_two_shapes_surface(shape1, shape_hight1  ,shape2, shape_hight2  ):

    roof_points = [] 
    
    for point in shape1:
        roof_points.append( [point[0] , point[1],  shape_hight1]  )
    
    
 
    for point in shape2:
        roof_points.append( [point[0] , point[1],  shape_hight2]  )
            
 

    return [roof_points ]  




def connect_two_shapes_multi_surfaces(shape1, shape_hight1  ,shape2, shape_hight2  ):

    roof_points = [] 
 
            
    if len(shape1) > 0 and  len(shape2)> 0 :
    
    
        x_center = None
        y_center = None
    
    
        neerstCenterIndexOld = None
    
        usedcenters = []            
    
        for index , point in enumerate( shape1 ): 
    
            ditarray =[]
            for  center  in  shape2 :
    
    
                deltaX= np.array(center[0] - point[0]  ).astype(float)
                deltaY= np.array(center[1] - point[1] ).astype(float)
                dist= np.sqrt(  deltaX * deltaX    + deltaY *deltaY  )
    
    
    
    
                ditarray.append(dist)     
    
            ##print(ditarray)       
            neerstCenterIndex = np.argsort(ditarray)[0] 
    
            if neerstCenterIndexOld is None:
                neerstCenterIndexOld = neerstCenterIndex
    
    
    
            if neerstCenterIndex not in usedcenters:
                usedcenters.append(neerstCenterIndex)
    
            center = shape2[neerstCenterIndex]
            x_center = center[0]
            y_center = center[1]
    
            if index <  len(shape1 ) -1:
                pointssegment = []            
                pointssegment.append( [point[0] , point[1],  shape_hight1 ]  )
                pointssegment.append( [shape1[index+1][0] , shape1[index+1][1] , shape_hight1 ]) 
                pointssegment.append( [x_center , y_center ,  shape_hight2 ]  ) 
    
    
                # if is_clockwise([[point[0] , point[1]],
                #                   [shape1[index+1][0] ,  shape1[index+1][1]] ,
                #                   [x_center , y_center ]]):
                #     pointssegment.reverse()
    
    
                roof_points.append(pointssegment)
    
            if neerstCenterIndexOld != neerstCenterIndex:
    
                centerold = shape2[neerstCenterIndexOld]
                x_center_old = centerold[0]
                y_center_old = centerold[1]
    
                pointssegment = []            
                pointssegment.append( [point[0] , point[1],  shape_hight1]  )
                pointssegment.append( [x_center , y_center ,  shape_hight2 ]  ) 
                pointssegment.append( [x_center_old , y_center_old ,  shape_hight2 ]) 
    
    
                # if is_clockwise([ [point[0] , point[1]] , 
                #                  [x_center_old , y_center_old ] ,
                #                  [x_center , y_center]]):
                #     pointssegment.reverse()            
    
    
    
                roof_points.append(pointssegment) 
    
    
                neerstCenterIndexOld = neerstCenterIndex
    
    



    return  roof_points   


def draw_Polygon_centerpoints(PolygonPoints ,centerlines ): 

    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon , Rectangle

    if not  is_clockwise(PolygonPoints):
        PolygonPoints.reverse()

    fig, ax = plt.subplots(  facecolor='lightskyblue', layout='constrained')
    plt.axis('equal') 
    facecolor = 'r' 
    p = Polygon(PolygonPoints, facecolor = facecolor , alpha=.7)    






    ax.add_patch( p  )

    xs, ys = zip(* PolygonPoints )        
    plt.scatter(xs,ys)


    # poly_line = LinearRing(PolygonPoints)
    # poly_line_offset = poly_line.offset_curve(-1 ,  quad_segs=16, join_style=2, mitre_limit=5.0)
    # x, y = poly_line_offset.xy
    # ax.plot(x, y, color="green", alpha=0.7, linewidth=3, 
    #         solid_capstyle='round', zorder=2) 
    # plt.scatter(x,y)
    
    for line in centerlines:
        xs, ys = zip(* line ) 
    
    
        ax.plot(xs, ys,  alpha=0.7, linewidth=3,          solid_capstyle='round', zorder=2)        
        #plt.scatter(xs,ys)


    plt.show()
    
  
  


 

def Dijkstra_ShortestPath(Centerlinesnetwork , Start ,End ):
    
    
    NodesDict = dict()
    Pointsdict = dict()
    lineslegth = dict()
    
    
    #
 
    
    for index, line in  enumerate ( Centerlinesnetwork ):
        
        if line is not None:
            for point in [line[0] ,  line[-1]]:
     
        
                if NodesDict.get(str(point) , None) is None:
                    NodesDict[str(point)] = []
                    Pointsdict[str(point)]= point
        
        
        
                if str(point ) not in NodesDict[str(point)]:
                    NodesDict[str(point)].append( index ) 
                
        lineslegth[index]   =  LineString(line).length
    
    
    nodekeys = list(NodesDict.keys())
    
    if not ( str(Start) in nodekeys  and str(End) in nodekeys ):
        #raise ValueError("Start ,End not in network ")
        return [] 
    
    if Start == End:
        return [] 
    
    way  = [End]
    waylines = []
    
    nods_cost = dict()
    nods_privice = dict()
    opt_way = dict()
    
    for key in nodekeys:
        nods_cost[key] = 999999999999999999999999999999999999999999999999999999999999999
        
    
    nods_cost[str(Start)] = 0
    
    visited = []
    
    for i in range(0 , len(nodekeys)):
        minvalue = 999999999999999999999999999999999999999999999999999999999999999
        minkey = None
        
        for  nodekey in nodekeys:
            if nodekey not  in visited and  nods_cost[nodekey ]  <= minvalue:
                minkey = nodekey
                minvalue =  nods_cost[nodekey ] 
                
        
        ##print(minkey)
        
        visited.append(minkey)
        
        lines_indexes = NodesDict[minkey]
        
        ##print(lines_indexes)        
                
            
        #lines_ends = []
        
        currentnode =  Pointsdict[str(minkey)]
        

        
        curentcost = nods_cost[minkey]
        
        for lines_index  in lines_indexes:
            
            
            line =  Centerlinesnetwork[lines_index]
        
        
            if currentnode == line[0]:
        
                lines_ends =  line[-1]  
        
            else:
        
                lines_ends = line[0]  
 
 
            if nods_cost[str(lines_ends)] >  curentcost + lineslegth[index]:
                nods_cost[str(lines_ends)] =  curentcost + lineslegth[index]            
                nods_privice[str(lines_ends)] = currentnode
                opt_way[str(lines_ends)] = lines_index
            
            
        if currentnode == End:
            break 
               
    #print(nods_cost)    
    #print(nodekeys)        
    
    
    try:
        
        i_while = 0
        while way[0] != Start  and i_while < 100:
 
            i_while = i_while + 1
            way.insert(0, nods_privice[str(way[0])] )
            
            if str(way[0]) in opt_way.keys():
                
                lines_index = opt_way[str(way[0])]
                line =  Centerlinesnetwork[lines_index]
                if line[0] != way[0]:
                    line.reverse()
                    
                
                waylines.insert(0,  line)
             


        
        
        return way   
    
    except:
        return []  
    
    
    
 
def project_to_Points( Points , point):
 
 
    if len(Points) >= 2:
        
        line = LineString(Points) 
        p = Point(point)
        p2 = line.interpolate(line.project(p))
        
        x,y = p2.xy
        
        x = x.tolist()[0]
        y = y.tolist()[0]
        
        return [x,y ]
        
    else:
        
        return None  
    
    
    
 
 
 
def is_point_on_line( line , point):
 
 
    project = project_to_Points( line , point) 
    
 
    deltax = project[0]  - point[0]
    deltay = project[1]  - point[1]             

    dist = np.sqrt( deltax*deltax   +  deltay *deltay  )     
    
    return dist<1e-3       




def repelace_midel_point_with2points(privicPoint,point, nextPoint , distace): 

    
    deltax = privicPoint[0]  - point[0]
    deltay = privicPoint[1]  - point[1]             
    
    dist1 = np.sqrt( deltax*deltax   +  deltay *deltay  ) 
    
    #print("dist1" ,dist1 )
    
     
    
    if dist1 > distace /2  + 0.5 :
    
        newpoint1 =   point_between_twoPoints(point ,privicPoint , - distace /2)
   
    else:
 
        newpoint1 =  privicPoint
    
    
    deltax = nextPoint[0]  - newpoint1[0]
    deltay = nextPoint[1]  - newpoint1[1]             
    
    dist2 = np.sqrt( deltax*deltax   +  deltay *deltay  )  
    
    #print("dist2" ,dist2 )
    
    if dist2 > distace :
    
        newpoint2 =    point_between_twoPoints(newpoint1 ,nextPoint , -distace)
 
    else:
        
        newpoint2 =  nextPoint
        
        
    return  newpoint1 , newpoint2

def comb(n, k):
    """
    N choose k
    """
    return factorial(n) / factorial(k) / factorial(n - k)


def bernstein_poly(i, n, t):
    """
     The Bernstein polynomial of n, i as a function of t
    """

    return comb(n, i) * ( t**(n-i) ) * (1 - t)**i


def bezier_curve(points, n=1000):
    """
       Given a set of control points, return the
       bezier curve defined by the control points.

       points should be a list of lists, or list of tuples
       such as [ [1,1], 
                 [2,3], 
                 [4,5], ..[Xn, Yn] ]
        n is the number of points at which to return the curve, defaults to 1000

        See http://processingjs.nihongoresources.com/bezierinfo/
    """

    nPoints = len(points)
    xPoints = np.array([p[0] for p in points])
    yPoints = np.array([p[1] for p in points])

    t = np.linspace(0.0, 1.0, n)

    polynomial_array = np.array(
        [bernstein_poly(i, nPoints-1, t) for i in range(0, nPoints)]
    )

    xvals = np.dot(xPoints, polynomial_array)
    yvals = np.dot(yPoints, polynomial_array)
    
    
    points = [*zip(xvals , yvals)]
    

    return points





def travel(dx, x1, y1, x2, y2):
    a = {"x": x2 - x1, "y": y2 - y1}
    mag = np.sqrt(a["x"]*a["x"] + a["y"]*a["y"])

    if (mag == 0):
        a["x"] = a["y"] = 0;
    else:
        a["x"] = a["x"]/mag*dx
        a["y"] = a["y"]/mag*dx

    return [x1 + a["x"], y1 + a["y"]]


def calculate_angle(x1, y1, x2, y2, x3, y3):
    # calcuate the two vector
    # vector 1: point1 to point 2
    vec1 = (x2 - x1, y2 - y1)  
    # vector 1: point1 to point 3
    vec2 = (x3 - x1, y3 - y1)
    # calculate dot product
    dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1]
    # calculate magnitude
    magnitude_vec1 = math.sqrt(vec1[0]**2 + vec1[1]**2)
    magnitude_vec2 = math.sqrt(vec2[0]**2 + vec2[1]**2)
    # calculate the angle for two vector
    angle_rad = math.acos(dot_product / (magnitude_vec1 * magnitude_vec2))
    # rad to degree
    # = math.degrees(angle_rad)
    return angle_rad

# output unit: 45.0 (degree)

# def plot_line(line,color="go-",label=""):
#     plt.plot([p[0] for p in line],
#          [p[1] for p in line],color,label=label)

def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y



def most_common(lst):

    
    return max(set(lst), key=lst.count)


if __name__ == '__main__':

    pass

    # PolygonPoints = [[0, 0], [0, 4], [4, 4], [10, 0]]
    # centerpoints = CenterlinePoints(PolygonPoints)
    # #print(centerpoints)
    # draw_Polygon_centerpoints(PolygonPoints ,centerpoints )
    #
    #
    #
    # cross_sections1 = [[3.414061134947077, 12.32306878859126],[3.9313468200146158, 7.591990807006974],[4.414147672713062, 3.17260742268625],[16.55304959847785, 4.441674894254976],[17.78763066404366, 4.597526392719522],[17.918662560077955, 8.271070053784182],[17.877278781756406, 8.605028379488346],[16.663389887476093, 8.48257277427971],[16.353010838401076, 11.443670212622093],[15.8564202171043, 11.388008878702411],[15.615015073358357, 13.592134041634266],[3.414061134947077, 12.32306878859126]]
    # centerpoints = CenterlinePoints(cross_sections1)
    # #print(centerpoints)
    # draw_Polygon_centerpoints(cross_sections1 ,centerpoints )
    #
    #
    #
    #
    # cross_sections2 = [[-20,-20], [-20,20], [40,20], [40,-20], [10,-20], [10,-10], [-10,-10], [-10,-20], [-20,-20]]
    # centerpoints = CenterlinePoints(cross_sections2)
    # #print(centerpoints)
    # draw_Polygon_centerpoints(cross_sections2 ,centerpoints )
    #
    #
    #
    #
    #
    # cross_sections3 = [[-45,-20], [-30,-20], [-30,10], [-40,10]]
    # centerpoints = CenterlinePoints(cross_sections3)
    # #print(centerpoints)
    # draw_Polygon_centerpoints(cross_sections3 ,centerpoints )
    #
    #
    #
    #
    # cross_sections4 = [[50,-22], [60,-22], [60,-10], [80,-10], [80,-20], [110,-20], [110,20], [55,25], [50,-22]]    
    # centerpoints = CenterlinePoints(cross_sections4)
    # #print(centerpoints)
    # draw_Polygon_centerpoints(cross_sections4 ,centerpoints )
    #
    #
    # from scenery_model import scenery  
    # name = "westertor2"
    # minlat = 51.71476  # 
    # minlon = 8.74467
    # maxlat = 51.71605
    # maxlon = 8.74728
    #
    # sceneryobj = scenery.Scenery.from_location(minlat , minlon  , maxlat  , maxlon  )

    # import matplotlib.pyplot as plt
    # import numpy as np
    # import math
    
    #https://stackoverflow.com/questions/51223685/create-circle-tangent-to-two-lines-with-radius-r-geometry
    

    
    # pointStart = [1,1]
    # pointmidel = [4,10]
    # pointend = [ 8,8]
    #
    # x_start = pointStart[0]
    # y_start = pointStart[1]
    #
    # x_midel = pointmidel[0]
    # y_midel = pointmidel[1]    
    #
    # x_end = pointend[0]
    # y_end = pointend[1]
    #
    # deltax0 = x_midel - x_start
    # deltay0 = y_midel - y_start
    #
    # line_segment1 = [pointStart, pointmidel]  # endpoint p1,p2 for line1 
    # line_segment2 = [pointmidel ,pointend ]  # endpoint p2,p3 for line2
    # line = line_segment1 + line_segment2
    # plot_line(line,'g-' )
    # radius = 2  #the required radius
    #
    # hdg0 = np.arctan2(deltay0, deltax0) if deltax0 != 0 else (np.pi / 2 if deltay0 > 0 else -np.pi / 2)
    #
    # deltax1 = x_end - x_midel
    # deltay1 = y_end - y_midel
    # hdg1 = np.arctan2(deltay1, deltax1) if deltax1 != 0 else (np.pi / 2 if deltay1 > 0 else -np.pi / 2)
    #
    # length1 = np.sqrt(deltax0 * deltax0 + deltay0 * deltay0) 
    # length2 = np.sqrt(deltax1 * deltax1 + deltay1 * deltay1) 
    #
    # radius = min(radius , length1 / 3, length2 / 3)
    # # angle
    # angle = calculate_angle(pointmidel[0],pointmidel[1], pointStart[0], pointStart[1], pointend[0], pointend[1])  #red point,purple point,green point
    # #print(angle)
    #
    # #the distance between point1 and radius from point1
    # dist=radius/np.tan(angle/2)
    #
    # l1_x1 = line_segment1[0][0]
    # l1_y1 = line_segment1[0][1]
    # l1_x2 = line_segment1[1][0]
    # l1_y2 = line_segment1[1][1]
    # new_point1 = travel(dist, l1_x2, l1_y2, l1_x1, l1_y1)
    #
    # l2_x1 = line_segment2[0][0]
    # l2_y1 = line_segment2[0][1]
    # l2_x2 = line_segment2[1][0]
    # l2_y2 = line_segment2[1][1]
    # new_point2 = travel(dist, l2_x1, l2_y1, l2_x2, l2_y2)
    #
    # plt.plot(line_segment1[1][0], line_segment1[1][1],'ro',label="Point 1")
    # plt.plot(new_point2[0], new_point2[1],'go',label="radius from Point 1")
    # plt.plot(new_point1[0], new_point1[1],'mo',label="radius from Point 1")
    #
    # # normal 1
    # dx = l1_x2 - l1_x1
    # dy = l1_y2 - l1_y1
    # normal_line1 = [[new_point1[0]+-dy, new_point1[1]+dx],[new_point1[0]+dy, new_point1[1]+-dx]]
    # plot_line(normal_line1,'m',label="normal 1")
    #
    # # normal 2
    # dx2 = l2_x2 - l2_x1
    # dy2 = l2_y2 - l2_y1
    # normal_line2 = [[new_point2[0]+-dy2, new_point2[1]+dx2],[new_point2[0]+dy2, new_point2[1]+-dx2]]
    # plot_line(normal_line2,'g',label="normal 2")
    #
    # #plot circle
    # #find the center of circle
    # x,y=line_intersection(normal_line1,normal_line2)
    # theta = np.linspace( 0 , 2 * np.pi , 150 )
    # a = x + radius * np.cos( theta )
    # b = y + radius * np.sin( theta )
    # plt.plot(a, b)
    # plt.legend()
    # plt.axis('square')
    #
    #
    #
    # from scenery_model.scenery import RoadReferenceLine
    #
    # pointStart = [1,1]
    # pointmidel = [4,10]
    # pointend = [ 8,8]
    #
    # x_start = pointStart[0]
    # y_start = pointStart[1]
    #
    # x_midel = pointmidel[0]
    # y_midel = pointmidel[1]    
    #
    # x_end = pointend[0]
    # y_end = pointend[1]
    #
    # deltax0 = x_midel - x_start
    # deltay0 = y_midel - y_start    
    #
    #
    # line_segment1 = [pointStart, pointmidel]  # endpoint p1,p2 for line1 
    # line_segment2 = [pointmidel ,pointend ]  # endpoint p2,p3 for line2
    #
    #
    # radius = 2  #the required radius
    #
    # hdg0 = np.arctan2(deltay0, deltax0) if deltax0 != 0 else (np.pi / 2 if deltay0 > 0 else -np.pi / 2)
    #
    # deltax1 = x_end - x_midel
    # deltay1 = y_end - y_midel
    # hdg1 = np.arctan2(deltay1, deltax1) if deltax1 != 0 else (np.pi / 2 if deltay1 > 0 else -np.pi / 2)
    #
    # length1 = np.sqrt(deltax0 * deltax0 + deltay0 * deltay0) 
    # length2 = np.sqrt(deltax1 * deltax1 + deltay1 * deltay1)
    #
    #
    # ref = RoadReferenceLine(x0=x_start, y0=y_start, hdg=hdg0, geometry_elements=[])
    #
    #
    #
    #
    #
    # angle =  calculate_angle(x_midel, y_midel, x_start, y_start, x_end, y_end) 
    # dist=radius/np.tan(angle/2)
    #
    # length1 -= dist
    # length2 -= dist
    #
    #
    #
    # l1_x1 = line_segment1[0][0]
    # l1_y1 = line_segment1[0][1]
    # l1_x2 = line_segment1[1][0]
    # l1_y2 = line_segment1[1][1]
    # new_point1 = travel(dist, l1_x2, l1_y2, l1_x1, l1_y1)
    #
    #
    # ref.addStraightLine(length1)
    # ref.set_endPoint(new_point1[0], new_point1[1])
    #
    # l2_x1 = line_segment2[0][0]
    # l2_y1 = line_segment2[0][1]
    # l2_x2 = line_segment2[1][0]
    # l2_y2 = line_segment2[1][1]
    # new_point2 = travel(dist, l2_x1, l2_y1, l2_x2, l2_y2)
    #
    # x_arc_start = new_point1[0]
    # y_arc_start = new_point1[1]
    # x_arc_end = new_point2[0]
    # y_arc_end = new_point2[1]
    # hed_arc_end = hdg1
    #
    # alfa = np.pi / 2 - hdg0
    # theta = hdg0 - hed_arc_end
    # arc_Radius = (x_arc_end - x_arc_start) / (np.sin(np.pi - hdg0) + np.cos(np.pi - alfa - theta))
    # arc_length = np.abs(theta * arc_Radius)
    #
    # #print(radius)
    # #print(arc_length)
    # ref.addArc(arc_length, 1.0 / -arc_Radius)
    # ref.set_endPoint(new_point2[0], new_point2[1])
    # ref.addStraightLine(length2)
    # ref.set_endPoint(x_end , y_end)
    #
    #
    #
    #
    #
    #
    #
    #
    # line = line_segment1 + line_segment2
    # plot_line(line,'g-' )
    #
    #
    # # normal 1
    # dx = l1_x2 - l1_x1
    # dy = l1_y2 - l1_y1
    # normal_line1 = [[new_point1[0]+-dy, new_point1[1]+dx],[new_point1[0]+dy, new_point1[1]+-dx]]
    # plot_line(normal_line1,'m',label="normal 1")
    #
    # # normal 2
    # dx2 = l2_x2 - l2_x1
    # dy2 = l2_y2 - l2_y1
    # normal_line2 = [[new_point2[0]+-dy2, new_point2[1]+dx2],[new_point2[0]+dy2, new_point2[1]+-dx2]]
    # plot_line(normal_line2,'g',label="normal 2")
    # x,y=line_intersection(normal_line1,normal_line2)
    # a = x + radius * np.cos( theta )
    # b = y + radius * np.sin( theta )
    # plt.plot(a, b)
    #
    # xs = []
    # ys = []
    #
    # Length = ref.getLength()
    # for s in np.arange(0, Length  +.1 , .1):
    #
    #     x, y = ref.ST2XY(s, 0)
    #     xs.append(x)
    #     ys.append(y)
    #
    # plt.plot(xs , ys , color="k" , alpha=.5)
    #
    #
    # plt.show()    
     
    
 