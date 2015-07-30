"""Module to convert exported FlexStation plate read files to spreadhseets of:
 ____________________________________
| WELL A1                |
| TIME 1    TIME 2    ...    TIME N  |
| VALUE 1   VALUE 2   ...    VALUE N |
|                  |
| . . .                              |
|                                    |
| WELL ZN                            |
| TIME 1    TIME 2    ...    TIME N  |
| VALUE 1   VALUE 2   ...    VALUE N |
|____________________________________|
...for all wells on the plate.
Call from the command line as python simple_flipr.py *args
Required arguments are:
-name of input file: first argument, or specify with -i or --input
-name of output file: second argument, or specify with -o or --output
Optional arguments are:
-run temperature (defaults to 37C): third argument, or specify with -t or --temp
-number of rows on plate (defaults to 8): fourth argument, or specify with -r or --rows
-number of columns on plate (defaults to 10): fifth argument, or specify with -c or --cols
"""



import sys
import getopt

class Individual(object):

  def __init__(self, timeTupleArray):
    """Initialize with list of tuples of (time, fluorescence value)."""
    self.times = [tup[0] for tup in timeTupleArray]
    self.values = [tup[1] for tup in timeTupleArray]

def simple_reader(filename, nRow = 8, nCol = 10, readTemp = 37):
  """Input exported file from FlexStation.
  Output array with nRow rows and nCol columns, where each cell contains
  a list of tuples of (time: fluorescence value) for that particular well
  on the plate."""
  plate = [[[] for u in range(nCol)] for i in range(nRow)]
  times = None
  with open(filename, 'r') as fo:

    for idx, line in enumerate(fo):

      try:
        int(float(line.split()[0]))
        #print line.split()[0]
        if int(float(line.split()[0])) in (readTemp - 1, readTemp, readTemp + 1):
          blockStart = idx
        if blockStart <= idx < blockStart + nRow * 2:
          #print idx, blockStart
          if idx == blockStart:
            times = [float(item) for item in line.split()[1::]]
          else:
            if times:
              values = [float(item) for item in line.split()]
              assert len(values) == len(times) == nCol
              pairs = [(times[i], values[i]) for i in range(len(times))]
              row = (idx - 1 - blockStart)/2

              for index, pair in enumerate(pairs):
                plate[row][index].append(pair)

              times, values = None, None

            else:
              times = [float(item) for item in line.split()]
      except:
        pass #line contains text
  return plate

def plate_to_indiv(plate_array):
  indiv_array = [[] for dummy in range(len(plate_array))]
  for row_idx in range(len(plate_array)):
    for col_idx in range(len(plate_array[row_idx])):
      indiv_array[row_idx].append(Individual(plate_array[row_idx][col_idx]))
  return indiv_array


def output(indiv_array, filename):
  ALPH = 'A B C D E F G H I J K L M N O P Q R S T U V W X Y Z'.split()
  with open(filename, 'w') as fo:

    for col_idx in range(len(indiv_array[0])):
      for row_idx in range(len(indiv_array)):
        current_indiv = indiv_array[row_idx][col_idx]
        #print len(current_indiv.times)
        time_string = '\t'.join(str(current_indiv.times).split(','))[1:-1]
        value_string = '\t'.join(str(current_indiv.values).split(','))[1:-1]

        fo.write(ALPH[row_idx]+str(col_idx+1))
        fo.write('\n')
        fo.write(time_string)
        fo.write('\n')
        fo.write(value_string)
        fo.write('\n')
        fo.write('\n')


def flipr_to_spreadsheet(inputFilename, outputFilename, nRow = 8, nCol = 10, readTemp = 37):
  time_array = simple_reader(inputFilename, nRow, nCol, readTemp)
  indiv_array = plate_to_indiv(time_array)
  output(indiv_array, outputFilename)

def main(argv):
  try:
    opts, args = getopt.getopt(argv, "i:o:t:r:c:", ["input=", "output=", "temp=", "rows=", "cols="])
    #print opts
    if opts:
      temp, rows, cols = 37, 8, 10
      for opt, arg in opts:
        if opt in ("-i", "--input"):
          inputfile = arg
        elif opt in ("-o", "--output"):
          outputfile = arg
        elif opt in ("-t", "--temp"):
          temp = int(arg)
        elif opt in ("-r", "--rows"):
          rows = int(arg)
        elif opt in ("-c", "--cols"):
          cols = int(arg)
        else:
          raise ValueError("Error: unrecognized argument flag!")
      print "input file: "+str(inputfile)
      print "output file: "+str(outputfile)
      flipr_to_spreadsheet(inputfile, outputfile, rows, cols, temp)
      print "output successful!"
    else:
      print "input file: "+str(args[0])
      print "output file: "+str(args[1])
      flipr_to_spreadsheet(*args)
      print "output successful!"

  except getopt.GetoptError:           
        #usage()                          
    sys.exit(2)  

if __name__ == "__main__":
  main(sys.argv[1:]) #sys.argv[0] is the name of the script; not useful