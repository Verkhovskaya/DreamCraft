import sys
import mclevel
import materials
import numpy as np
from PIL import Image
import time
import os

from fpdf import FPDF

sys.setrecursionlimit(10000)

def make_pdf(user_id, x1, z1, y1, x2, z2, y2):
   x_min = min(int(x1), int(x2))
   x_max = max(int(x1), int(x2))
   y_min = min(int(y1), int(y2))
   y_max = max(int(y1), int(y2))
   z_min = min(int(z1), int(z2))
   z_max = max(int(z1), int(z2))

   x_diff = x_max - x_min
   y_diff = y_max - y_min
   z_diff = z_max - z_min

   level = mclevel.fromFile("/root/pymclevel/data/663/map") #"/root/pymclevel/data/" + str(user_id) + "/map")

   map = np.zeros((x_diff, y_diff, z_diff))
   types = []


   def show(map):
      print(map.shape)
      for z in range(map.shape[2]):
         for x in range(map.shape[0]):
            for y in range(map.shape[1]):
               print(int(map[x, y, z])),
            print
         print

   for z in range(z_min, z_max):
      for x in range(x_min, x_max):
         for y in range(y_min, y_max):
            chunk = level.getChunk(x/16, y/16)
            block = int(chunk.Blocks[x%16,y%16,z])
            map[x-x_min,y-y_min,z-z_min] = block

   types_temp = []
   colors = [(0,0,0), (129,207,224), (255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255), (255, 0, 255), (255, 255, 0)]

   for x in range(x_diff):
      for y in range(y_diff):
         for z in range(z_diff):
            block = map[x,y,z]
            if block not in types_temp:
               types_temp.append(int(block))
   types_temp = sorted(types_temp)

   for x in range(x_diff):
      for y in range(y_diff):
         for z in range(z_diff):
            block = map[x,y,z]
            if block != 0:
               map[x,y,z] = 1

   for x in range(x_diff):
      for y in range(y_diff):
         for z in range(z_diff):
            block = map[x,y,z]
            if block not in types:
               types.append(int(block))

   types = sorted(types)

   pixel_size = 10

   for x in range(x_diff):
      for y in range(y_diff):
         for z in range(z_diff):
            block = map[x,y,z]
            if block != 0:
               map[x,y,z] = 1

   def draw_level(pixel_size, map):
      image = np.zeros(((map.shape[0]+1)*pixel_size, (map.shape[1]+1)*pixel_size, 3), dtype=np.uint8)
      for x in range(map.shape[0]):
         for y in range(map.shape[1]):
            image[x*pixel_size:(x+1)*pixel_size, y*pixel_size:(y+1)*pixel_size] = colors[int(map[x,y])]
      return image


   class Tile:
      def __init__(self, type):
         self.seen = False
         self.type = type

   def spread(flat, type, x, y):
      if x<0 or x >= len(flat[0]) or y<0 or y >= len(flat):
         return []
      if flat[y][x].seen or flat[y][x].type != type:
         return []
      flat[y][x].seen = True
      visited = []
      visited += spread(flat, type, x+1, y)
      visited += spread(flat, type, x, y+1)
      visited += spread(flat, type, x-1, y)
      visited += spread(flat, type, x, y-1)
      visited.append((x,y))
      return visited

   def get_cutouts(type):
      cutouts = []
      for z in range(z_diff):
         flat = [[Tile(map[x,y,z]) for x in range(x_diff)] for y in range(y_diff)]
         for x in range(x_diff):
            for y in range(y_diff):
               cutout = spread(flat, type, x, y)
               if cutout != []:
                  cutouts.append(cutout)
      return cutouts

   def normalize(cutouts):
      normalized = []
      for cutout in cutouts:
         min_x = min([a[0] for a in cutout])
         min_y = min([a[1] for a in cutout])
         normalized.append([(a[0]-min_x, a[1]-min_y) for a in cutout])
      return normalized

   map_x = 100
   map_y = 140

   for type in types:
      if type != 0:
         cutouts = normalize(get_cutouts(type))

         cutouts = sorted(cutouts, key=lambda cut: max([a[1] for a in cut]))  # Sort by cutout height

         layers = [[cutouts[0]]]

         for cutout in cutouts[1:]:
            prev_width = max([max([block[0] for block in peice]) for peice in layers[-1]]) + 1
            if max([a[0] for a in cutout]) + prev_width < map_x:
               layers[-1].append([(block[0] + prev_width, block[1]) for block in cutout])
            else:
               layers.append([cutout])


         """
         first = layers[0::2]  # Every second, largest first
         second = layers[1::2][::-1]  # Every second, smallest first, oriented backwards
         
         interleaved = []
         for a in range(len(first)):
            interleaved.append(first[a])
            if a < len(second):
               interleaved.append(second[a])
         """

         layout = []
         prev_height = 0
         for layer in layers:
            print(prev_height)
            prev_height += max([max([block[1] for block in peice]) for peice in layer]) + 1
            for peice in layer:
               layout.append([(block[0], block[1]+prev_height) for block in peice])
         max_x = max([max([block[0] for block in peice]) for peice in layout])
         max_y = max([max([block[1] for block in peice]) for peice in layout])
         print(max_x, max_y)
         sheet = np.zeros((max_x+1, max_y+1))

         for peice in layout:
            for block in peice:
               sheet[block[0], block[1]] = 1

         outlines = []
         for peice in layout:
            outline = []
            for block in peice:
               line0 = ((block[0], block[1]), (block[0], block[1]+1))
               line1 = ((block[0], block[1]), (block[0]+1, block[1]))
               line2 = ((block[0]+1, block[1]), (block[0]+1, block[1]+1))
               line3 = ((block[0], block[1]+1), (block[0]+1, block[1]+1))
               if line0 in outline:
                  outline.remove(line0)
               else:
                  outline.append(line0)
               if line1 in outline:
                  outline.remove(line1)
               else:
                  outline.append(line1)
               if line2 in outline:
                  outline.remove(line2)
               else:
                  outline.append(line2)
               if line3 in outline:
                  outline.remove(line3)
               else:
                  outline.append(line3)
            for line in outline:
               if line not in outlines:
                  outlines.append(line)

         outline_text = ""
         for line in outlines:
            outline_text += "line " + str(line[0][0]) + "," + str(line[0][1]) + " " + str(line[1][0]) + "," + str(line[1][1]) + "\n\n"

         write_to = open("/root/pymclevel/data/" + str(user_id) + "/commands.scr", "w")
         write_to.write(outline_text)
         write_to.close()

   os.mkdir("/root/pymclevel/data/" + str(user_id) + "/layout")
   image_names = []
   for z in range(map.shape[2]):
      data = draw_level(10, map[:,:,z])
      img = Image.fromarray(data, 'RGB')
      img_name = "/root/pymclevel/data/" + str(user_id) + "/layout/" + str(z) + ".png"
      image_names.append(img_name)
      img.save(img_name)

   pdf = FPDF()
   pdf.add_page()
   pdf.image("/root/pymclevel/front_page.jpg", 0, 0, 240, 240)
   # imagelist is the list with all image filenames
   for image in image_names:
      pdf.add_page()
      pdf.image(image, 30, 30, 150, 150)
   pdf.output("/root/pymclevel/data/" + str(user_id) + "/layout.pdf", "F")

