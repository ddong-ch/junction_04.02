
'''
Created on 03.11.2023

@author: abdel
'''
 
import os  
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
from pyproj import Proj, Transformer  # conda install conda-forge::pyproj
import inspect
import copy
from PIL import Image
import math
# from scipy.special import fresnel
# from scipy.optimize import minimize 
from typing import Tuple, Optional
from math import isclose
# from shapely.geometry import LineString
import random 
from shapely  import intersection_all , convex_hull , MultiPoint
from centerline.geometry import Centerline  # pip install centerline
from shapely.geometry.polygon import LinearRing 
from shapely.geometry import Polygon  # pip install shapely 
import importlib.util
from datetime import datetime 
import json
import copy 
import string 
import re


special_char_map = {ord('ä'):'ae', ord('ü'):'ue', ord('ö'):'oe', ord('ß'):'ss'}


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, currentdir) 

updir = Path(currentdir).parent.absolute()
 
spec = importlib.util.spec_from_file_location("osm_map", os.path.join(updir , "maps", "osm_map.py"))
osm_map = importlib.util.module_from_spec(spec)
sys.modules["osm_map"] = osm_map
spec.loader.exec_module(osm_map)
 
 


try:

    from maps import opendrive as opendrive

except:
    spec = importlib.util.spec_from_file_location("opendrive", os.path.join(updir , "maps", "opendrive.py"))
    opendrive = importlib.util.module_from_spec(spec)
    sys.modules["opendrive"] = opendrive
    spec.loader.exec_module(opendrive)
 
spec = importlib.util.spec_from_file_location("utilities", os.path.join(updir , "maps", "utilities.py"))
utilities = importlib.util.module_from_spec(spec)
sys.modules["utilities"] = utilities
spec.loader.exec_module(utilities)

 

sources = r"C:\scenery_Data" 

sources_osm = os.path.join(sources, "OSM")
 
if not os.path.isdir(sources_osm):
    #print('making dir ' , sources_osm)
    os.mkdir(sources_osm)
 


pointObjects = []

class Point():
    
    pointObjects = dict()
    
    
    def __new__(cls, *args, **kwargs):
        new_object = object.__new__(cls )
        new_object.__init__(*args, **kwargs)
    
        old_object = cls.pointObjects.get(str(new_object), None)
        if old_object is None:
            cls.pointObjects[str(new_object)] = new_object
            obj = new_object
        else:
            obj = old_object            
    
    
        return obj    
    
    
    def __init__(self, x , y , tags = {}  ):
        
        if hasattr(self, "tags"):
            return
        
        self.x = x
        self.y = y
        self.Z = 0
        self.tags = tags
        # self.latitude = latitude
        # self.longitude = longitude
        # self.node_id = node_id
        
        self.Ways_reference = []
        
        #self.connectionsNodes = []
        
        #self.NearNodes = []




    def add_Reference(self, obj):
     
        if not obj in  self.Ways_reference:
        
            self.Ways_reference.append(obj)

 
    
    def __str__(self):
        return  f"{self.x}_{self.y}"

    def draw_node(self , fig, ax):
 
        ax.scatter(self.x, self.y)  
  
class  SceneryObject():
  
    @classmethod     
    def newPointWay(cls, point  , tags):
        
        
        if  'addr:city' in tags  and 'addr:housenumber' in tags :
        
            return  None
 
 
        if  'shop' in tags    :
        
            return  None
        
        elif  'natural' in tags:
                        
            natural = tags.get('natural')
 
            if  natural in [ "stone"] :
                
                return Stone(point, tags )  
        
            elif  natural in [ "shrub" , 'tree_stump'] :
                
                return Shrub(point, tags )  
        
        
            elif  natural in [ "tree"  ] :
                
                return Tree(point, tags )  
            
            else:
                ##print("+++++" , natural)  
                ##print("+++++" , tags) 
                return  None
  
        elif  'amenity' in tags:
            
            amenity = tags.get('amenity')
            
            if  amenity in [ "pharmacy" , "cafe"  ,"toilets" ,"doctors" ,"dentist" , "fast_food"] :
                
                return None
            
            
            elif  amenity in [ "bench"] :
                
                return Bench(point, tags )             
            
            
            

            elif  amenity in [ "waste_basket"] :
                
                return Waste_Basket(point, tags )    
            

            elif  amenity in [ "bicycle_parking"] :
                
                return BicycleParking(point, tags )    
            

            elif  amenity in [ "recycling"] :
                
                return Recycling(point, tags )    
            

 
            
            
            else:
                
                # if amenity not in pointObjects:
                #
                #     pointObjects.append(amenity)
                #
                #     print("+++++" , amenity)  
                ##print("+++++" , tags) 
                return  None               
 
        elif  'highway' in tags:
            
            highway = tags.get('highway')
            if  highway in [ "street_lamp"] :
                
                return Street_Lamp(point, tags )             
            

            elif  highway in [ "bus_stop"] :
                
                return Bus_Stop(point, tags )             
             
            
            else:
                if highway not in pointObjects:
                
                    pointObjects.append(highway)
                
                    print("+++++" , highway) 
                
                ##print("+++++" , highway)  
                ##print("+++++" , tags) 
                return  None        



        elif  'man_made' in tags:
            
            man_made = tags.get('man_made')
            if  man_made in [ "flagpole"] :
                
                return Flagpole(point, tags )             
            

 
            
            else:
                ##print("+++++" , man_made)  
                ##print("+++++" , tags) 
                return  None         



        elif  'power' in tags:
            
            power = tags.get('power')
            if  power in [ "substation" , "transformer"] :
                
                return PowerSubstation(point, tags )             
            
            if  power in [ "tower"] :
                
                return PowerTower(point, tags ) 
 
            
            else:
                ##print("+++++" , power)  
                ##print("+++++" , tags) 
                return  None         



        
        else:
            
            ##print("+++++" , tags)  
            return  None      
               
  
    
    @classmethod     
    def newWay(cls, points , tags, relvantnodes):
        
        
 
        #
        
        if   len(points)  == 0 :
        
            return None
        
        elif   len(points)  ==1 :
 
            
            return cls.newPointWay(points , tags)

        if "boundary"  in tags or len(tags) == 0  or 'demolished:building' in tags   or  'historic' in tags:
        
            return None
        
        elif 'place' in tags and  tags.get('place') == 'region':
        
            return None #organizationalAreaSpace(points, tags , relvantnodes)        
        
        
        
        elif len(tags) == 1 and 'source' in tags:
        
            return None #organizationalAreaSpace(points, tags , relvantnodes) 
        
        elif   len(tags) == 0 :
            classList= []
            
            for node in points:
 
                for ref in node.Ways_reference:
                    classList.append(ref.__class__ )  
                    
               
 
            
            for node in  relvantnodes:
                for ref in node.Ways_reference:
                    classList.append(ref.__class__ )
                
            #print(classList) 
            if len( classList ) > 0  and len( classList ) < 10:
               
                wayclass = utilities.most_common(classList) 
                
                
                if  wayclass ==  Bridge    :
                
                    return Waterway(points, tags, relvantnodes)
                
 
                else:
 
                    return wayclass(points, tags , relvantnodes )  
                
            else:
                return organizationalAreaSpace(points, tags, relvantnodes)
                
                
                
                

 
           
        
        elif "landuse" in tags:
            
            landuse = tags.get("landuse")
            
            if landuse in ["allotments" , "orchard" , "cemetery" , "greenhouse_horticulture", "plant_nursery" , "flowerbed", "greenfield", "forest" , "farmland"  , "meadow" ,   "brownfield" , "grass" , "village_green" , "farmyard", "recreation_ground"]:
                return GreenSpace(points, tags , relvantnodes)

            elif  landuse in ["railway"]:
                
                if points[0] !=  points[-1]:
                
                    return Railway(points, tags , relvantnodes)
                
                else:
                    return organizationalAreaSpace(points, tags, relvantnodes)

            elif  landuse in ["basin"]:
                
                return Waterway(points, tags , relvantnodes)
            
            elif  landuse in ["industrial"  , "commercial"  , "clerical" , "education" , "construction"  , "retail" , "residential" ]:
                
                return organizationalAreaSpace(points, tags , relvantnodes) 
 
        elif  'natural' in tags:
                        
            natural = tags.get('natural')
            
            if natural == 'water':
            
                return Waterway(points, tags , relvantnodes) 
            
            elif  natural in [ "landform", "scrub", "beach", "wood","scree","grassland","wetland", "tree_row", "valley", "sand", "shrubbery",  "earth_bank"] :
                
                return GreenSpace(points, tags , relvantnodes)  



            elif  natural in [ "stone"] :
                
                return Stone(points, tags )  

            elif  natural in [ "shrub" , 'tree_stump'] :
                
                return Shrub(points, tags )  


            elif  natural in [ "tree"  ] :
                
                return Tree(points, tags )  
            
            else:
                print("+++++" , tags)
            
            
        elif "waterway" in tags:
            return Waterway(points, tags , relvantnodes) 
        
        elif   "building" in tags  :
            
            building = tags.get('building')
            
            if building == "bridge":
            
                return Bridge(points, tags , relvantnodes) 

            elif building == "railway":
            
                if points[0] !=  points[-1]:
                
                    return Railway(points, tags , relvantnodes)
                
                else:
                    return organizationalAreaSpace(points, tags, relvantnodes)

            
            else:
                return Building(points, tags , relvantnodes)                      




        elif   'building:part' in tags  :
            
            #building = tags.get('building') 
            return Building(points, tags , relvantnodes)   
        
        elif   'roof:edge' in tags  :
            
            #building = tags.get('building') 
            return Building(points, tags , relvantnodes)           

        elif  'roof:ridge' in tags  :
            
            #building = tags.get('building') 
            return Building(points, tags , relvantnodes)   

        elif  'roof:ridge' in tags  :
            
            #building = tags.get('building') 
            return Building(points, tags , relvantnodes)   
  
  
        elif  'roof:shape' in tags  :
            
            #building = tags.get('building') 
            return Building(points, tags , relvantnodes)  
        
        elif 'building:material' in tags  :
            
            #building = tags.get('building') 
            return Building(points, tags , relvantnodes) 
        
             
        elif "railway" in tags:
    
            if points[0] !=  points[-1]:
            
                return Railway(points, tags , relvantnodes)
            
            else:
                return organizationalAreaSpace(points, tags, relvantnodes)  
     
        
        elif   "bridge" in tags   and  tags.get("bridge") == 'yes':
            
            return Bridge(points, tags, relvantnodes)
 
 
        elif   "highway" in tags  :

            highway = tags.get("highway")
    
            if "railway" in tags:
    
                if points[0] !=  points[-1]:
                
                    return Railway(points, tags , relvantnodes)
                
                else:
                    return organizationalAreaSpace(points, tags, relvantnodes)   
  
            elif "lanes" in tags: 
            
                return DrivingRoad(points, tags , relvantnodes)
            
            elif "lane" in tags: 
            
                return DrivingRoad(points, tags, relvantnodes )


            
            elif  highway  == 'service'   :
                
 
                return ServiceRoad(points, tags , relvantnodes  )
            
            elif "maxspeed" in tags:
            
                return DrivingRoad(points, tags, relvantnodes  )  

                 

            # elif "motor_vehicle:conditional" in tags    :
            #
            #
            #     # if 'surface' in tags:
            #     #     surface= tags.get("surface")
            #     #
            #     #     if surface == "paving_stones":
            #     #
            #     #         return PedestrianRoad(points, tags, relvantnodes )
            #     #
            #     #     elif surface == "paving_stones":
            #     #
            #     #         return DrivingRoad(points, tags, relvantnodes )
            #     #
            #     #     else:
            #     #
            #     #         return PedestrianRoad(points, tags, relvantnodes )
            #     #
            #     #
            #     #
            #     # else:
            #     return DrivingRoad(points, tags, relvantnodes ) 
 

            
            elif "bus" in tags:
            
                return DrivingRoad(points, tags  , relvantnodes  )        
     
            elif   highway == "residential":
            
                return DrivingRoad(points, tags , relvantnodes  )        
            
            elif    highway == "living_street":
            
                return DrivingRoad(points, tags , relvantnodes ) 
 
 
            elif  highway  == 'service' and  tags.get("service")  == 'driveway':
                
                return ServiceRoad(points, tags , relvantnodes  )
 
            elif  highway  == 'service' and  tags.get("service")  == 'parking_aisle':
                
                return ServiceRoad(points, tags , relvantnodes  )
            

 
            
            # elif "motor_vehicle:conditional" in tags  and 'entrance' not in tags:
            #
            #     return PedestrianRoad(points, tags, relvantnodes )
 
            elif  highway in  [ 'cycleway' ]:
                
                
                
                return CycleRoad(points, tags , relvantnodes  )


 

         
            elif  highway in  ["pedestrian"  , "path"   , "steps"   , 'construction'  , "footway"  ]:
 
                return PedestrianRoad(points, tags , relvantnodes  )
             
 

    
            else:
     
                return PedestrianRoad(points, tags , relvantnodes)  # Road(  points, tags    ) 





        elif "amenity" in tags:
            
            amenity = tags.get('amenity')
 
            if amenity in [  "college"  , "hospital" , "kindergarten"   , "school"  , "place_of_worship" , "community_centre"  , "nursing_home" , "police"]: 
            
                return organizationalAreaSpace(points, tags , relvantnodes )   
  
            elif amenity in [ 'parking']: 
                return ParkingSpace(points, tags, relvantnodes )          
   
        elif "parking" in tags:
            
            return ParkingSpace(points, tags  , relvantnodes) 
         
        elif 'public_transport'  in tags:
            
            public_transport = tags.get('public_transport')
            
            if public_transport == 'station':
                
                return organizationalAreaSpace(points, tags, relvantnodes  ) 
            
 
        
        elif  "leisure" in tags:
        
            leisure = tags.get("leisure")
        
            if leisure in [ "park"  , 'garden' , "outdoor_seating" , "playground" ]:
        
                return GreenSpace(points, tags , relvantnodes )            
         
        # elif "motor_vehicle:conditional" in tags:
        #     return organizationalAreaSpace(points, tags , relvantnodes )  
            
        elif  'natural' in tags:
                            
            natural = tags.get('natural')
            
            if    natural in [ 'scrub' , 'garden' , "shrubbery"  , "tree_row" , "grassland" , "wood"]: 
                
                return GreenSpace (points, tags , relvantnodes )                
 

            
            # else:
            #     return organizationalAreaSpace(points, tags , relvantnodes )
                
 
            
        elif   'historic' in tags:
            
            # return None
            return organizationalAreaSpace(points, tags , relvantnodes )              
            
            
        elif "boundary"  in tags or 'demolished:building' in tags  :#or   or  'historic' in tags:
            
            # return None
            return organizationalAreaSpace(points, tags , relvantnodes )      
        
        elif "area" in tags  and tags.get("area") == 'yes': 
            
            return organizationalAreaSpace(points, tags , relvantnodes )         
        
 
        elif "barrier" in tags: 
        
            return Barrier(points, tags , relvantnodes) 
 
        elif 'area:highway' in tags  and tags.get('area:highway' )  == 'traffic_island' : 
        
            return Barrier(points, tags , relvantnodes)  


        elif 'area:highway' in tags  and tags.get('area:highway' )  == 'cycleway' : 
        
            return PedestrianRoad(points, tags , relvantnodes)

  
        elif 'aeroway' in tags  and tags.get('aeroway' )  == 'helipad' : 
        
            return ParkingSpace(points, tags , relvantnodes)

        else:
            ##print("#####################################################################")
            ##print(tags)
            return None  # SceneryObject(points, tags , relvantnodes)
        
    def __init__(self, points , tags, relvantnodes):
        
        
        #print(self.__class__.__name__)
        
        self.points = points
        self.tags = tags
        self.relvantnodes = relvantnodes
 
        Y = []
        X = []
        pointscord = []
 
        for point in self.points:
            point.add_Reference(self)
 
            x, y = point.x  , point.y
    
            if y != None:
                Y.append(y)
                X.append(x)
                
                pointscord.append([x, y])
        
        self.area = utilities.PolygonArea(pointscord)
        
        
 
        center = utilities.centroid(pointscord)
        self.x_center = center[0]
        self.y_center = center[1]

 

        housenumber = tags.get("addr:housenumber", None)
        
 
        
        city = tags.get("addr:city", None)
 
 
                
        postcode = tags.get("addr:postcode", None)          
        
     
              
        street = tags.get("addr:street", None)
        
 
 
        self.address = None
        
        for ele in  [housenumber , street , postcode , city  ]:
 
            if ele  is not None: 
                
                # #print(ele)
                if self.address is None:
                    self.address = ele
                    
                else:
                    self.address = self.address + ele
                
                if ele != city:
                    self.address = self.address + "_"
    
        if self.address  is None:
            #x_center , y_center = self.get_Center()
            self.address = f"{self.x_center}_{self.y_center}"  # ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        
        
        
        
        self.address =  str(self.__class__.__name__) + "_"+ self.address.replace(";", "_")
 
 
    def get_Center(self):
    
        return (self.x_center, self.y_center)       
      
 
    def draw_way(self , fig, ax, color=None):
 
        if len(self.points) > 0:
            from matplotlib.patches import Polygon 
            points_cord = []
            
            for node in self.points:
                points_cord.append([node.x , node.y])
            
            if self.points[0] == self.points[-1]:
            
                p = Polygon(points_cord, facecolor=color , alpha=.3)  # facecolor=facecolor,
                ax.add_patch(p)  
            else:
                
                xs, ys = zip(*points_cord)  
                ax.plot(xs, ys, color=color  , alpha=.5) 


    def update(self):
        
        pass

class  PointObject(SceneryObject):
    
    def __init__(self, centernode,Radius, tags, relvantnodes):
        
        #centernode = points 
        
        self.centerPoint = centernode
        
        
        points =[]
        
        x_center =  centernode.x
        y_center =  centernode.y
        
        #Radius = 3
        Radius_abs = np.abs(Radius)
   
        for theta in range(0,360,5):
 
            xs = x_center + Radius_abs *  np.cos(theta*np.pi/180)   
            ys = y_center + Radius_abs *  np.sin(theta*np.pi/180)            
            
            points.append(Point(xs , ys, tags )) 
         
    
        points.append(points[0]) 
        
        
        SceneryObject.__init__(self, points, tags, relvantnodes)

class  Flagpole(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="g"
        
        PointObject.draw_way(self, fig, ax, color=color)
 
class  PowerTower(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="g"
        
        PointObject.draw_way(self, fig, ax, color=color)

class  PowerSubstation(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="g"
        
        PointObject.draw_way(self, fig, ax, color=color)

class  Tree(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="g"
        
        PointObject.draw_way(self, fig, ax, color=color)
     
class  Shrub(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="g"
        
        PointObject.draw_way(self, fig, ax, color=color)

class  Stone(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="y"
        
        PointObject.draw_way(self, fig, ax, color=color)
 
class  Bench(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="k"
        
        PointObject.draw_way(self, fig, ax, color=color)
 
class  Waste_Basket(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="k"
        
        PointObject.draw_way(self, fig, ax, color=color)

class  Recycling(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="k"
        
        PointObject.draw_way(self, fig, ax, color=color)

class  BicycleParking(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="k"
        
        PointObject.draw_way(self, fig, ax, color=color)

class  Street_Lamp(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="y"
        
        PointObject.draw_way(self, fig, ax, color=color)
 
class  Bus_Stop(PointObject):
    
 
 
    def __init__(self, centernode, tags ):
     
        relvantnodes =[]
        
        Radius = .01
        
        PointObject.__init__(self, centernode, Radius, tags, relvantnodes) 
    
    
    def draw_way(self, fig, ax):
        
        color="b"
        
        PointObject.draw_way(self, fig, ax, color=color) 
              
class  Building(SceneryObject):
 
    def __init__(self, points, tags, relvantnodes):
        SceneryObject.__init__(self, points, tags, relvantnodes)

        
        ##print(relvantnodes)

        self.commanWalls = False
             
        self.roof_levels = tags.get('roof:levels', None)         
        self.roof_material = tags.get('roof:material', None)       
        self.roof_shape = tags.get('roof:shape', None)                 
        self.roof_color = tags.get('roof:colour', None)  
         
        self.buildingType = tags.get('building', None)  
        self.building_levels = tags.get('building:levels', None)                           
        self.building_color = tags.get('building:colour', None)          
        self.building_material = tags.get('building:material', None)




        self.shop = tags.get('shop', None)      
        self.building_part = tags.get('building:part', None) == 'yes'
        self.demolished = tags.get('demolished:building', None) == 'yes'       


        BuildingType = self.tags.get("building")
        
        
        if BuildingType == 'yes' and self.tags.get("amenity")  is not None:
            BuildingType = self.tags.get("amenity") 
        
        
        
 
 
        if self.roof_shape  is None and  self.roof_levels is not None: 
            self.roof_shape =   "gabled" 
                
            
            
        
 
 
        if  BuildingType == "parking":
            if self.building_levels is None:
                self.building_levels  = random.choice([ 2,  3, 4 ]) 
            
                
 
            if self.roof_shape  is None:
                
                self.roof_shape =   "flat"             
                
            if self.roof_levels is None:
 
            
                self.roof_levels = 0
                            
 
                
        elif  BuildingType in ["chapel"  ,"church" ,"parish_hall" ,"religious" ]:
            if self.building_levels is None:
                self.building_levels  = random.choice([  3, 4 ]) 

            if self.roof_shape  is None:
                
                self.roof_shape =   "gabled"    
            if self.roof_levels is None:
 
            
                self.roof_levels = 1
            

        elif  BuildingType in [ "yes" , "commercial" ,"retail" , "industrial" , "warehouse" ,"supermarket" ,"mosque"]:
            if self.building_levels is None:
                self.building_levels  = random.choice([2,  3, 4 ]) 


 

        elif  BuildingType in [   "industrial" , "warehouse" ,"sports_centre" , "sports_hall"]:
            if self.building_levels is None:
                self.building_levels   = random.choice([2,  3, 4 ]) 

 

        elif  BuildingType in [ "office" ,"residential"  ,"apartments" ,"government" ,"hotel" ,"civic"]:
            if self.building_levels is None:
                self.building_levels  = random.choice([ 2, 3, 4 ]) 
                
            
            if self.roof_shape  is None:
                
                self.roof_shape = random.choice([ "flat", "gabled" , "gabled"])
                
                
                        
 
 

        elif  BuildingType in ["house"  ,"detached" , "semidetached_house" ]:
            if self.building_levels is None:
                self.building_levels   = random.choice([2,  3 ]) 

 
 
        elif  BuildingType in ["garage"  ,"shelter" ,"garages"  ,"terrace" ,"barn" ,"carport" ,"shed" , "roof" ,"pavilion" ,"greenhouse" ,"agricultural" ,"farm_auxiliary" , "stable" ,"hut" ,"cabin"]:
            if self.building_levels is None:
                self.building_levels  = 1
                
 

            if self.roof_shape is None:
               
                self.roof_shape  = "flat"
                
                
                if  BuildingType in [ "barn" , "shed" , "roof" ,"pavilion" ,"greenhouse" ,"agricultural" ,"farm_auxiliary" , "stable" ,"hut" ,"cabin"]:
                    self.roof_shape  = "gabled"


 
                
            if self.roof_levels is None:
 
            
                self.roof_levels = 0
            
 


        elif  BuildingType in ["service" ,"toilets" ,"outbuilding" ,"container" , "allotment_house"]:
            if self.building_levels is None:
                self.building_levels  = 1

            if self.roof_levels is None:
 
            
                self.roof_levels = 0 

        elif  BuildingType in ["hospital"  ,"school" ,"construction" ]:
            if self.building_levels is None:
                self.building_levels  = random.choice([  3, 4 ]) 

 
        
        elif  BuildingType in ["kindergarten" ]:
            
            
            if self.building_levels is None:
                self.building_levels  = 1
                
            if self.roof_levels is None:
 
            
                self.roof_levels = 0 
                              
        
        elif  self.tags.get('height') is not None:
            if self.building_levels is None:
                height = self.tags.get('height')
                height =float(height.replace("m" ,""))
                self.building_levels  = int(height)/3            
            
            
        elif  BuildingType in ["tower" ]:
            if self.building_levels is None:
                self.building_levels  = random.choice([  3, 4 ])            
            

        
        if  self.tags.get('roof:height') is not None:
             
            height = self.tags.get('roof:height')
            height = float(height.replace("m" ,""))

            
            if  self.tags.get('height') is not None:
 
                height1 = self.tags.get('height')
                height1 =float(height1.replace("m" ,""))
                
                height = height - height1
            
            
            
            self.roof_levels  = int(height)/3             
                

 
        if self.building_levels is None:
            self.building_levels = 1
           
         
        if self.roof_shape  is None:
            
            self.roof_shape = random.choice([ "flat", "gabled", "hipped",   "mansard", "half-hipped", "skillion"])
            
 
        
        if self.roof_material is None  and self.roof_color is None  :
            
            
            if self.building_material is not None:
                self.roof_material = self.building_material
            
            elif self.roof_shape  == "flat":
                
                self.roof_color = "black"
                
            else:
                
                self.roof_color = random.choice([ "red" , "gray" , "brown" ])

        
        if self.roof_levels  is None and self.roof_shape !="flat":
            
            if self.building_levels == 1:
            
                self.roof_levels = 0
            
            else:
                    
                self.roof_levels = 1
                
               
        try:    
            
        
            self.roof_levels  = float(self.roof_levels )
        
        except:
            
            self.roof_levels = 0             
        
        
        try: 
            self.building_levels  = float(self.building_levels )             
                
        except:
            
            self.building_levels = 1  

 
    def draw_way(self, fig, ax, color=None):
 
        if len(self.points) > 0: 
            # from matplotlib.patches import Polygon 
            Buildingobjcord =[]
            for index , point in enumerate(self.points):
                Buildingobjcord.append([point.x , point.y  ])  


            xs, ys = zip(* Buildingobjcord) 
            ax.plot(xs, ys , color="b")                 
                 
 
 
class  AreaSpace(SceneryObject):
    
    def __init__(self, points, tags, relvantnodes):
        SceneryObject.__init__(self, points, tags, relvantnodes)
 
    
    def draw_way(self, fig, ax, color=None):
        SceneryObject.draw_way(self, fig, ax, color=color)

class  organizationalAreaSpace(AreaSpace):

    def draw_way(self, fig, ax):
        AreaSpace.draw_way(self, fig, ax, color='y')
        # if len(self.points) > 0: 
        #     # from matplotlib.patches import Polygon 
        #     Buildingobjcord =[]
        #     for index , point in enumerate(self.points):
        #         Buildingobjcord.append([point.x , point.y  ])  
        #
        #
        #     xs, ys = zip(* Buildingobjcord) 
        #     ax.plot(xs, ys , color="g") 
        
        pass
 
class  ParkingSpace(AreaSpace):

    def draw_way(self, fig, ax):
        AreaSpace.draw_way(self, fig, ax, color='gray')

class GreenSpace(AreaSpace):
    
    
    def __init__(self, points, tags, relvantnodes):
        
        if len(points) == 1:
            
 
            
            raise ValueError("error ") 
        
 
        
        AreaSpace.__init__(self, points, tags, relvantnodes)

    def draw_way(self, fig, ax):
        AreaSpace.draw_way(self, fig, ax, color='g')

class LineObject(SceneryObject):
    
    def __init__(self, points, tags, relvantnodes , Width = None  ):
        
        
        
        
        if "width" in tags:
            width = float(tags.get("width").replace("m" ,"" ).replace("," ,"." ))
        
        
        
        
        
        else:
        
            width = 2.5
            
        if width > 3 : 
            width = 2.5
        
        
        if Width is not None:
            width = Width
            
            
            
        
        if  points[0] !=  points[-1]:
        
            points_cord = []
        
            for node in  points:
                points_cord.append([node.x , node.y   ])
        
        
        
        
            points_cordcopy = points_cord.copy()
            points_cordcopy.reverse()
            cross_section_co = points_cord + points_cordcopy 
        
        
            #points2.reverse()
            cross_section_co = utilities.polygon_offset(cross_section_co, -width/2)  
        
        
        
        
            outer_points = []
        
            for point  in cross_section_co:
                
                obj = Point(point[0] , point[1] , dict())
                obj.add_Reference(self)
                outer_points.append(  obj ) 
        
        
            outer_points.append(outer_points[0])  
            
            
            self.outer_points = outer_points
            
        else:
            
            self.outer_points = points
            
             

        
        
        SceneryObject.__init__(self, points, tags, relvantnodes)

    def draw_way(self, fig, ax, color=None):
        #SceneryObject.draw_way(self, fig, ax, color=color)
        if len(self.outer_points) > 0:
            from matplotlib.patches import Polygon 
            points_cord = []
            
            for node in self.outer_points:
                points_cord.append([node.x , node.y])


            #xs, ys = zip(*points_cord)  # create lists of x and y values
            
            #ax.scatter(xs, ys)  
            
            if self.outer_points[0] == self.outer_points[-1]:
            
                p = Polygon(points_cord, facecolor=color , alpha=.5)  # facecolor=facecolor,
                ax.add_patch(p)  
            else:
                
                xs, ys = zip(*points_cord)  
                ax.plot(xs, ys, color=color  , alpha=.5)  
       
class Waterway(LineObject):
    
    def __init__(self, points, tags, relvantnodes):
        
        Width=3 
        LineObject.__init__(self, points, tags, relvantnodes, Width=Width)
 

    def draw_way(self, fig, ax):
        LineObject.draw_way(self, fig, ax, color='b') 

class Barrier(LineObject):
    
    
    def __init__(self, points, tags, relvantnodes):
        
        Width=1 
        LineObject.__init__(self, points, tags, relvantnodes, Width=Width)
 
    

    def draw_way(self, fig, ax):
        LineObject.draw_way(self, fig, ax, color='y') 
           
class StraightLine:
    
    def __init__(self, length=1):
        self.length = length
                
    def XY2ST(self, x0, y0, hdg, X, Y, S0):
        deltaX = np.array(X - x0).astype(float)
        deltaY = np.array(Y - y0).astype(float)        
        S = deltaX * np.cos(2 * np.pi - hdg) - deltaY * np.sin(2 * np.pi - hdg) + S0
        T = deltaX * np.sin(2 * np.pi - hdg) + deltaY * np.cos(2 * np.pi - hdg)
        return (S, T)
        
    def ST2XY(self, x0, y0, hdg, S, S0, T):
        delta_s = S - S0
        if delta_s > self.length:
            return (None, None)
        else:
            deltaS = np.array(S - S0).astype(float)
            deltaT = np.array(T).astype(float)        
            x = deltaS * np.cos(hdg) - deltaT * np.sin(hdg) + x0
            y = deltaS * np.sin(hdg) + deltaT * np.cos(hdg) + y0    
            return (x, y)
    
    def get_endPoint(self, x0, y0, hdg):
        x_end = x0 + self.length * np.cos(hdg)
        y_end = y0 + self.length * np.sin(hdg)
        hdg_end = hdg
        return (x_end, y_end, hdg_end)
      
# class Spiral:
#
#     def __init__(self, length=1, CurvaturStart=1, CurvaturEnd=1):
#         if length <= 0:
#             raise ValueError("Length must be positive")
#         self.length = length
#         self.CurvaturStart = CurvaturStart
#         self.CurvaturEnd = CurvaturEnd
#         self._gamma = 1.0 * (-1 * CurvaturEnd - -1 * CurvaturStart) / length
#
#     @classmethod
#     def _calc(cls, gamma, s, x0=0, y0=0, kappa0=0, theta0=0):
#         C0 = x0 + 1j * y0
#         kappa0 = -1 * kappa0
#
#         if gamma == 0 and kappa0 == 0:
#             Cs = C0 + np.exp(1j * theta0) * s
#         elif gamma == 0 and kappa0 != 0:
#             Cs = C0 + np.exp(1j * theta0) / kappa0 * (np.sin(kappa0 * s) + 1j * (1 - np.cos(kappa0 * s)))
#         else:
#             s_arr = np.asarray(s)
#             Sa, Ca = fresnel((kappa0 + gamma * s_arr) / np.sqrt(np.pi * np.abs(gamma)))
#             Sb, Cb = fresnel(kappa0 / np.sqrt(np.pi * np.abs(gamma)))
#             Cs1 = np.sqrt(np.pi / np.abs(gamma)) * np.exp(1j * (theta0 - kappa0**2 / 2 / gamma))
#             Cs2 = np.sign(gamma) * (Ca - Cb) + 1j * Sa - 1j * Sb
#             Cs = C0 + Cs1 * Cs2
#
#         theta = gamma * s_arr**2 / 2 + kappa0 * s_arr + theta0
#         return (Cs.real, Cs.imag, theta)
#
#     def ST2XY(self, x0, y0, hdg, S, S0, T):
#         if S < S0:
#             raise ValueError("S must be greater than or equal to S0")
#
#         theta0 = hdg
#         delta_s = S - S0
#
#         if delta_s > self.length:
#             return (None, None)
#         else:
#             kappa0 = self.CurvaturStart
#             xs, ys, hed = Spiral._calc(self._gamma, delta_s, x0, y0, kappa0, theta0)
#             xs += T * np.sin(np.pi - hed)
#             ys += T * np.cos(np.pi - hed)
#             return (xs, ys)
#
#     def get_endPoint(self, x0, y0, hdg):
#         theta0 = hdg
#         delta_s = self.length
#         kappa0 = self.CurvaturStart
#         x_end, y_end, hdg_end = Spiral._calc(self._gamma, delta_s, x0, y0, kappa0, theta0)
#         return (x_end, y_end, hdg_end)
#
#     def XY2ST(self, x0, y0, hdg, X, Y, S0):
#         theta0 = hdg
#         kappa0 = self.CurvaturStart
#
#         def distance_func(s):
#             xs, ys, _ = self._calc(self._gamma, s, x0, y0, kappa0, theta0)
#             return np.sqrt((X - xs)**2 + (Y - ys)**2)
#
#         res = minimize(distance_func, 0, bounds=[(0, self.length)])
#         S_soll = res.x[0]
#         T_min = distance_func(S_soll)
#
#         # If the closest point on the spiral is beyond its length
#         if S_soll >= self.length:
#             return (None, None)
#         else:
#             S = S_soll + S0
#             return (S, T_min)
 
class Arc:
    
    def __init__(self, length=1, Curvatur=1):
        if length <= 0:
            raise ValueError("Length must be positive")
        self.length = length
        self.Curvatur = Curvatur

    def ST2XY(self, x0, y0, hdg, S, S0, T):
        Radius = 1.0 / self.Curvatur
        Radius_abs = np.abs(Radius)
        delta_s = S - S0

        if delta_s > self.length:
            return (None, None)

        theta = delta_s / Radius_abs
        deltax = Radius_abs * np.sin(theta)
        deltay = Radius_abs * (1 - np.cos(theta))

        if Radius < 0:
            deltay = -deltay
            hdg_end = hdg - theta
        else:
            hdg_end = hdg + theta

        deltax_rot = deltax * np.cos(hdg) - deltay * np.sin(hdg)
        deltay_rot = deltax * np.sin(hdg) + deltay * np.cos(hdg)

        xs = x0 + deltax_rot - T * np.sin(hdg_end)
        ys = y0 + deltay_rot + T * np.cos(hdg_end)

        return (xs, ys)

    def get_endPoint(self, x0, y0, hdg):
        Radius = 1.0 / self.Curvatur
        Radius_abs = np.abs(Radius)
        delta_s = self.length

        theta = delta_s / Radius_abs
        deltax = Radius_abs * np.sin(theta)
        deltay = Radius_abs * (1 - np.cos(theta))

        if Radius < 0:
            deltay = -deltay
            hdg_end = hdg - theta
        else:
            hdg_end = hdg + theta

        deltax_rot = deltax * np.cos(hdg) - deltay * np.sin(hdg)
        deltay_rot = deltax * np.sin(hdg) + deltay * np.cos(hdg)

        x_end = x0 + deltax_rot
        y_end = y0 + deltay_rot

        hdg_end = (hdg_end + 2 * np.pi) % (2 * np.pi)

        return (x_end, y_end, hdg_end)

    def XY2ST(self, x0, y0, hdg, X, Y, S0):
        Radius = 1.0 / self.Curvatur
        deltaX = X - x0
        deltaY = Y - y0

        deltax_rot = deltaX * np.cos(-hdg) - deltaY * np.sin(-hdg)
        deltay_rot = deltaX * np.sin(-hdg) + deltaY * np.cos(-hdg)

        Radius_abs = np.abs(Radius)
        x_center = 0
        y_center = Radius

        deltaXPointCenter = deltax_rot - x_center
        deltaYPointCenter = deltay_rot - y_center

        L = np.sqrt(deltaXPointCenter ** 2 + deltaYPointCenter ** 2)

        if Radius > 0:
            theta = np.arctan2(deltaYPointCenter, deltaXPointCenter)
            theta = np.pi / 2 + theta
        else:
            theta = np.arctan2(deltaXPointCenter, deltaYPointCenter)

        theta = (theta + 2 * np.pi) % (2 * np.pi)

        L_circl = np.abs(theta) * Radius_abs

        if L_circl > self.length:
            return (None, None)
        else:
            S = L_circl + S0

            if Radius > 0:
                T = Radius_abs - L
            else:
                T = L - Radius_abs

            return (S, T)
 
class RoadReferenceLine:
    
    def __init__(self, x0=0, y0=0, hdg=0, geometry_elements=None):
        self.x0 = x0
        self.y0 = y0
        self.hdg = hdg
        self.geometry_elements = geometry_elements if geometry_elements is not None else []

    @classmethod  
    def Connect3points(cls, x_start, y_start, x_midel, y_midel, x_end, y_end ):
        deltax0 = x_midel - x_start
        deltay0 = y_midel - y_start
        hdg0 = np.arctan2(deltay0, deltax0) if deltax0 != 0 else (np.pi / 2 if deltay0 > 0 else -np.pi / 2)
        
        deltax1 = x_end - x_midel
        deltay1 = y_end - y_midel
        hdg1 = np.arctan2(deltay1, deltax1) if deltax1 != 0 else (np.pi / 2 if deltay1 > 0 else -np.pi / 2)

        if isclose(hdg0, hdg1, abs_tol=1e-2):
            deltax = x_end - x_start
            deltay = y_end - y_start   
            length = np.sqrt(deltax * deltax + deltay * deltay) 
            ref = RoadReferenceLine(x0=x_start, y0=y_start, hdg=hdg0, geometry_elements=[StraightLine(length)])
        else:
            ref = RoadReferenceLine(x0=x_start, y0=y_start, hdg=hdg0, geometry_elements=[])
            length1 = np.sqrt(deltax0 * deltax0 + deltay0 * deltay0) 
            length2 = np.sqrt(deltax1 * deltax1 + deltay1 * deltay1) 
            dist_inarc = min( 7,   length1 *40/100    , length2 *40/100   )
            
            
            length1 -= dist_inarc
            length2 -= dist_inarc
            
            ref.addStraightLine(length1)                
            x0, y0, hdg0 = ref.get_endPoint()
            
            x_arc_start = x0
            y_arc_start = y0
            x_arc_end = x_midel + dist_inarc * np.cos(hdg1)
            y_arc_end = y_midel + dist_inarc * np.sin(hdg1)
            hed_arc_end = hdg1
            
            alfa = np.pi / 2 - hdg0
            theta = hdg0 - hed_arc_end
            arc_Radius = (x_arc_end - x_arc_start) / (np.sin(np.pi - hdg0) + np.cos(np.pi - alfa - theta))
            
            
            
            arc_length = np.abs(theta * arc_Radius)
            
            ref.addArc(arc_length, 1.0 / -arc_Radius)
            ref.set_endPoint(x_arc_end, y_arc_end)
            ref.addStraightLine(length2)

        return ref

    @classmethod  
    def fitRoadReferenceLine(cls, points, x0=None, y0=None, hdg=None):
        
        if len(points) < 1:
            hdg_start = 0 if hdg is None else hdg
            x0_start = 0 if x0 is None else x0
            y0_start = 0 if y0 is None else y0
            return RoadReferenceLine(x0_start, y0_start, hdg_start, [])            
        
        
        points = copy.copy(points)
        if x0 is None or y0 is None:
            x0, y0 = points[0].x, points[0].y
        x0_start, y0_start = x0, y0
        
        if len(points) < 2:
            hdg_start = 0 if hdg is None else hdg
            return RoadReferenceLine(x0_start, y0_start, hdg_start, [])

        x1, y1 = points[1].x, points[1].y
        deltax = x1 - x0_start
        deltay = y1 - y0_start
        hdg = np.arctan2(deltay, deltax) if hdg is None else hdg
        hdg_start = hdg

        geometry_elements = []
        referenceLine = RoadReferenceLine(x0_start, y0_start, hdg_start, geometry_elements)
        
        for point in points:
            x_end, y_end = point.x, point.y
            referenceLine.add_New_Point(x_end, y_end)
            referenceLine.set_endPoint(x_end, y_end)

        endpoint = points[-1]
        x_end, y_end = endpoint.x, endpoint.y
        referenceLine.set_endPoint(x_end, y_end)
        
        return referenceLine

    def addStraightLine(self, length):
        if length > 0:
            if not self.geometry_elements or isinstance(self.geometry_elements[-1], Arc):
                self.geometry_elements.append(StraightLine(length))
            else:
                self.geometry_elements[-1].length += length

    def addArc(self, length, Curvatur):
        if length > 0 and Curvatur not in [np.nan, np.inf]:
            if not self.geometry_elements or isinstance(self.geometry_elements[-1], StraightLine):
                self.geometry_elements.append(Arc(length, Curvatur))
            elif not isclose(self.geometry_elements[-1].Curvatur, Curvatur, abs_tol=1e-5):
                self.geometry_elements.append(Arc(length, Curvatur))
            elif Curvatur == 0:
                self.addStraightLine(length)
            else:
                self.geometry_elements[-1].length += length

    def add_New_Point(self, x_end, y_end):
        x0, y0, _ = self.get_endPoint()
        deltax1 = x_end - x0
        deltay1 = y_end - y0
        if deltax1 == 0 and deltay1 == 0:
            return

        hdg1 = np.arctan2(deltay1, deltax1)
        if self.hdg < 0:
            self.hdg += 2 * np.pi
        if hdg1 < 0:
            hdg1 += 2 * np.pi

        if isclose(self.hdg, hdg1, abs_tol=1e-3):
            length = np.sqrt(deltax1 * deltax1 + deltay1 * deltay1)
            self.addStraightLine(length)
        else:
            x_midel = x0
            y_midel = y0
            
            try:
                last_ele = self.geometry_elements.pop()
            
            except:
                pass
 
            
            x_start, y_start, hdg0 = self.get_endPoint()
            refnew = RoadReferenceLine.Connect3points(x_start, y_start, x_midel, y_midel, x_end, y_end )
            self.geometry_elements.extend(refnew.geometry_elements)
            self.set_endPoint(x_end, y_end)

    def getLength(self):
        return sum(ele.length for ele in self.geometry_elements)

    def Reverse(self):
        
        x0, y0, hdg = self.get_endPoint()
        
        self.geometry_elements.reverse()
        
        self.x0 = x0
        self.y0 = y0
        self.hdg =  -hdg
        
        
    def set_startPoint(self, X_start, Y_start):  
 
 
        
        S, _ = self.XY2ST(X_start, Y_start)
        
        if S is not None  and  S > 0:
            
            x0_end, y0_end, hdg_end = self.get_endPoint()
            
            
            Length = self.getLength()
            
            geometry_elements_copy =  copy.deepcopy(  self.geometry_elements )
            
            self.set_endPoint( X_start, Y_start)
            
            x0_start, y0_start, hdg_start = self.get_endPoint()
            
            self.geometry_elements  = geometry_elements_copy
            
            if Length > S:
                
                S0 = 0
                for ele in self.geometry_elements :
                    if ele.length < S - S0 :
                        S0 = S0 + ele.length 
                        ele.length = 0
                        
                    else:
                        
                        ele.length = ele.length - (S - S0 )
                        self.x0 = x0_start
                        self.y0 = y0_start
                        self.hdg = hdg_start
                        break
                    
                
            geometry_elements = []
            
            for ele in    self.geometry_elements:
                
                if  ele.length  >0:
                    geometry_elements.append(ele)
                     
                
            self.geometry_elements = geometry_elements
            
            
 
    def get_StartPoint(self):
        """
        获取参考线的起点坐标和航向角
        Returns:
            x0 (float): 起点x坐标
            y0 (float): 起点y坐标 
            hdg (float): 起点航向角
        """
        return self.x0, self.y0, self.hdg    

    def get_EndPoint(self):
        """
        获取参考线的终点坐标和航向角
        Returns:
            x0 (float): 终点x坐标 
            y0 (float): 终点y坐标
            hdg (float): 终点航向角
        """
        x0, y0, hdg = self.get_endPoint()
        return x0, y0
   
    def get_endPoint(self):
        x0, y0, hdg = self.x0, self.y0, self.hdg
        for ele in self.geometry_elements:
            x0, y0, hdg = ele.get_endPoint(x0, y0, hdg)
        return x0, y0, hdg

    def set_endPoint(self, X_end, Y_end):
        S, _ = self.XY2ST(X_end, Y_end)
        if S is not None and  S >= 0:
            S0 = 0
            indextoremove = []
            index = 0
            allextra = False
            
            if len(self.geometry_elements) > 1:
            
                for ele in self.geometry_elements[:-1]:
                    index += 1
                    if S0 + ele.length < S and not allextra:
                        S0 += ele.length
                    else:
                        indextoremove.append(index)
                        allextra = True
    
                indextoremove.sort(reverse=True)
                for index in indextoremove:
                    self.geometry_elements.pop(index)
    
                if S is not None and self.geometry_elements and (S - S0) > 0:
                    self.geometry_elements[-1].length = S - S0
                    
            else:
                self.geometry_elements[0].length = S
                
                

    def ST2XY(self, S, T):
        x0, y0, hdg = self.x0, self.y0, self.hdg
        S0 = 0
        ele = None
        for ele in self.geometry_elements:
            if S - S0 <= ele.length:
                return ele.ST2XY(x0, y0, hdg, S, S0, T)
            else:
                x0, y0, hdg = ele.get_endPoint(x0, y0, hdg)
                S0 += ele.length
        if ele is not None:
            return ele.ST2XY(x0, y0, hdg, S, S0, T)
        else:
            return S, T

    def XY2ST(self, X, Y):
        x0, y0, hdg = self.x0, self.y0, self.hdg
        S0 = 0
        S_list, T_list = [], []
        if len(self.geometry_elements) > 1:
            self.geometry_elements[-1].length *= 1.01
        for ele in self.geometry_elements:
            try:
                S, T = ele.XY2ST(x0, y0, hdg, X, Y, S0)
            except:
                S, T = None, None
            if S is not None and S >= 0 and (S - S0) <= ele.length:
                S_list.append(S)
                T_list.append(np.abs(T))
            x0, y0, hdg = ele.get_endPoint(x0, y0, hdg)
            S0 += ele.length
        if len(self.geometry_elements) > 1:
            self.geometry_elements[-1].length /= 1.01
        if T_list:
            indexMinT = np.argmin(T_list)
            T = T_list[indexMinT]
            S = S_list[indexMinT]
            return S, T
        else:
            return None, None

    def export2opendrive(self):
        geometry = []
        hdg, s, x, y = self.hdg, 0, self.x0, self.y0
        for geo_ele in self.geometry_elements:
            length = geo_ele.length
            if isinstance(geo_ele, StraightLine):
                geometry.append(opendrive.t_road_planView_geometry(hdg, length, s, x, y, line=opendrive.t_road_planView_geometry_line()))
            elif isinstance(geo_ele, Arc):
                curvature = geo_ele.Curvatur
                geometry.append(opendrive.t_road_planView_geometry(hdg, length, s, x, y, arc=opendrive.t_road_planView_geometry_arc(curvature)))
            s += length
            x, y, hdg = geo_ele.get_endPoint(x, y, hdg)
        planView = opendrive.t_road_planView(geometry)
        return planView
    
class RoadType():

    @classmethod
    def fromOSMdict(cls, dictobj):
        
        tags = dictobj.get('tags')
       
        return RoadType(tags)
    
    def __init__(self, tags):
        
        self.tags = tags

    def export2opendrive(self): 
        
        type_road_opendrive = opendrive.e_roadType.TOWN
        
        country = opendrive.e_countryCode_deprecated.GERMANY
        
        if "maxspeed" in self.tags.keys():
            
            # index = self.tags.index("maxspeed")
            try:
                maxspeed = int(self.tags["maxspeed"])
            except:
                
                if self.tags["maxspeed"] == 'none':
                
                    maxspeed = 130
                else:
                    maxspeed = 50
                               
        else:
            maxspeed = 30       
        
        speed = opendrive.t_road_type_speed(max=maxspeed, unit=opendrive.e_unitSpeed.KMH)
        s = 0
        type_list = opendrive.t_road_type(country, s   , type_road_opendrive, speed) 
        
        return type_list

class RoadSuperelevation():

 
    
    def __init__(self,s = 0, a= 0 ,b= 0, c = 0 ,d= 0) :
        
        self.s = s
        self.a = a
        self.b = b  
        self.c = c
        self.d = d
 
    
    def getSuperelevation(self, S):


        ds = S - self.s
        
        
        superelevation   = self.a + self.b*ds + self.c*ds*ds + self.d*ds*ds*ds 
    
        return superelevation     
    
    def export2opendrive(self): 

        superelevation =  opendrive.t_road_lateralProfile_superelevation(a=self.a, b=self.b, c=self.c, d=self.d, s=self.s) 
                
 
        return superelevation

class RoadLateralProfileShape():

 
    
    def __init__(self,s = 0,t = 0 , a= 0 ,b= 0, c = 0 ,d= 0) :
        
        self.s = s
        self.t = t
        self.a = a
        self.b = b  
        self.c = c
        self.d = d
 
 
    def getHshape(self, T):


        dt = T - self.t
        
        
        Hshape   = self.a + self.b*dt + self.c*dt*dt + self.d*dt*dt*dt 
    
        return Hshape  
 

    def export2opendrive(self): 

        lateralProfile_shape =  opendrive.t_road_lateralProfile_shape(a=self.a, b=self.b, c=self.c, d=self.d, s=self.s, t=self.t) 
                
 
        return lateralProfile_shape

class RoadLateralProfile():

    @classmethod
    def fromOSMdict(cls, tags, points):
       
        return RoadLateralProfile([RoadSuperelevation(s = 0 , a= 0 ,b= 0, c = 0 ,d= 0)], [RoadLateralProfileShape(s = 0,t = 0 , a= 0 ,b= 0, c = 0 ,d= 0)])

    
    def __init__(self, superelevationList , shapeList):

  
        self.superelevationList = superelevationList
        self.shapeList = shapeList

 

 

    def export2opendrive(self): 

        superelevation = []
        
        for ele in self.superelevationList:
            
            superelevation.append(ele.export2opendrive())
 
        shape = []
        
        
        for ele in self.shapeList:
            
            shape.append(ele.export2opendrive())        
        
        lateralProfile = opendrive.t_road_lateralProfile(superelevation, shape)
        
        return lateralProfile

class RoadElevationProfile():
 
    @classmethod
    def fromOSMdict(cls, tags, points):
 
        return RoadElevationProfile(a=0, b=0, c=0, d=0, s=0)
    
    def __init__(self, a=0, b=0, c=0, d=0, s=0):
        
        self.a = a
        self.b = b
        self.c = c
        self.d =  d        
        self.s = s
 

    def export2opendrive(self): 
        elevation = [ opendrive.t_road_elevationProfile_elevation(a=self.a, b=self.b, c=self.c , d=self.d, s=self.s)]
        elevationProfile = opendrive.t_road_elevationProfile(elevation) 
        
        return elevationProfile
    
class RoadLaneOffset():
    
    def __init__(self, a  , b , c  , d  , s):
        
        self.s = s 
        self.a = a
        self.b = b
        self.c = c
        self.d = d
    
    
    def getOffset(self, S):
        
 
        ds = S - self.s
        
        
        offset  = self.a + self.b*ds + self.c*ds*ds + self.d*ds*ds*ds 
    
        return offset
        
    def export2opendrive(self): 
        
        laneOffsetElement = opendrive.t_road_lanes_laneOffset(a=self.a, b=self.b, c=self.c, d=self.d , s=self.s)     
 
        return laneOffsetElement

class LaneLink():
    
    def __init__(self, predecessor , successor):
        
        self.predecessor = predecessor
        self.successor =successor

    def export2opendrive(self): 
        
        if self.predecessor is not None:
            
            predecessor = opendrive.t_road_lanes_laneSection_lcr_lane_link_predecessorSuccessor(id  = self.predecessor.get_lane_id())
         
        else:
            predecessor = None
               


        if self.successor is not None:
            
            successor = opendrive.t_road_lanes_laneSection_lcr_lane_link_predecessorSuccessor(id  = self.successor.get_lane_id())
         
        else:
            successor = None

        
        
        return  opendrive.t_road_lanes_laneSection_lcr_lane_link(predecessor, successor )
        
class LaneMark():
    
    def __init__(self, color , laneChange , material, sOffset , LaneMarkType , weight , width):
        
        self.color = color
        self.laneChange = laneChange
        self.material = material
        self.sOffset = sOffset
        self.LaneMarkType = LaneMarkType
        self.weight = weight
        self.width = width

    def export2opendrive(self): 
        
        roadMark_lane = opendrive.t_road_lanes_laneSection_lcr_lane_roadMark(color=self.color,
                                                                                    laneChange=self.laneChange,
                                                                                    material=self.material,
                                                                                    sOffset=str(self.sOffset),
                                                                                    type__attr=self.LaneMarkType,
                                                                                    weight=self.weight ,
                                                                                    width=str(self.width))
 
        return  roadMark_lane

class LaneWidth():
    
    def __init__(self, sOffset , a , b , c, d):
        
        self.sOffset = sOffset
        self.a = a
        self.b = b
        self.c = c
        self.d = d


    def getWidth(self, dS_section):
        
 
        ds = dS_section - self.sOffset
        
        
        Width  = self.a + self.b*ds + self.c*ds*ds + self.d*ds*ds*ds 
    
        return Width


    def export2opendrive(self): 
        
        lane_width = opendrive.t_road_lanes_laneSection_lr_lane_width(a=self.a, b=self.b, c=self.c, d=self.d  , sOffset=self.sOffset) 
 
        return  lane_width

class LaneHeight():


    def __init__(self, sOffset ,inner ,outer):
        
        self.sOffset = sOffset
        self.inner = inner
        self.outer = outer
 


    def export2opendrive(self): 
        
        lane_height = opendrive.t_road_lanes_laneSection_lr_lane_height(self.inner, self.outer, sOffset = self.sOffset)
 
        return  lane_height

class  WhiteBrokenLaneMark(LaneMark):
    
    def __init__(self, sOffset=0):
        
        color = opendrive.e_roadMarkColor.WHITE
        laneChange = opendrive.e_road_lanes_laneSection_lcr_lane_roadMark_laneChange.NONE
        material = "standard"
        sOffset = sOffset
        LaneMarkType = opendrive.e_roadMarkType.BROKEN       
        weight = opendrive.e_roadMarkWeight.STANDARD
        width = "1.1999999731779099e-01"
        
        LaneMark.__init__(self, color, laneChange, material, sOffset, LaneMarkType, weight, width)
        
class  WhiteSolidLaneMark(LaneMark):
    
    def __init__(self, sOffset=0):
        
        color = opendrive.e_roadMarkColor.WHITE
        laneChange = opendrive.e_road_lanes_laneSection_lcr_lane_roadMark_laneChange.NONE
        material = "standard"
        sOffset = sOffset
        LaneMarkType = opendrive.e_roadMarkType.SOLID       
        weight = opendrive.e_roadMarkWeight.STANDARD
        width = "1.1999999731779099e-01"
        
        LaneMark.__init__(self, color, laneChange, material, sOffset, LaneMarkType, weight, width)        
        
class  SidewalkCurbLaneMark(LaneMark):
    
    
    
    
    def __init__(self, sOffset=0):
        
        color = opendrive.e_roadMarkColor.STANDARD
        laneChange = opendrive.e_road_lanes_laneSection_lcr_lane_roadMark_laneChange.NONE
        material = "standard"
        sOffset = sOffset
        LaneMarkType = opendrive.e_roadMarkType.NONE       
        weight = opendrive.e_roadMarkWeight.STANDARD
        width = "0"
        
        LaneMark.__init__(self, color, laneChange, material, sOffset, LaneMarkType, weight, width)

class  RoadLane():
    
    def __init__(self,  laneType , laneWidths=[], laneMarks=[], laneHeights=[], laneLink=None , level=False , turn = None ):
 
        #self.LaneId = LaneId
        self.laneMarks = laneMarks
        self.laneWidths = laneWidths
        self.laneLink = laneLink
        self.laneType = laneType
        self.level = level
        self.laneHeights = laneHeights 
        
        self.lanSection = None
        self.turn = turn

    def get_lane_id(self):
        
        if self.lanSection is not None:
        
            return self.lanSection.get_lane_id(self)

        else:
            
            return None
    

    def getWidth(self, dS_section):
        
        
        laneWidth = None
        
        for laneWidthsele in self.laneWidths:
            
            if dS_section >= laneWidthsele.sOffset:
                laneWidth = laneWidthsele
                
            else:
                break 
            
        if  laneWidth is not None:
              
            return laneWidth.getWidth(  dS_section)
        
        else:
            return 0  
 

    def export2opendrive(self): 

        if self.laneLink is not None:
        
            link = self.laneLink.export2opendrive()
            
        else:
            link = None
            
            
        height = []
        for ele in self.laneHeights:
            height.append(ele.export2opendrive())            
 
        roadMark = []
        
        for ele in self.laneMarks:
            roadMark.append(ele.export2opendrive())
        
        width = []
        
        for ele in self.laneWidths:
            width.append(ele.export2opendrive())
        
        if self.level:
        
            level = "true"
        
        else:
            level = "false"
        
        lanetype = self.laneType     
        
        # opendrive.t_road_lanes_laneSection_center_lane(level, type_, link, border, width, roadMark, material, speed, access, height, rule, dataQuality, include, userData, id, gds_collector_)
        
        if self.LaneId == 0:
            
            center_lane = opendrive.t_road_lanes_laneSection_center_lane (level=level , id=self.LaneId , roadMark=roadMark , link=link)
 
            return center_lane   
        
        elif  self.LaneId > 0:  # left lane
            
            left = opendrive.t_road_lanes_laneSection_left_lane(level=level, type_=lanetype, link=link, width=width , id=self.LaneId  , roadMark=roadMark , height = height   ) 
            
            return left
            
        elif  self.LaneId < 0:  # right lane             
 
            right = opendrive.t_road_lanes_laneSection_right_lane(level=level, type_=lanetype, link=link, width=width , id=self.LaneId  , roadMark=roadMark  , height = height ) 
 
            return right        
    
    def draw(self, fig , ax , road , color = "k"):
 
        if road.ReferenceLine is not None  and self.LaneId != 0 :
            from matplotlib.patches import Polygon 
            #xs = []
            #ys = []
            
            
            befor = []
            after = []
            
        
            Length = road.ReferenceLine.getLength()
            for s in np.arange(0, Length    , .1):
        
                [[x_befor, y_befor] ,[x_after, y_after]] = road.roadLanes.get_lane_cross_section_coord(s , self.LaneId) 
                #xs.append(x_after)
                #ys.append(y_after)
                
                befor.append([x_befor, y_befor])
                after.append([x_after, y_after])
                
                
            [[x_befor, y_befor] ,[x_after, y_after]] = road.roadLanes.get_lane_cross_section_coord(Length , self.LaneId) 
            #xs.append( x_after)
            #ys.append( y_after)
        
 
 
 
 
            befor.append([x_befor, y_befor])
            after.append([x_after, y_after]) 
 
 
            if self.LaneId > 0:
                
                point1 = befor[0]
                point2 = after[0]
                point3 = after[1]
                point4 = befor[1]
                
                
                
                #center1 = [(point1[0] + point2[0] )/2 , (point1[1] + point2[1] )/2 ]
                #center2 = [(point3[0] + point4[0] )/2 , (point3[1] + point4[1] )/2 ]
                points_cord =[point1 ,point2 , point3 ,point4  ]
                p = Polygon(points_cord, facecolor="g" , alpha=1)  # facecolor=facecolor,
                ax.add_patch(p)                 
                 
                
                
            elif self.LaneId < 0:
                #center = befor[-1]
 
                point1 = befor[-1]
                point2 = after[-1]
                point3 = after[-2]
                point4 = befor[-2]
                           
                points_cord =[point1 ,point2 , point3 ,point4  ]
                p = Polygon(points_cord, facecolor="r" , alpha=1)  # facecolor=facecolor,
                ax.add_patch(p)            
                 
            
            after.reverse()
            points_cord = befor + after
            p = Polygon(points_cord, facecolor=color , alpha=.5)  # facecolor=facecolor,
            ax.add_patch(p)
    LaneId = property(get_lane_id, None, None, None)

class  DrivingLane(RoadLane):
    
    def __init__(self, laneType, laneWidths=[], laneMarks=[], laneHeights=[], laneLink=None, level=False , turn = None):
        RoadLane.__init__(self, laneType, laneWidths=laneWidths, laneMarks=laneMarks, laneHeights=laneHeights, laneLink=laneLink, level=level ,turn = turn  )
        
        
    def draw(self, fig, ax, road, color="k" ):
        RoadLane.draw(self, fig, ax, road, color  )    

class  RoadCurb (RoadLane):
    
    
    
    
 
    def __init__(self,  laneMarks=[], laneLink=None, level=False):
        
        laneType = opendrive.e_laneType.CURB
        laneWidths = [LaneWidth(sOffset=0, a=1.5239999999999998e-01, b=0, c=0, d=0)]
        laneHeights = [LaneHeight(sOffset = 0, inner = .15, outer = .15)]
        RoadLane.__init__(self,  laneType, laneWidths=laneWidths, laneMarks=laneMarks, laneHeights=laneHeights, laneLink=laneLink, level=level)

    
    
    def draw(self, fig, ax, road, color="r"):
        color="r"
        RoadLane.draw(self, fig, ax, road, color=color)
               
class  RoadSidewalk (RoadLane):

    def __init__(self,   laneMarks=[], laneLink=None, level=False , width = 2):
        
        laneType = opendrive.e_laneType.SIDEWALK
        laneWidths = [LaneWidth(sOffset=0, a=width, b=0, c=0, d=0)]
        laneHeights = [LaneHeight(sOffset = 0, inner = .15, outer = .15)]
        
        RoadLane.__init__(self,  laneType, laneWidths=laneWidths, laneMarks=laneMarks, laneHeights=laneHeights, laneLink=laneLink, level=level)


    def draw(self, fig, ax, road, color="y"):
        color="y"
        RoadLane.draw(self, fig, ax, road, color=color)

class  RoadCyclistsLane (RoadLane):

    def __init__(self,  laneMarks=[], laneLink=None, level=False , width = 2):
        
        laneType = opendrive.e_laneType.BIKING
        laneWidths = [LaneWidth(sOffset=0, a=width, b=0, c=0, d=0)]
        RoadLane.__init__(self,   laneType, laneWidths=laneWidths, laneMarks=laneMarks, laneLink=laneLink, level=level)

    def draw(self, fig, ax, road, color="b"):
        color="b"
        RoadLane.draw(self, fig, ax, road, color=color)

class  RoadCyclistsTrack (RoadLane):

    def __init__(self,  laneMarks=[], laneLink=None, level=False , width = 2):
        
        laneType = opendrive.e_laneType.BIKING
        laneWidths = [LaneWidth(sOffset=0, a=width, b=0, c=0, d=0)]
        laneHeights = [LaneHeight(sOffset = 0, inner = .15, outer = .15)]
        RoadLane.__init__(self,   laneType, laneWidths=laneWidths, laneMarks=laneMarks, laneLink=laneLink, laneHeights=laneHeights, level=level)

    def draw(self, fig, ax, road, color="b"):
        color="b"
        RoadLane.draw(self, fig, ax, road, color=color)
                
class  RoadLaneSection():
    
    def __init__(self, Leftlanes, Centerlane , Rightlanes , s= 0):
        
        self.Leftlanes = Leftlanes
        self.Centerlane = Centerlane
        self.Rightlanes = Rightlanes
        
        self.s =s
        
        
        self.Centerlane.lanSection = self
        
        for lane in self.Leftlanes:
            lane.lanSection = self
            
        for lane in self.Rightlanes:
            lane.lanSection = self           
        
    def get_lane_id(self, lane):

        if lane == self.Centerlane:
            return 0
        elif lane in self.Leftlanes:
            Leftlanes  = self.Leftlanes
            #LeftlanesCopy = Leftlanes.copy()
            #LeftlanesCopy.reverse()            
            
            #return len(self.Leftlanes) - self.Leftlanes.index(lane)+1  
            return Leftlanes.index(lane) + 1 
        elif lane in self.Rightlanes:
            return -1*self.Rightlanes.index(lane)-1

    def export2opendrive(self): 
        
        leftlist = []
        
        for lane in self.Leftlanes:
        
            leftlist.append(lane.export2opendrive())
        
        left = opendrive.t_road_lanes_laneSection_left(leftlist)
 
        center = opendrive.t_road_lanes_laneSection_center([self.Centerlane.export2opendrive()]) 
              
        rightlist = []
        
        for lane in self.Rightlanes:
        
            rightlist.append(lane.export2opendrive())
        
        right = opendrive.t_road_lanes_laneSection_right(rightlist)
              
        lansec = opendrive.t_road_lanes_laneSection(s=self.s, singleSide=False, left=left, center=center, right=right)
        
        return lansec
    
    def draw(self, fig , ax , road):
        
        
        
        color = "k"
        for lane in self.Leftlanes:
        
            lane.draw(fig , ax , road , color)
            
        self.Centerlane.draw(fig , ax , road )
        
        color = "k"
        for lane in self.Rightlanes:
                
            lane.draw(fig , ax , road , color  )        
              
class  RoadLanes():
 
    @classmethod
    def fromOSMdict(cls, tags, points , road):
 
 

        Leftlanes = []
        Rightlanes = []




        
        if isinstance(road, PedestrianRoad):
            if 'width' in tags:
 
                width = float( tags.get("width").replace("m" ,"" ).replace("," ,"." ) ) 
                if width > 3:
                    width = 3
 
            else:
                width = 2 
        
            a =   width/2  
            roadlaneOffset = RoadLaneOffset(a=a, b=0, c=0, d=0, s=0)                
        
            level = False
 
            laneLink = None
            laneMarks = []
        
            Centerlane = DrivingLane(  laneType=None, laneWidths=[], laneMarks=[], laneLink=None, level=False)   
            Rightlanes.append(RoadSidewalk(  laneMarks, laneLink, level , width))   
 
        elif  isinstance(road, CycleRoad):
            if 'width' in tags:
 
                width = float( tags.get("width").replace("m" ,"" ).replace("," ,"." ) )
                if width > 3:
                    width = 3  
            else:
                width = 2             
        
            a =   width/2  
            roadlaneOffset = RoadLaneOffset(a=a, b=0, c=0, d=0, s=0)  
        
            level = False
             
            laneLink = None
            laneMarks = []
        
            Centerlane = DrivingLane(  laneType=None, laneWidths=[], laneMarks=[], laneLink=None, level=False)    
            Rightlanes.append(RoadCyclistsLane( laneMarks, laneLink, level , width))   
        
        
        elif  isinstance(road, ServiceRoad): 
            if 'width' in tags:
 
                width = float( tags.get("width").replace("m" ,"" ).replace("," ,"." ) )
                if width > 3:
                    width = 3  
            else:
                width = 3.5  
        
            level = False
 
            laneLink = None
            laneMarks = [] 
        
            a =   width/2  
            roadlaneOffset = RoadLaneOffset(a=a, b=0, c=0, d=0, s=0)  
        
            Centerlane = RoadLane(  laneType=None, laneWidths=[], laneMarks=[], laneLink=None, level=False)   
            level = False
            laneWidths = [LaneWidth(sOffset=0, a=width , b=0 , c=0 , d=0) ]
            lanetype = "driving"
            Rightlanes.append(DrivingLane(  laneType=lanetype, laneWidths=laneWidths, laneMarks=[], laneLink=laneLink, level=level))
        
        else:
 
            if "turn:lanes" in tags:
                turnlist = tags.get("turn:lanes").split("|")
            else:
                turnlist =[]

            # tags = dictobj.get('tags')
            # points =[]   
            # for node in dictobj.get('nodes'):
            #
            #
            #     points.append(node) 
            highway = tags.get("highway")
            surface = tags.get("surface")
            maxspeed = tags.get("maxspeed")
            
            oneway = tags.get('oneway') == "yes"
            lanes = tags.get('lanes' , None) 
            add_sidewalk_left = False
            add_sidewalk_right = False
            
            
            add_cycleway_left = False
            add_cycleway_right = False
            
            if lanes is  not None:
                lanes = int(lanes)
            
            lanes_backward = tags.get('lanes:backward' , None) 
            
            if lanes_backward is  not None:
                lanes_backward = int(lanes_backward)
            
            lanes_forward = tags.get('lanes:forward' , None) 
    
            if lanes_forward is  not None:
                lanes_forward = int(lanes_forward)
            
            if lanes is  None  and   lanes_backward is None and  lanes_forward is None:
     
                
                if oneway:
                    lanes = 1
                    lanes_forward = 1
                else:
                    
                    if highway == 'residential':
                        lanes_backward = 1
                        lanes_forward = 1                
      
      
                    elif highway == 'living_street':
                        lanes_backward = 1
                        lanes_forward = 1    
    
                    elif highway == 'living_street':
                        lanes_backward = 1
                        lanes_forward = 1   
    
                    elif highway == 'pedestrian':
                        lanes_backward = 1
                        lanes_forward = 1   
                        
                        
                        if surface ==  'asphalt':
                            add_sidewalk_left = True
                            add_sidewalk_right = True                    
                    
                    elif maxspeed is not None:
                        lanes_backward = 1
                        lanes_forward = 1                     
                                        
                    else:
                    
                        lanes = 0
                        lanes_backward = 0
                        lanes_forward = 0
            
            if lanes_backward is None and  lanes_forward is None:
      
                if lanes == 1:
                        
                    oneway =  True
                
                if oneway:
                    lanes_forward = lanes
                    lanes_backward = 0
                
                else:
     
    
                    lanes_forward = int(lanes / 2) 
                    lanes_backward = lanes - lanes_forward
                    
                    
            if lanes_forward is None:
                lanes_forward = 0
                
            if lanes_backward is None:
                lanes_backward = 0            
                    
                    
            if 'width' in tags:
                
                ##print(tags)
                
                width = float( tags.get("width").replace("m" ,"" ).replace("," ,"." ) )
                
                if lanes_forward + lanes_backward == 0:
                    lanes_forward = 1
                    
                
                
                lane_width = width / (lanes_forward + lanes_backward) 
                
                
                
                
            else:
                lane_width = 3.5 
            
            
            if lane_width > 10 :
                lane_width = 10
                    
            cycleway_right = tags.get('cycleway:right') 
            cycleway_left = tags.get('cycleway:left')   
            cycleway_both = tags.get('cycleway:both')
            cycleway = tags.get('cycleway' )
            
             
            maxspeed = tags.get('maxspeed' , None)  
            
            sidewalk = tags.get('sidewalk' , None)  
       
            sidewalk_left = tags.get('sidewalk:left' , None)   
            sidewalk_right = tags.get('sidewalk:right' , None)
            sidewalk_both = tags.get('sidewalk:both' , None)
            
            
            surface= tags.get("surface")
            #surface = tags.get('asphalt' , None)    
            turn_lanes = tags.get('turn:lanes' , None) 
            lit = tags.get('lit' , None)
            

            
  
            
            
            if sidewalk_left in ["yes","use_sidepath","separate","lane"]:
                add_sidewalk_left = True
            
            elif  sidewalk in   [  "both" , "left", "yes"]:
                 
                add_sidewalk_left = True
    
            elif  sidewalk ==  "left" :
                 
                add_sidewalk_left = True
    
                 
            elif  sidewalk_both  ==   "separate"  :
                 
                add_sidewalk_left = True
                
             
            if   cycleway_right in   ['lane' ]:
                add_cycleway_right = True
                
               
             
            if   cycleway_left in    ['lane' ]:
                add_cycleway_left = True                             
    
    
    
            if   cycleway_both in   ['lane' ]:
                add_cycleway_right = True 
                add_cycleway_left = True  
                
                
            if   cycleway  in   ['lane' ]:
                
                if oneway:
                    add_sidewalk_right = True
                else:
                    add_sidewalk_right = True
                    add_cycleway_left = True 
                    
                
            
            
            if sidewalk_right in ["yes","use_sidepath","separate","lane"]:
                add_sidewalk_right = True
            
            elif  sidewalk in   [  "both","right", "yes"]:
                 
                add_sidewalk_right = True
    
            elif  sidewalk  == "right" :
                 
                add_sidewalk_right = True
    
    
    
            elif  sidewalk_both ==   "separate" :
                 
                add_sidewalk_right = True
                
            
     
            if lanes_forward is not None:
    
                for i in range(0,  lanes_forward  , 1):
        
                    level = False
                    laneWidths = [LaneWidth(sOffset=0, a=lane_width , b=0 , c=0 , d=0) ]
                    link = None  # opendrive.t_road_link( )
                    lanetype = "driving"

                    turn = None
                    if len(turnlist)    > 0:

                        if i < len(turnlist):
                            turn = turnlist[i]
                        else:
                            turn = None


                    
                    if   surface == "asphalt":
                    
                        if  i < lanes_forward -1  or add_cycleway_right  :
 
                            Rightlanes.append(DrivingLane(  laneType=lanetype, laneWidths=laneWidths, laneMarks=[ WhiteBrokenLaneMark(0)  ], laneLink=link, level=level , turn= turn))
                        else:
                            
                            Rightlanes.append(DrivingLane(  laneType=lanetype, laneWidths=laneWidths, laneMarks=[ ], laneLink=link, level=level , turn= turn))                    
                        
                    else:
                        Rightlanes.append(DrivingLane(  laneType=lanetype, laneWidths=laneWidths, laneMarks=[], laneLink=link, level=level , turn= turn) )
    
    
    
            if add_cycleway_right:
                level = False
            
                laneLink = None
                laneMarks = [SidewalkCurbLaneMark(0)  ]
                Rightlanes.append(RoadCyclistsLane( laneMarks  , laneLink, level))
            
            if add_sidewalk_right:
                level = False
                 
                laneLink = None
    
                laneMarks = [SidewalkCurbLaneMark(0)]
                Rightlanes.append(RoadCurb(  laneMarks, laneLink, level))
                
                if   cycleway_right in   ['track' ]   or  cycleway_both in   ['track' ] or  cycleway  in   ['track' ]  :
                    level = False
                
                    laneLink = None
                    laneMarks = []
                    Rightlanes.append(RoadCyclistsTrack( laneMarks  , laneLink, level))            
                
    
                
     
                laneLink = None
    
                laneMarks = [SidewalkCurbLaneMark(0)]
                Rightlanes.append(RoadSidewalk(  laneMarks, laneLink, level))            
            
            
    
            

   
    
    
      
    
            if lanes_backward is not None:
    
                for i in range(0,lanes_backward, 1):
        
                    level = False
                    laneWidths = [LaneWidth(sOffset=0, a=lane_width , b=0 , c=0 , d=0) ]
                    link = None  # opendrive.t_road_link( )
                    lanetype = "driving"
                    if   surface == "asphalt":
                        if i < lanes_backward -1 or  add_cycleway_left:
 
                            Leftlanes.append(DrivingLane(  laneType=lanetype, laneWidths=laneWidths, laneMarks=[ WhiteBrokenLaneMark(0) ], laneLink=link, level=level))                   
                        else:
                            Leftlanes.append(DrivingLane(  laneType=lanetype, laneWidths=laneWidths, laneMarks=[ ], laneLink=link, level=level))
            
                    else:
                        
                        Leftlanes.append(DrivingLane(  laneType=lanetype, laneWidths=laneWidths, laneMarks=[  ], laneLink=link, level=level))        
            

    
            if add_cycleway_left:
                level = False
            
                laneLink = None
                laneMarks = [SidewalkCurbLaneMark(0)  ]
                Leftlanes.append(RoadCyclistsLane(  laneMarks  , laneLink, level))    

            
    
    
            if add_sidewalk_left:
                level = False
     
                laneLink = None
    


                
     
                laneLink = None
    
                laneMarks = [SidewalkCurbLaneMark(0)]
                
                
                Leftlanes.append(RoadCurb(  laneMarks, laneLink, level))
     
                if   cycleway_left in   ['track' ] or  cycleway_both in   ['track' ] or  cycleway  in   ['track' ] :
                    level = False
                
                    laneLink = None
                    laneMarks = [ ]
                    Leftlanes.append(RoadCyclistsTrack( laneMarks  , laneLink, level))  
                     
                laneMarks = [SidewalkCurbLaneMark(0)]
                
                Leftlanes.append(RoadSidewalk(  laneMarks, laneLink, level)) 
      
                 
            
            if oneway:
                Centerlane = DrivingLane(  laneType=None, laneWidths=[], laneMarks=[], laneLink=None, level=False) 
                if lanes_forward == 1:
                    a =   lane_width *  (    lanes_forward   )/2.0  
                    
                    
                     
                else:
                    a =   lane_width *  int( (    lanes_forward +1  )/2.0 ) 
                    
 
                     
                roadlaneOffset = RoadLaneOffset(a=a, b=0, c=0, d=0, s=0)
            
            else:
                roadlaneOffset = RoadLaneOffset(a=0, b=0, c=0, d=0, s=0)
    
                if surface == "asphalt":
                
                    Centerlane = DrivingLane(  laneType=None, laneWidths=[], laneMarks=[WhiteSolidLaneMark(0)], laneLink=None, level=False)
                
                else:
                    Centerlane = DrivingLane(  laneType=None, laneWidths=[], laneMarks=[], laneLink=None, level=False)          
    
        if "turn:lanes" in tags:
            turnlist = tags.get("turn:lanes").split("|")
            print(turnlist)    
            print("Leftlanes" ,  len(Leftlanes))
            print("Rightlanes" ,  len(Rightlanes))
        roadsection = RoadLaneSection(Leftlanes, Centerlane, Rightlanes , 0)
        RoadLaneOffsetList = [roadlaneOffset]
        RoadLaneSectionLis = [roadsection]
 
        return RoadLanes(RoadLaneOffsetList, RoadLaneSectionLis , road)
    
    def __init__(self, RoadLaneOffsetList, RoadLaneSectionList , road):
 
        self.RoadLaneOffsetList = RoadLaneOffsetList
 
        self.RoadLaneSectionList = RoadLaneSectionList#
        
        
        self.road = road




    def get_offset(self , S  ): 
        
        
        laneOffset = None
 
        
        for laneOffsetele in self.RoadLaneOffsetList:
            
            if S >= laneOffsetele.s:
                laneOffset = laneOffsetele
                
            else:
                break
            
 

        if laneOffset is None:
            
            Offset = 0
            
        else:
            
 
            
            Offset = laneOffset.getOffset( S)
            
 
 
        return Offset





    def get_lane_width(self , S , LaneId): 
        
        
 
        laneSection= None
        
 

        for laneSectionele in self.RoadLaneSectionList:
            
            if S >= laneSectionele.s:
                laneSection = laneSectionele
                
            else:
                break
            
 
            
        if laneSection is not None:
            
            dS_section =  S - laneSection.s
            
            
            Rightlanes  = laneSection.Rightlanes
            Leftlanes  = laneSection.Leftlanes
            if  LaneId  < 0   :
                Laneindex = abs(LaneId) -1
                if Laneindex <= len(Rightlanes) -1 :
                    lane = Rightlanes[Laneindex]
                    width =   lane.getWidth( dS_section)
 
            elif  LaneId  > 0  :
                 
                
                Laneindex=    LaneId  - 1  
                if Laneindex <=  len(Leftlanes) -1 :
                    lane = Leftlanes[Laneindex]
                    width =   lane.getWidth( dS_section)
 
                    
                else:
                    width = 0
                    
                      
                
            else:
                width = 0
                
        else:
            
            width = 0
            
 
             
               
        
        return width



 
    def get_lane_cross_section_coord(self , S , LaneId): 
        
 
        laneSection= None
        
 
            


        for laneSectionele in self.RoadLaneSectionList:
            
            if S >= laneSectionele.s:
                laneSection = laneSectionele
                
            else:
                break
            
         
         
            
 
 
            
        Offset = self.get_offset( S)
            
 
        
        width_befor = 0
        width_after = 0             
          
        
            
        if laneSection is not None:
            
            dS_section =  S - laneSection.s
 
            if  LaneId  < 0 :
 
                Laneindex = abs(LaneId) -1
                for i in range(-1, -1*(Laneindex+ +2) , -1 ):
                    LaneId =  i  
                    laneWidth = self.get_lane_width(S, LaneId)
                    width_befor = width_after
                    width_after = width_after + laneWidth
                    
                
 
 
            elif  LaneId  > 0 :
 
                Laneindex =  LaneId -1  
                
                for i in range(  1 , Laneindex+2,  1  ) :
                    LaneId =  i  
                    laneWidth = self.get_lane_width(S, LaneId)
                    width_befor = width_after
                    width_after = width_after + laneWidth  
                   
 
    
                
            else:
                
                width_befor = 0
                width_after = 0
                
        else:
            
            width_befor = 0
            width_after = 0  
            
            
                   

        if LaneId  < 0 :
            width_befor = Offset - width_befor
            width_after = Offset - width_after
            
        else:
        
            width_befor = Offset + width_befor
            width_after = Offset + width_after        
        
        x_befor, y_befor = self.road.ReferenceLine.ST2XY(S, width_befor )
        x_after, y_after = self.road.ReferenceLine.ST2XY(S, width_after )
             
               
        
        return [[x_befor, y_befor] ,[x_after, y_after]]
        
        
        
        
            
            
        
        
        
        
            
 
        

    def export2opendrive(self): 
        
        laneOffset = []
        
        for roadLaneOffset  in self.RoadLaneOffsetList:
 
            laneOffset.append(roadLaneOffset.export2opendrive())  
         
        laneSection = []  
        
        for roadLaneSec in self.RoadLaneSectionList:
            laneSection.append(roadLaneSec.export2opendrive())          
        
        lanes = opendrive.t_road_lanes(laneOffset=laneOffset, laneSection=laneSection)    
        
        return   lanes  
 
    
    
    
    
    
    def draw(self, fig , ax , road):
        
        for roadLaneSec in self.RoadLaneSectionList:
            roadLaneSec.draw(fig , ax, road)
     
     
     
    def  getRoad_cross_section_coord(self,S):
        
        
        laneSection= None
        
 


        for laneSectionele in self.RoadLaneSectionList:
            
            if S >= laneSectionele.s:
                laneSection = laneSectionele
                
            else:
                break
            
        
        
        if len(laneSection.Leftlanes) > 0:
            lanIdLeft =  laneSection.Leftlanes[0].LaneId       

        else:
            
            lanIdLeft = 0
            

        if len(laneSection.Rightlanes) > 0:
            lanIdRight =  laneSection.Rightlanes[-1].LaneId       

        else:
            
            lanIdRight = 0
            
            
        [[_, _] ,[x_after_Left, y_after_Left]] = self.get_lane_cross_section_coord(S, lanIdLeft)

        [[_, _] ,[x_after_Right, y_after_Right]] = self.get_lane_cross_section_coord(S, lanIdRight)
       
         
        return [[x_after_Right, y_after_Right] , [x_after_Left, y_after_Left]]
 
class  RoadLinkPredecessorSuccessor(): 
    
    def __init__(self, PredecessorSuccessor  , contactPoint):
        
        self.PredecessorSuccessor = PredecessorSuccessor
        self.contactPoint = contactPoint
 
 
 
    def   export2opendrive(self):
        elementId = self.PredecessorSuccessor.getId()
        elementS = None #0
        
        if isinstance(self.PredecessorSuccessor , DrivingRoad ):
        
            elementType = opendrive.e_road_link_elementType.ROAD.value 
         
        elif isinstance(self.PredecessorSuccessor , Junction ):
        
            elementType = opendrive.e_road_link_elementType.JUNCTION.value  
            
        else:
            elementType = opendrive.e_road_link_elementType.ROAD.value 
           
        elementDir = None
        
        ele = opendrive.t_road_link_predecessorSuccessor(self.contactPoint, elementDir, elementId, elementS, elementType )
        
        
        return ele
 
class  RoadLink():
    
    def __init__(self,  Predecessor ,  Successor , road  ):
        
        
        
        self.Predecessor = Predecessor
        self.Successor = Successor
 
        self.predecessorLink = None
        self.successorLink   = None
        self.road            = road
        
    
    
    def update(self):
        

        if self.road is not None:
            if len(self.road.points) > 0 :
    
                start = self.road.points[0]
                end =  self.road.points[-1]
            
                if self.Predecessor is not None:
                
                    if len(self.Predecessor.points) > 0 :
                        Predecessor_start =  self.Predecessor.points[0]
                        Predecessor_end   =  self.Predecessor.points[-1]  
                    
                        contactPoint =None
                    
                        if start == Predecessor_end:
                    
                            contactPoint = opendrive.e_contactPoint.END.value 
                             
                        elif start == Predecessor_start:
                            contactPoint = opendrive.e_contactPoint.START.value 
                            
                    
                        if contactPoint is not None:
     
                            self.predecessorLink = RoadLinkPredecessorSuccessor(PredecessorSuccessor =  self.Predecessor, contactPoint =contactPoint )
 
                if self.Successor is not None:
                    
                    
                    if len(self.Successor.points) > 0 :
                    
                        Successor_start =  self.Successor.points[0]
                        Successor_end   =  self.Successor.points[-1]
                        contactPoint =None
                    
                    
                        if end == Successor_start:
                            
                            contactPoint = opendrive.e_contactPoint.START.value
                        elif end == Successor_end:
                            contactPoint = opendrive.e_contactPoint.END.value
                            
                    
                    
                        if contactPoint is not None:
                  
                            self.successorLink = RoadLinkPredecessorSuccessor(PredecessorSuccessor =  self.Successor, contactPoint =contactPoint )
 
 
    def   export2opendrive(self):
        
        
        if self.predecessorLink is not None:
            predecessor = self.predecessorLink.export2opendrive()
            
        else:
            predecessor = None    
        
        
        if self.successorLink is not None:
        
            successor = self.successorLink.export2opendrive()
        else:
            successor = None          
        
        roadlink = opendrive.t_road_link(predecessor, successor )


        return roadlink
         
class  Road():
 
 
    def __init__(self , points , tags , relvantnodes ):

        self.relvantnodes = relvantnodes


 
        self.points = []
        for point in points:
            point.add_Reference(self)
            self.points.append(point)
 
 
        self.tags = tags 
        name = self.tags.get('name' , "None").translate(special_char_map)
        name.encode().decode('unicode-escape')
        
        self.name = re.sub(r'\W+', '', name)
        
        
        ReferenceLine = RoadReferenceLine.fitRoadReferenceLine(points)
        
        roadType = [RoadType(tags)]
        roadLateralProfile = RoadLateralProfile.fromOSMdict( tags,  points)
        roadElevationProfile = RoadElevationProfile.fromOSMdict( tags,  points)
        roadLanes = RoadLanes.fromOSMdict( tags, points, self) 
        link = RoadLink(Predecessor = None, Successor= None , road = self)
        
        
        
        
        self.ReferenceLine = ReferenceLine 
        
 

        self.roadType = roadType
        self.roadLateralProfile = roadLateralProfile
        self.roadElevationProfile = roadElevationProfile
        self.roadLanes = roadLanes
        
 
        
        self.junction = None
        self.link = link

 
    
    def getId(self):
        
        if self in Scenery.get_instance().Roads:
 
            allelements = Scenery.get_instance().Roads + Scenery.get_instance().Junctions
            return  allelements.index(self)    #返回索引就是返回的一个数字，一个ID
        
        else:
            return None
        
        
    def update_ReferenceLines(self):
        
 
        if self.link.Predecessor is not None  or  self.link.Successor is not None:  
        
            PredecessorPoints = []
        
            if self.link.Predecessor is not None :
                PredecessorPoints = self.link.Predecessor.points.copy()
        
        
            SuccessorPoints = []
        
            if self.link.Successor is not None:
                SuccessorPoints = self.link.Successor.points.copy()
        
        
            points = self.points.copy()
        
            point_start = points[0]
            point_End = points[-1]
 
            if len(PredecessorPoints) > 0 :
 
            
                if point_start == PredecessorPoints[-1]:
                    points = PredecessorPoints + points   
            
 
            if len(SuccessorPoints) > 0 :
 
            
                if point_End == SuccessorPoints[0]:
            
                    points =  points +SuccessorPoints 
            
            
 
        
        
            fitpoints = []
        
            for point in points:
                if point not in fitpoints:
                    fitpoints.append(point)
        
        
            self.ReferenceLine = RoadReferenceLine.fitRoadReferenceLine(fitpoints)
        
 
            
            self.ReferenceLine.set_startPoint(point_start.x, point_start.y)
            self.ReferenceLine.set_endPoint(point_End.x, point_End.y)              
            

        else:
            self.ReferenceLine = RoadReferenceLine.fitRoadReferenceLine(self.points)
        
 
    def draw_way(self, fig , ax): 
 
        self.roadLanes.draw(fig , ax, self)
 

    def export2opendrive(self): 
        
        if self.junction  is None:
        
            junction = "-1"
        
        else:
            junction = self.junction.getId()
            
        
        if self.ReferenceLine  is not None:
            length = self.ReferenceLine.getLength()
            planView = self.ReferenceLine.export2opendrive()
            
        else:
            
            length = 0
            planView = None 
 
        lateralProfile = self.roadLateralProfile.export2opendrive()
        elevationProfile = self.roadElevationProfile.export2opendrive()
        roadType = []
        
        for obj in self.roadType:
            
            roadType.append(obj.export2opendrive())
        lanes = self.roadLanes.export2opendrive() 
        
        rule = opendrive.e_trafficRule.RHT
        
        if self.link is not None:
            
            roadlink = self.link.export2opendrive()
            
        else:
            roadlink =None
        
        
        
        name =   self.name 
        
        return opendrive.t_road(id=self.getId(),name =name,  junction=junction, length=length, planView=planView , lanes=lanes , elevationProfile=elevationProfile , lateralProfile=lateralProfile , rule=rule , type_=roadType , link = roadlink)          



    def update(self):
 

                     



        self.link.update()
        
        if len(self.points) > 0:
            self.update_ReferenceLines()


    
    def getLength(self):
        
        return self.ReferenceLine.getLength()
    
    
    def getWidth_coord(self,S):
        return self.roadLanes.getRoad_cross_section_coord( S)
    
 
         
class  DrivingRoad(Road):
    
    
    def __init__(self, points, tags , relvantnodes):
        Road.__init__(self, points, tags, relvantnodes)
 
 
    
    def draw_way(self, fig, ax):
        Road.draw_way(self, fig, ax)    

class  Bridge(Road):
    
    
    
    def __init__(self, points, tags , relvantnodes):
        Road.__init__(self, points, tags, relvantnodes)
        
        self.roadElevationProfile.a = 1
    
    def draw_way(self, fig, ax):
        Road.draw_way(self, fig, ax)
        
        
    
    def export2opendrive(self):
        opendriveobj = Road.export2opendrive(self)
        
        
        bridgeid = str(self.getId()) + "_Bridge"
        
        length = self.getLength()
        
        name = self.name
        
        s = 0
        
        type_ = opendrive.e_bridgeType.CONCRETE
        
        bridge = opendrive.t_road_objects_bridge(bridgeid, length, name, s, type_ )
        
        opendriveobj.objects = opendrive.t_road_objects( bridge = [bridge] )
        
    
        return opendriveobj
    
class  Tunnel(Road):
    
    
    def __init__(self, points, tags , relvantnodes):
        Road.__init__(self, points, tags, relvantnodes)
        
        self.roadElevationProfile.a = -5
        
    
    def draw_way(self, fig, ax):
        Road.draw_way(self, fig, ax)


    def export2opendrive(self):
        opendriveobj= Road.export2opendrive(self)
        
        
        Tunnelid = str( self.getId() ) + "_Tunnel"
        
        length = self.getLength()
        
        name = self.name
        
        s = 0
        
        type_ = opendrive.e_bridgeType.CONCRETE
        
        daylight = 1
        lighting = 1
        
        tunnel = opendrive.t_road_objects_tunnel(daylight, Tunnelid, length, lighting, name, s, type_ )
        
        opendriveobj.objects = opendrive.t_road_objects( tunnel = [tunnel] )
        
    
        return opendriveobj

class  PedestrianRoad(LineObject):
    
    def __init__(self, points, tags, relvantnodes, Width=2):
        LineObject.__init__(self, points, tags, relvantnodes, Width=Width)
        

    def draw_way(self, fig, ax, color="y"):
        LineObject.draw_way(self, fig, ax, color=color)    
    
    # def __init__(self, points, tags , relvantnodes):
    #     Road.__init__(self, points, tags, relvantnodes)
    #
    # def draw_way(self, fig, ax):
    #     Road.draw_way(self, fig, ax)
    #

class  CycleRoad(LineObject):
    
    
    def __init__(self, points, tags, relvantnodes, Width=2):
        LineObject.__init__(self, points, tags, relvantnodes, Width=Width)
        

    def draw_way(self, fig, ax, color="b"):
        LineObject.draw_way(self, fig, ax, color=color)
    
    
    # def __init__(self, points, tags , relvantnodes):
    #     Road.__init__(self, points, tags, relvantnodes)
    #
    # def draw_way(self, fig, ax):
    #     Road.draw_way(self, fig, ax)

class  ServiceRoad(LineObject):
    

    def __init__(self, points, tags, relvantnodes, Width=3):
        LineObject.__init__(self, points, tags, relvantnodes, Width=Width)
        

    def draw_way(self, fig, ax, color="k"):
        LineObject.draw_way(self, fig, ax, color=color)
    
    # def __init__(self, points, tags , relvantnodes):
    #     Road.__init__(self, points, tags, relvantnodes)
    #
    # def draw_way(self, fig, ax):
    #     Road.draw_way(self, fig, ax)

class  Railway(LineObject):
    
 
    def __init__(self, points, tags, relvantnodes):
        
        Width=3 
        LineObject.__init__(self, points, tags, relvantnodes, Width=Width)
 
    

    def draw_way(self, fig, ax):
        LineObject.draw_way(self, fig, ax, color='r') 

class  JunctionConnectionLaneLink():


    def __init__(self, fromLane , toLane):
        self.fromLane = fromLane
        self.toLane = toLane
        
        
          

    def export2opendrive(self):
        
        fromLane = self.fromLane.get_lane_id()
        toLane = self.toLane.get_lane_id()
        
        conxml = opendrive.t_junction_connection_laneLink(fromLane , toLane ) 
        
        
        return conxml
        
class  JunctionConnection():
    
    
    def __init__(self,junction , incomingRoad , connectingRoad , contactPoint , ConnectionlaneLinks ):
        self.junction = junction
        self.incomingRoad =incomingRoad
        self.connectingRoad = connectingRoad
        self.contactPoint = contactPoint
        self.ConnectionlaneLinks = ConnectionlaneLinks



    def getId(self):
        
        return  self.junction.Connections.index(self)

    
    def export2opendrive(self): 
        conid = self.getId()
        contactPoint = self.contactPoint
        incomingRoad = self.incomingRoad.getId()
        connectingRoad = self.connectingRoad.getId()
        
        linkedRoad = None
        
        type_ = None
        
        predecessor = None
        successor = None
        
        laneLink =[]
        
        for link in self.ConnectionlaneLinks:
            laneLink.append(link.export2opendrive())
             
        
        
        
        conxml = opendrive.t_junction_connection(connectingRoad, contactPoint, conid, incomingRoad, linkedRoad, type_, predecessor, successor, laneLink )
        
        return conxml

class  Junction(): 
 

    def __init__(self,  IncommingRoads):
        
  
        
        self.IncommingRoads =IncommingRoads
        
        self.Connections = []
 
        self.JunctionRoads = [] 
 
 
    def update(self ):      #更新路口信息

        RoadsList = []  
        
        #widthlist = []
        
        for road in self.IncommingRoads: #获取路口的所有连接道路
           
            if road.getId() is not None:  #如果道路的id不为空
                
                RoadsList.append(road)  #将道路添加到道路列表中
 
                
        
        
        
        
        for road in self.JunctionRoads:   #获取路口的所有连接道路
            
            if road in Scenery.get_instance().Roads:  #如果道路在道路列表中
                Scenery.get_instance().Roads.remove(road)   #将道路从道路列表中移除
                    
            
        
        
        self.Connections = []  #清空路口的连接道路
        
        self.JunctionRoads =[]  #清空路口的连接道路
        
        roaddict = {}        #创建一个字典
        
        
 
        for road in RoadsList:  
            
            pointscoord = []  #程序运行结束后，包含了除当前道路外其他道路的起点终点

            for other_road in RoadsList:  
 
                
                if road != other_road:  
                    
                    pointscoord.append([ other_road.points[0].x , other_road.points[0].y]  )  #获取每一条道路的起点终点
                    pointscoord.append([ other_road.points[-1].x , other_road.points[-1].y]  )
                    
            
            start = road.points[0]
            end = road.points[-1]
            
            
            roadpoints = [[ start.x , start.y]   , [ end.x , end.y]] #当前道路的起点终点
            
            
            selctions =[]
            
            for point in pointscoord:
                
                closest_point = utilities.find_closest_point(roadpoints ,point )  #其余道路的起点终点与当前道路的起点终点进行比较，找到其余道路距离目标点最近的点
                
                if closest_point == roadpoints[0]:
                    selctions.append(start)
                    
                else:
                    selctions.append(end)
                    
              
            if len( selctions ) > 0  :    
                Connection_point = utilities.most_common(selctions)    
                    
                roaddict[str(road)] = Connection_point #键值对
            
 
        roaddictNewConnection = {}
        
        for road in RoadsList:         #Roadlist存储的是所以道路的起点和终点
        
            Connection_point = roaddict.get(str(road)) 
 
            if road.points[0] == Connection_point:
                Road_Connection = "start"
                #S_Road = 0
            
            else:
                Road_Connection = "end"
                #S_Road = road.getLength()
                
                
            roaddictNewConnection[str(road)] = 0  
            
            roadlength  = road.getLength() 
            
            road_leftline =[]
            road_rightline =[]

           
 
            
            for s in np.arange(0, roadlength + 1  , 1):
                
                [[x_after_Right, y_after_Right] , [x_after_Left, y_after_Left]] =  road.getWidth_coord(s ) 
                
                road_leftline.append([x_after_Left, y_after_Left])
                road_rightline.append([x_after_Right, y_after_Right])
                
  
                   
                                  
 
 
            for otherRoad in    RoadsList:
                
                if  road !=    otherRoad:
                    
                    other_Connection_point = roaddict.get(str(otherRoad)) 
                    
                    

                    if otherRoad.points[0] == other_Connection_point:  #如果其他道路的起点等于起点
                        #otherRoad_Connection = "start"
                        S = 0
                    
                    else:
                        #otherRoad_Connection = "end"
                        S = otherRoad.getLength()
                    
                    
                    
                    [[x_after_Right, y_after_Right] , [x_after_Left, y_after_Left]] =  otherRoad.getWidth_coord(S ) 
                    
                    S1 , _ = road.ReferenceLine.XY2ST(x_after_Right, y_after_Right)
                    S2 , _ = road.ReferenceLine.XY2ST(x_after_Left, y_after_Left)
                    
                    for S in [S1 ,S2]:
                        if S is not None:
 
                            if Road_Connection == "start":
                                
                                Distance =  S
                 
                            else:
                                Distance = roadlength - S
 

                            roaddictNewConnection[str(road)] = max(roaddictNewConnection[str(road)] , Distance )
                        
                   
                    
                    

                    otherRoad_leftline =[]
                    otherRoad_rightline =[]


                    Length = otherRoad.getLength()
                    for s in np.arange(0, Length + 1  , 1):
                        
                        [[x_after_Right, y_after_Right] , [x_after_Left, y_after_Left]] =  otherRoad.getWidth_coord(s ) 
                        
                        otherRoad_leftline.append([x_after_Left, y_after_Left])
                        otherRoad_rightline.append([x_after_Right, y_after_Right])



                    otherRoad_Predecessor_road_leftline = []
                    otherRoad_Predecessor_road_rightline = []
        
                    otherRoad_Successor_road_leftline = []
                    otherRoad_Successor_road_rightline = []  
                        
 
                    
                    for line1  in [road_leftline ,road_rightline ]:
                        for line2  in [otherRoad_leftline ,otherRoad_rightline , otherRoad_Predecessor_road_leftline , otherRoad_Predecessor_road_rightline ,otherRoad_Successor_road_leftline , otherRoad_Successor_road_rightline  ]:
                            
                            if len(line1 ) > 0 and len(line2) >0 :
                            
                                try:
                                    point = utilities.intersectionPoint(line1, line2)
        
                                    if  point is not None:
                                        
                                        S, _ = road.ReferenceLine.XY2ST(point[0] ,point[1])
                                        
                                        if S is not None:
                                            
                                            if Road_Connection == "start":
                                                
                                                Distance =  S
                                 
                                            else:
                                                Distance = roadlength - S
                                                
                                            roaddictNewConnection[str(road)] = max(roaddictNewConnection[str(road)] , Distance )    
                                    
 
                                except:
                                    
                                    pass
                        
 
        #print("############")
        for road in RoadsList:
            Distance = roaddictNewConnection.get(str(road))
            Connection_point = roaddict.get(str(road))
            
            length  = road.getLength()
            
            if road.points[0] == Connection_point:
                Road_Connection = "start"
 
            else:
                Road_Connection = "end"
                
 
            
            Distance = Distance *1.2
 
 
            if Distance >= length*.49 :
            
                Distance =  length*.49
 
        
            if Distance >= 30 :
                
                Distance =  30
            
  
            
            roaddictNewConnection[str(road)] = Distance 
            

        
        for road in RoadsList:
        
        
            Connection_point = roaddict.get(str(road)) 
        
            if road.points[0] == Connection_point:
                Road_Connection = "start"
        
            else:
                Road_Connection = "end"
        
        
            Distance = roaddictNewConnection.get(str(road))
        
            length  = road.getLength()  
        
            #print(road.Predecessor)
            #print(road.Successor)
        
        
        
            if Road_Connection == "start":
                S = Distance*3/10
                x, y = road.ReferenceLine.ST2XY(S , 0)
                road.ReferenceLine.set_startPoint(x, y)
        
            else:
        
                S = length - Distance*3/10  
        
                x, y = road.ReferenceLine.ST2XY(S , 0)
                road.ReferenceLine.set_endPoint(x, y)           

                    
        for  road  in RoadsList:


                                
            inLanesroad = []
            outLanesotherRoad = []   
                     
            roadlength  = road.getLength() 
            road_Lanes = road.roadLanes
    
            Connection_point = roaddict.get(str(road)) 
        
            if road.points[0] == Connection_point:
                Road_Connection = "start"
                
                road.Predecessor = self 
                
                road.link.predecessorLink = RoadLinkPredecessorSuccessor(PredecessorSuccessor =  self , contactPoint =Road_Connection )
                
            else:
                Road_Connection = "end"  
                
                       
                road.Successor = self
                road.link.successorLink = RoadLinkPredecessorSuccessor(PredecessorSuccessor =  self , contactPoint =Road_Connection )
                
               
            
            if len(road_Lanes.RoadLaneSectionList ) > 0:
            
                if Road_Connection == "start":
                    road_section = road_Lanes.RoadLaneSectionList[0]
                    inLanesroad = road_section.Leftlanes
                    
                    
                else:
                    road_section = road_Lanes.RoadLaneSectionList[-1]
                    inLanesroad = road_section.Rightlanes
     
 
            for lane in inLanesroad:
                print(lane.turn)


            for otherRoad in RoadsList:
 
                if road != otherRoad    :
          
                    other_roadlength  = otherRoad.getLength() 
                    other_road_Lanes = otherRoad.roadLanes
                    other_Connection_point = roaddict.get(str(otherRoad)) 
 

                    if otherRoad.points[0] == other_Connection_point:
                        otherRoad_Connection = "start"
                    else:
                        otherRoad_Connection = "end"                    
 
 
                            
                    if len(other_road_Lanes.RoadLaneSectionList ) > 0:
                        
                        if otherRoad_Connection == "start":
                            other_road_section = other_road_Lanes.RoadLaneSectionList[0]
                            outLanesotherRoad = other_road_section.Rightlanes   
                            
                            
                        else:
                            other_road_section = other_road_Lanes.RoadLaneSectionList[-1]
                            outLanesotherRoad = other_road_section.Leftlanes
                                                        
                        
                        
                    usedLans =[]
                    
                    inLanesroad = inLanesroad.copy()
                    #inLanesroad.reverse()  
                                      
                    outLanesotherRoad = outLanesotherRoad.copy()
                    #outLanesotherRoad.reverse()
                    
                    
                    inLanesroadnew =[]
                    
                    addedinLanes = [] 
                    
                    for lane in inLanesroad:
                        
                        if not isinstance(lane , RoadSidewalk ) and  not isinstance(lane , RoadCurb )  and  not isinstance(lane , RoadCyclistsLane ) :
                            inLanesroadnew.append(lane)
                            
                        elif isinstance(lane , RoadCyclistsLane ):
                            addedinLanes.append(lane)
                            
                    inLanesroad =  inLanesroadnew   
                        
                    
                    outLanesotherRoadnew = []
                    
                    addedoutLanes = []
                    
                    for lane in outLanesotherRoad:
                        
                        if not isinstance(lane , RoadSidewalk ) and  not isinstance(lane , RoadCurb ) and  not isinstance(lane , RoadCyclistsLane ) :
                            outLanesotherRoadnew.append(lane)
                            
                        elif isinstance(lane , RoadCyclistsLane ):
                            addedoutLanes.append(lane)
                            
                            
                    outLanesotherRoad =  outLanesotherRoadnew                       
                    
 
                        
                     
 
                    #print(inLanesroad)
                    
                    if len(outLanesotherRoad) > len(inLanesroad)  and  len(inLanesroad) > 1:
                        
                        diff = len(outLanesotherRoad) - len(inLanesroad)
                         
                        for _ in range(0, diff ):
                            inLanesroad =   inLanesroad + [inLanesroad[-1]] 
                    
                    
                    #print("###############################")
                    #print(len(inLanesroad ))
                    #print(len( outLanesotherRoad ))
                    
                    
                    
                    inLanesroad = inLanesroad + addedinLanes
                    outLanesotherRoad = outLanesotherRoad+ addedoutLanes
                    
                    for lane  in     inLanesroad:
                    
                        for  other_lane in  outLanesotherRoad:
                    
                            if  lane.__class__   ==  other_lane.__class__    and other_lane not in usedLans   :
                                
                                usedLans.append(other_lane)
                                
                                #print( lane.__class__.__name__  )
                                 
                                
                                LaneId = lane.LaneId    
                                
                    
                                #lane_leftline =[]
                                #lane_rightline =[]
                                
                                lane_centerline = []
                                step =   1#(roaddictNewConnection.get(str(road)) + roaddictNewConnection.get(str(otherRoad)))/10
                                
                                #print(roadlength)
                                #print(step)
                                for S in np.arange(0 , roadlength  +step  , step):
                                    
                                    [[x_after_Right, y_after_Right] , [x_after_Left, y_after_Left]] =  road_Lanes.get_lane_cross_section_coord(  S , LaneId ) 
                                    
                                    #lane_leftline.append([x_after_Left, y_after_Left])
                                    #lane_rightline.append([x_after_Right, y_after_Right])                                   
                                    if x_after_Left is not None and  x_after_Right is not None and y_after_Left is not None and  y_after_Right is not None:
 
                                        lane_centerline.append([ (x_after_Left  +x_after_Right)/2  , (y_after_Left+ y_after_Right)/2])
                                    
                                
                                other_LaneId = other_lane.LaneId
                                
                                #other_lane_leftline =[]
                                #other_lane_rightline =[]
                                
                                other_lane_centerline = []
                    
                                for S in np.arange(0, other_roadlength  +step  , step):
                                    
                                    [[x_after_Right, y_after_Right] , [x_after_Left, y_after_Left]] =  other_road_Lanes.get_lane_cross_section_coord(  S , other_LaneId ) 
                                    
                                    #other_lane_leftline.append([x_after_Left, y_after_Left])
                                    #other_lane_rightline.append([x_after_Right, y_after_Right])
                                    if x_after_Left is not None and  x_after_Right is not None and y_after_Left is not None and  y_after_Right is not None:
                                        other_lane_centerline.append([ (x_after_Left  +x_after_Right)/2  , (y_after_Left+ y_after_Right)/2])                                     
                                
                                
                                centerline = []
                                if Road_Connection == "start":
                                    lane_centerline.reverse()
                                    
                                    if otherRoad_Connection == "start":    
                                        #other_lane_centerline.reverse()
                                        centerline = lane_centerline  +other_lane_centerline  
 
                                
                                    else:
                                
                                        other_lane_centerline.reverse()
                                
                                        centerline = lane_centerline  +other_lane_centerline 
 
                                else:
                                
                                    if otherRoad_Connection == "start":
                                
                                        centerline = lane_centerline  +other_lane_centerline  
                                          
                                
                                    else:
                                        other_lane_centerline.reverse()
                                
                                        centerline = lane_centerline  +other_lane_centerline 
                                
                                  
                    
                                # x, y = zip(*centerline)
                                # plt.plot(x, y)
                                # ax.scatter(x, y)
                                points = []
                                
                                for cord in centerline:
                                    
                                    points.append(Point(cord[0] , cord[1] ))
                                    
                                
                                
                                newRoad = DrivingRoad( [] , dict() ,[])
                                newRoad.ReferenceLine = RoadReferenceLine.fitRoadReferenceLine(points )
                                
                                
                                Distance = roaddictNewConnection.get(str(road))
                                length  = road.getLength()
                                if Road_Connection == "start":
                                    S = Distance*7/10
                                
                                
                                else:
                                    S = length - Distance *7/10
                                [[x_after_Right, y_after_Right] , [x_after_Left, y_after_Left]] =  road_Lanes.get_lane_cross_section_coord(  S , LaneId )
                                x = (x_after_Right + x_after_Left) / 2
                                y = (y_after_Right + y_after_Left) / 2
                                newRoad.ReferenceLine.set_startPoint(x, y)
                                
                                
                                
                                Distance = roaddictNewConnection.get(str(otherRoad))
                                length  = otherRoad.getLength()
                                if otherRoad_Connection == "start":
                                    S = Distance*7/10
                                
                                
                                else:
                                    S = length - Distance *7/10
                                
                                
                                [[x_after_Right, y_after_Right] , [x_after_Left, y_after_Left]] =  other_road_Lanes.get_lane_cross_section_coord(  S , other_LaneId )
                                x = (x_after_Right + x_after_Left) / 2
                                y = (y_after_Right + y_after_Left) / 2
                                newRoad.ReferenceLine.set_endPoint(x, y)
                                
                                newRoad_lenght = newRoad.getLength()
                                
                                lane_width_strat    = lane.laneWidths[-1].a
                                lane_width_end      = other_lane.laneWidths[-1].a
                                laneWidths = [LaneWidth(sOffset=0, a=lane_width_strat , b= (lane_width_end - lane_width_strat )/ newRoad_lenght , c=0 , d=0) ]
                                
                                
                                if isinstance(lane , DrivingLane):
                                
                                    level = False
                                
                                    laneLink = None  # opendrive.t_road_link( )
                                    lanetype = "driving"                                
                                
                                    laneMarks = [WhiteBrokenLaneMark(0)]
                                
                                    laneHeights = []
                                
                                    newlane = DrivingLane(lanetype, laneWidths, laneMarks, laneHeights, laneLink, level)
                                    newlane.lanSection = newRoad.roadLanes.RoadLaneSectionList[0]
                                    newRoad.roadLanes.RoadLaneSectionList[0].Leftlanes.append( newlane  )
                                    newRoad.roadLanes.RoadLaneOffsetList[0].a = - laneWidths[0].a/2
                                    newRoad.roadLanes.RoadLaneOffsetList[0].b = - laneWidths[0].b/2
                                elif isinstance(lane , RoadCyclistsLane):
                                
                                    lane_width    = lane_width_strat                        
                                    level = False
                                    laneWidths = [LaneWidth(sOffset=0, a=lane_width , b=0 , c=0 , d=0) ]
                                    laneLink = None  # opendrive.t_road_link( )
                                
                                
                                    laneMarks = [WhiteBrokenLaneMark(0)]
                                
                                
                                
                                    newlane = RoadCyclistsLane(laneMarks, laneLink, level, lane_width)
                                    newlane.laneWidths = laneWidths
                                
                                    newlane.lanSection = newRoad.roadLanes.RoadLaneSectionList[0]
                                    newRoad.roadLanes.RoadLaneSectionList[0].Leftlanes.append( newlane  )
                                    newRoad.roadLanes.RoadLaneOffsetList[0].a = - laneWidths[0].a/2
                                    newRoad.roadLanes.RoadLaneOffsetList[0].b = - laneWidths[0].b/2                                  
                                
                                
                                
                                newRoad.link = RoadLink(None , None,newRoad)
                                newRoad.link.predecessorLink = RoadLinkPredecessorSuccessor(road, Road_Connection)
                                newRoad.link.successorLink = RoadLinkPredecessorSuccessor(otherRoad, otherRoad_Connection)
                                
                                
                                self.JunctionRoads.append(newRoad) 
                                
                                newRoad.junction = self
                                Scenery.get_instance().Roads.append(newRoad)
                                
                                ConnectionlaneLinks =[JunctionConnectionLaneLink(fromLane = lane , toLane = other_lane)]
                                
                                
                                connection  = JunctionConnection(junction =  self , incomingRoad = road, connectingRoad = newRoad, contactPoint = Road_Connection , ConnectionlaneLinks = ConnectionlaneLinks)
                                self.Connections.append(connection)
                                
                                break
                                    
                                    

 

        for road in RoadsList:
        
        
            Connection_point = roaddict.get(str(road)) 
        
            if road.points[0] == Connection_point:
                Road_Connection = "start"
        
            else:
                Road_Connection = "end"
        
        
            Distance = roaddictNewConnection.get(str(road))
        
            length  = road.getLength()  
        
            #print(road.Predecessor)
            #print(road.Successor)
        
        
        
            if Road_Connection == "start":
                S = Distance*7/10
                x, y = road.ReferenceLine.ST2XY(S , 0)
                road.ReferenceLine.set_startPoint(x, y)
        
            else:
        
                S = length - Distance *7/10 
        
                x, y = road.ReferenceLine.ST2XY(S , 0)
                road.ReferenceLine.set_endPoint(x, y)                   
                    
 
 
    
    def draw_way(self, fig , ax):
        
        for road in self.JunctionRoads:
    
            road.draw_way(fig , ax)

    def export2opendrive(self): 
        
        id = self.getId()
        mainRoad = None
        name = None
        orientation = None #opendrive.e_orientation.
        sEnd = None
        sStart = None
        
        type_ = opendrive.e_junction_type.DEFAULT
        
        
        priority= None
        controller= None 
        surface = None
        
        connection = []
        
        for con in self.Connections:
            
            connection.append(con.export2opendrive())
        
        
        junxml = opendrive.t_junction(id, mainRoad, name, orientation, sEnd, sStart, type_, connection, priority, controller, surface )
        
        return junxml
 
 
    def getId(self):
        
        if self in Scenery.get_instance().Junctions:
        
     
            
            allelements = Scenery.get_instance().Roads + Scenery.get_instance().Junctions
            return  allelements.index(self)
        
        else:
            return None

class  Scenery():
 
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            obj = object.__new__(cls)
            obj.__init__( *args, **kwargs) 
            
            cls._instance = obj
            
        return cls._instance
    
    
    @classmethod
    def get_instance(cls):
        if Scenery._instance is None:
            Scenery._instance = Scenery(name = None , metaData = None, nodes = None, ways = None, Roads= None, Junctions= None)
            
        else:
            return Scenery._instance 
            
            
 
 
    @classmethod
    def from_location(cls, minlat, minlon, maxlat  , maxlon, ref_lat=None , ref_lon =None  ): 
        
        minlat = min(minlat , maxlat)
        maxlat = max(minlat , maxlat)
        
        minlon = min(minlon , maxlon)
        maxlon = max(minlon , maxlon)
        
        filepath = os.path.join(sources_osm, f"{minlon}_{minlat}_{maxlon}_{maxlat}.osm")    
        if not  os.path.isfile(filepath):
      
            url = f"https://overpass-api.de/api/map?bbox={minlon},{minlat},{maxlon},{maxlat}" 
            utilities.download_url(url, filepath)
        
        if  os.path.isfile(filepath): 
            
            return cls.from_Osm(filepath, ref_lat , ref_lon   )          
 
    @classmethod
    def from_Osm(cls, filepath, ref_lat=None , ref_lon =None  ):
        
        Database_name = os.path.basename(filepath)[:-4]
        #print(Database_name)
        
        osmObj = osm_map.parse(filepath, silence=True , print_warnings=True)
        
        # for b in osmObj.bounds:
        #     #print(b)

        # for b in osmObj.relation:
        #     #print(b)
        
        bound = osmObj.bounds[0]
        
        minlat = float(bound.minlat)
        minlon = float(bound.minlon)      
        maxlat = float(bound.maxlat)
        maxlon = float(bound.maxlon)
        
        
        if ref_lat is None:
            ref_lat = minlat
 
        if ref_lon is None:
            ref_lon = minlon
        
        min_x, min_y = utilities.projection_fromGeographic(minlat, minlon, ref_lat , ref_lon)
        max_x, max_y = utilities.projection_fromGeographic(maxlat, maxlon, ref_lat , ref_lon)
        
        metaData = {"minlat":minlat , "minlon": minlon , "maxlat": maxlat  , "maxlon": maxlon  , "min_x": min_x , "min_y": min_y , "max_x": max_x , "max_y":max_y }
                
 
        nodsdict = dict()
 
        Nodeswaysdict = dict() 
        
        nodesmap = dict()
 
        for node in tqdm(osmObj.node):
            # ###print(node)
            node_id = node.id
            latitude = float(node.lat)
            longitude = float(node.lon)
            x , y = utilities.projection_fromGeographic(latitude, longitude,ref_lat , ref_lon) 
        
            # if x <= max_x + deltaX   and x >= min_x - deltaX   and y <= max_y +deltaY  and y >= min_y -deltaY  :
            # if  x <= max_x    and x >= min_x   and y <= max_y   and y >= min_y    :  
                  
            tags = dict()
            
            for tag  in node.tag:
                tags[tag.k] = tag.v
            
            node = Point(x, y, tags )  # {"x": x , "y" : y , "tags" : tags  ,"latitude":latitude  , "longitude":longitude , "node_id" : node_id}
            
            Nodeswaysdict[node_id] = []  
            
            nodsdict[node_id] = node  
            x = int(node.x)
            y = int(node.y)  
            
            key = f"{x}_{y}"
            
            if nodesmap.get(key , None) is None:
                
                nodesmap[key] = []
                
            nodesmap[key].append(node_id)     


                
        ways = []
        
        
        
        waysList = []
        
        for way in tqdm(osmObj.way):
        
            way_id = way.id
             
            nodes = []
            
            poly = []
            
            relvantnodes = []
            for nd in way.nd:
                
                node_id = nd.ref
                
                node = nodsdict.get(node_id, None)
                
                if node is not None:
                    nodes.append(node) 
                    poly.append([node.x, node.y])        
        
                tags = dict()
            
                for tag  in way.tag:
                    tags[tag.k] = tag.v          
        
            area = utilities.PolygonArea(poly)


            if len(nodes) > 0:
                
                if  utilities.is_clockwise(poly) and  nodes[0] == nodes[-1]:
                    nodes.reverse()
                    poly.reverse()
            
                tags = dict()
            
                for tag  in way.tag:
                    tags[tag.k] = tag.v  
                    
                #print("find  relvantnodes")
                    
                if nodes[0] == nodes[-1]:
                
                    outer = poly                    
                    
                    ##print(len(outer))
                    
                    if len(outer) > 0:
                        
                        relaventnodeides = []
                        
                        center = utilities.centroid(outer)
                        # #print("center"  , center)
                        x_center = center[0]
                        y_center = center[1]
                        
                        x_cord = int(x_center)
                        y_cord = int(y_center)
                        
                        r = int(math.sqrt( area ) + 20)
                        
                        if r < 1000:
                        
                            #print(r)
                            for i in range(-r , r + 1 , 1):
                                 
                                for j in range(-r , r + 1 , 1):
                            
                                    key = f"{x_cord+i}_{y_cord+j}"
                                    
                                    relaventnodeides = nodesmap.get(key , [])
                                    
                                    # #print(key , len(relaventnodeides))
                        
                                    # relaventnodeides = list(set(relaventnodeides))
                        
                                    for node_id in relaventnodeides:
                                        node = nodsdict.get(node_id, None)
                            
                                        if node is not None and  node not in nodes  and node not in relvantnodes:
                                            point = [node.x, node.y]
                                            if  utilities.is_inside_polygon(outer , point):  # and len(node.tags.keys() ) >0 
                                                relvantnodes.append(node)  
            
            
                waydict = {"nodes":nodes  , "area":area  , "tags" :tags  , "relvantnodes" : relvantnodes}
        
                waysList.append(waydict)
        
        
        waysList.sort(key=lambda x: x.get("area"), reverse=False)
                     
        for way in tqdm(waysList):
            
            #print(way.get("area"))
            nodes = way.get("nodes")
            tags = way.get("tags")
            relvantnodes = way.get("relvantnodes")
 
            newWay = SceneryObject.newWay(nodes, tags , relvantnodes)    
            
            if newWay is not None: 
            
                ways.append(  newWay )
        
        # remove unused nodes 
        
        new_nodsdict = dict() 
        
        for node_key  in nodsdict.keys():
        
            node = nodsdict.get(node_key)
            
            add = False
            x = int(node.x)
            y = int(node.y)  
            
            if len(node.Ways_reference) > 0:
                add = True            
                      
            elif     x <= max_x    and x >= min_x   and y <= max_y   and y >= min_y   and len(node.tags.keys()) > 0: 
                
                add = True
            
            if add: 
                new_nodsdict[node_key] = node 
                

                     
        nodsdict = new_nodsdict
        

        for node_key  in nodsdict.keys():
        
            node = nodsdict.get(node_key)
            
            if len(node.Ways_reference) == 0 and len(node.tags.keys()) > 0 :
                
                newWay = SceneryObject.newPointWay( node , node.tags  )    
                
                if newWay is not None: 
                
                    ways.append(  newWay )
        

 
 
        roads =[] 
        
        
        
        #GreenSpaceTrees = []
        for way in  ways :
        
        
        
            if isinstance(way, Road) :# and not isinstance(way,PedestrianRoad )  and not isinstance(way,CycleRoad ) and not isinstance(way,ServiceRoad ):
                roads.append(way)
 

 
        
        for road in roads:#
        
            ways.remove(road)
        
        
 
        Roads = [] #roads#Scenery.organize_Roads(roads)    
        Junctions =   [] 
        
        
        RoadConnections = []
        
 
        for road in roads:
        
            if  len(road.points) >  1 : 
                end = road.points[-1]  
                end_reference_all = end.Ways_reference 
                end_reference = []
                for roadObj in end_reference_all:
                    if isinstance(roadObj, road.__class__ ):
                        end_reference.append(roadObj)
                
                
                if len(end_reference) >= 2:
                    
                    end_reference.sort(key=lambda x:   x.getLength() , reverse=True)
                    
                    if  end_reference not in RoadConnections:
                        RoadConnections.append(end_reference)
                     
                    
                start = road.points[0]         
                start_reference_all = start.Ways_reference 
                start_reference = []
        
                for roadObj in start_reference_all:
                    if isinstance(roadObj, road.__class__ ):
                        start_reference.append(roadObj)

 
                if len(start_reference) >= 2:
                    
                    start_reference.sort(key=lambda x:   x.getLength() , reverse=True)
                    
                    if  start_reference not in RoadConnections:
                        RoadConnections.append(start_reference)
        
        
        coverd = []
        
        for roadConnection in RoadConnections:
            
            if roadConnection not in coverd:
                
                coverd.append(roadConnection)
                
                if len(roadConnection) == 2:
                    
                    road = roadConnection[0]
                    other = roadConnection[1]
                    
                    start = road.points[0] 
                    end = road.points[-1] 

                    other_start = other.points[0]  
                    other_end = other.points[-1]      
                    
                    if end == other_start and road.link.Successor is None and other.link.Predecessor is None  :
                        road.link.Successor = other 
                        other.link.Predecessor = road  
                    elif end == other_end and road.link.Successor is None and other.link.Successor is None  :
                        road.link.Successor = other 
                        other.link.Successor = road  


                    elif start == other_end and road.link.Predecessor is None and other.link.Successor is None  :
                        road.link.Predecessor = other 
                        other.link.Successor = road  
                    elif start == other_start and road.link.Predecessor is None and other.link.Predecessor is None  :
                        road.link.Predecessor = other 
                        other.link.Predecessor = road  
                    
                else:
                    
                    junction = Junction(roadConnection)
                    Junctions.append(junction)  
                    
                    
                
                   
        for road in roads:
        
            #road.update()
            if road.getLength() > 0  and len(road.points) > 0:
                Roads.append(road)          
        
        
        
 
        
 
        obj =  Scenery(Database_name, metaData, nodsdict, ways  , Roads  , Junctions)
        
        obj.update()
        
        return obj
    
 

    
    def __init__(self,name, metaData,nodes,  ways , Roads  , Junctions):
        self.name = name
        self.metaData = metaData
        self.nodes = nodes
        self.ways = ways
        self.Roads = Roads
        
        self.Junctions = Junctions
        
        
        #self.update()
        
    def update(self):
        
        
        roads = self.Roads 
        newRoads =[]
        for road in roads:
            
            road.update()
            if road.getLength() > 0  and len(road.points) > 0:
                newRoads.append(road)
                
        self.Roads = newRoads
                    
        for junction in self.Junctions:
        
            junction.update()        
            pass


    def export2opendrive(self, save_path):
    
        east = self.metaData.get('max_x')
        north = self.metaData.get('max_y')
        west = self.metaData.get('min_x')
        south = self.metaData.get('min_y')
    
        #referenceLat = self.metaData.get('minlat')
        #referenceLon = self.metaData.get('minlon')
    
        geo = "<![CDATA[+proj=tmerc +lat_0=0.002049196191879877 +lon_0=4.513789469769987 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +geoidgrids=egm96_15.gtx +vunits=m +no_defs ]]>"
    
        geoReference = opendrive.t_header_GeoReference(valueOf_=geo)
    
        header = opendrive.t_header(east=east, name=self.name, north=north, revMajor=1, revMinor=7, south=south, vendor="OSM", version=1, west=west, geoReference=geoReference)
    
        roadlist = []
        #i = 0
        for roadObj in self.Roads:
    
            if isinstance(roadObj, Road):
    
                roadXml = roadObj.export2opendrive()
                #roadXml.id = i
                roadlist.append(roadXml)
    
                #i = i + 1
    
        controller = []
        junctions = []
        
 
        for junctionObj  in  self.Junctions:
        
            junctionXml = junctionObj.export2opendrive()
            #junctionXml.id = j
            junctions.append(junctionXml)
        
 
        
        junctionGroup = []
        station = []
        dataQuality = None
        include = None
        userData = None
        gds_collector_ = None 
        opendrive_object = opendrive.OpenDRIVE(header, roadlist, controller, junctions, junctionGroup, station, dataQuality, include, userData, gds_collector_)
    
        with open(save_path, 'w' , encoding='utf-8') as outfile:
    
            outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            opendrive_object.export(outfile=outfile , level=0 , pretty_print=True)


    def draw_scenery(self, show=False, savepath=None , size=(25, 25) , img=None):
 
        import matplotlib.pyplot as plt
        from matplotlib.patches import Polygon , Rectangle
        # for road in self.Roads:
        fig, ax = plt.subplots(figsize=size, facecolor='lightskyblue', layout='constrained')
        plt.axis('equal')
        
        cid = fig.canvas.mpl_connect('button_press_event', onclick)
        
        if img is not None:
            
            # , "min_x" : min_x , "min_y" : min_y , "max_x" : max_x , "max_y" :max_y 
            min_x = self.metaData["min_x"]
            min_y = self.metaData["min_y"]
            max_x = self.metaData["max_x"]
            max_y = self.metaData["max_y"]
            
            extent = (min_x, max_x, min_y, max_y)
            
            # #print(extent)
            # img = cv2.Canny(img,100,200)
            plt.imshow(img , origin='upper', extent=extent)
 
        
        for way in self.ways :
             
             
            way.draw_way(fig, ax)


        for way in self.Roads :
             
             
            way.draw_way(fig, ax)

        for way in self.Junctions :
        
        
            way.draw_way(fig, ax)

 
        if savepath is None:
            savepath = f".\\Data\\scenery"
        
        plt.savefig(savepath + ".png")
        plt.savefig(savepath + ".svg")
        if show:
            plt.show()  
 
 
def onclick(event):
    # global ix, iy
    
    # global sceneryObj
    
    ix, iy = event.xdata, event.ydata
    
    if ix is not None and iy   is not None:
     
        # clear()
 
        dist = 1000
        closet_node = None
        
        for node_id in sceneryobj.nodes.keys():
            node = sceneryobj.nodes.get(node_id)
            
            
            
            node_x = node.x
            node_y = node.y
    
            deltaX = (ix - node_x).astype(float)
            deltaY = (iy - node_y) .astype(float)
            
            new_dist = np.sqrt(deltaX * deltaX + deltaY * deltaY)
            
            if new_dist < dist:
                dist = new_dist
                
                closet_node = node
        
        if closet_node is not None:
        
            print("************************ Node ******************************")
            
            print(str(closet_node.tags))    
            
            for ref in closet_node.Ways_reference:
                 
                print( f"################################{ref.__class__.__name__} #############################################" )
                print( f"################################ {ref}#############################################" )
                ##print(str(ref.tags))
 
                refdict= ref.__dict__
                
                for key in refdict.keys():
                    
                    
                    if key not in  [ "relvantnodes"  , "points"]:
                        print( key , "--> ",   refdict.get(key) )
     
                for node in ref.points:
                    
                    if len(node.tags) > 0:
                        print(node.tags)                 
                    
                if isinstance(ref ,Road): 
                    print("Length" ,ref.ReferenceLine.getLength())
                    
                    for ele in ref.ReferenceLine.geometry_elements:
                        
                        
                           
                        
                        print(ele , "length" , ele.length)
                        if isinstance(ele , Arc):
                            print(ele , "R" , 1/ ele.Curvatur)
 
if __name__ == '__main__':




    
    name = "dbank"
    minlat = 51.71427 #dbank
    minlon = 8.74480
    maxlat = 51.71526
    maxlon = 8.74649
    
    
 
 

    name = "problem"
    minlat = 51.744210
    minlon = 8.710806
    maxlat = 51.746409
    maxlon = 8.713800
   
 
 

    name = "innerring"
    minlat = 51.7135  # innerring
    minlon = 8.7431
    maxlat = 51.7249
    maxlon = 8.7650 
 

    
    name = "paderborn_big" 
    minlat = 51.7020 # padebor big
    minlon = 8.6866
    maxlat = 51.7735
    maxlon = 8.7657       



    name = "Landstrasse_L776_Paderborn" 
    minlat = 51.59957  
    minlon = 8.57775
    maxlat = 51.68267
    maxlon = 8.66272    


    name = "warburger"
    minlat = 51.707122  # 
    minlon = 8.775724
    maxlat = 51.707897
    maxlon = 8.777159


    
    name = "HNI"    
    minlat = 51.71073  # 
    minlon = 8.73018
    maxlat = 51.73474
    maxlon = 8.75095  

    name = "westertor_big"    
    minlat = 51.7135  # 
    minlon = 8.74310
    maxlat = 51.71850
    maxlon = 8.75160  


    

    
    name = "juncition12"
    minlat = 51.707443  # 
    minlon = 8.746048
    maxlat = 51.707762
    maxlon = 8.746593


    
    

    

    name = "uni"
    minlat = 51.70382  # 
    minlon = 8.76700
    maxlat = 51.70916
    maxlon = 8.77949

    name = "westertor2"
    minlat = 51.715272  # 
    minlon = 8.746002
    maxlat = 51.715666
    maxlon = 8.746764

    name = "viele junction"
    minlat = 51.713655  # 
    minlon = 8.764024
    maxlat = 51.717604
    maxlon = 8.765411

    

    name = "westertor2"
    minlat = 51.71476  # 
    minlon = 8.74467
    maxlat = 51.71605
    maxlon = 8.74728
    
    name = "juncition0"
    minlat = 48.137309  # 
    minlon = 11.555563
    maxlat = 48.137710
    maxlon = 11.556343

    name = "schnitt"
    minlat = 51.714124  # 
    minlon = 8.764359
    maxlat = 51.714995
    maxlon = 8.766470

    ref_lat =  minlat  
    ref_lon = minlon
    

    sceneryobj = Scenery.from_location(minlat , minlon  , maxlat  , maxlon , ref_lat  , ref_lon   )
    
    
    
    
    
    sceneryobj.export2opendrive(f"C:\\scenery_Data\\Output\\{name}.xodr")
 
    sceneryobj.draw_scenery(True , f"C:\\scenery_Data\\Output\\{name}" , (15, 15)) 
    
        
 