"""
Thomatronik GmbH
Brückenstr. 1	    Tel.: +49 (0)8031 2175-0    www.thomatronik.de
D-83022 Rosenheim	Fax.: +49 (0)8031 2175-30   info@thomatronik.de

Author:	     Mueller  <info@thomatronik.de>
Date:        30.03.2017

Changes
--------
30.03.2017: First Release

Description:
This module will open a Matplotlib 2d Graph Window during a transient simulation. It will show at specified points
several fieldvalues. The Graphs will be updated automatically after each timestep

Known Issues:
- This works only for 2 or more fieldcomponents, if you specify only one component in logcomponents it will crah, 
  because then there is only one axis defined and not an array of axis.
  
- The window with the fieldvalues cannot be resized or closed during simulation.   
"""

import operafea
import time
import numpy as np
import matplotlib.pyplot as plt

# For debug output set to True or False
debug = True

# Modellname for Output data file
filename = operafea.getUsrVarStr("modellname")

# Define the points to get field values at. Units are in your model units
koordinates = [[1, 1, 0]]

# Define the basic field components to extract from database
# rbx, rby, rbz, rjx, rjy, rjz, rex, rey, rez....
fieldcomponents = ["rjx", "rjy", "rjz", "rbx", "rby", "rbz"]

# Define the field values for logging. Below you have to define
logcomponents = ["Jmod","Bmod"]

def fieldconversion(logvalue,data):
    logvalue = logvalue.upper()
    return {
        "JX": data["RJX"],
        "JY": data["RJY"],
        "JZ": data["RJZ"],
        "JMOD": np.sqrt(data["RJX"]**2+data["RJY"]**2+data["RJZ"]**2),
        "BX": data["RBX"],
        "BY": data["RBY"],
        "BZ": data["RBZ"],
        "BMOD": np.sqrt(data["RBX"]**2 + data["RBY"]**2 + data["RBZ"]**2)
    }[logvalue]

# Get the length and field units
lengu = operafea.getUsrVarStr("LENGU")
curdu = operafea.getUsrVarStr("CURDU")
elecu = operafea.getUsrVarStr("ELECU")
fluxu = operafea.getUsrVarStr("FLUXU")
fielu = operafea.getUsrVarStr("FIELU")

def unitconversion(logvalue):
    logvalue = logvalue.upper()
    return {
        "J": curdu,
        "B": fluxu,
        "E": elecu,
        "H": fielu
    }[logvalue[0]]

if debug:
    operafea.output("Laengeneinheit: "+lengu)

# Output data to file
outputfile = filename+"_fields.txt"
print_header = False

# Define a figure and several axes to visualize data during simulation
fig, ax = plt.subplots(nrows=len(logcomponents), ncols=len(koordinates), sharex=True, figsize=(len(koordinates)*5,len(logcomponents)*3))
fig.suptitle('Logfile: ' + filename + ', Output: ' + time.strftime("%c"), fontsize=12)
fig.canvas.set_window_title('Thomatronik GmbH')

# Set the title of each axes for each point
if len(koordinates) > 1:
    for point in range(len(koordinates)):
        ax[0][point].set_title("Punkt("+lengu+"): x={:.2f}, y={:.2f}, z={:.2f}".format(*koordinates[point]))
else:
    ax[0].set_title("Punkt("+lengu+"): x={:.2f}, y={:.2f}, z={:.2f}".format(*koordinates[0]))

# Set the y-axis label for each log component
for field in range(len(logcomponents)):
    if len(koordinates) > 1:
        ax[field][0].set_ylabel(logcomponents[field]+" in "+unitconversion(logcomponents[field]))
    else:
        ax[field].set_ylabel(logcomponents[field] + " in " + unitconversion(logcomponents[field]))

# Set the x-axis label
if len(koordinates) > 1:
    for point in range(len(koordinates)):
        ax[len(logcomponents)-1][point].set_xlabel("Time in s")
else:
    ax[len(logcomponents) - 1].set_xlabel("Time in s")

# Define a list of lines to store the data into
ln = [[0 for i in range(len(koordinates))] for j in  range(len(logcomponents))]

# Create the line for each axis
for point in range(len(koordinates)):
    for field in range(len(logcomponents)):
        if len(koordinates) > 1:
            ln[field][point] = ax[field][point].plot([], [], '-ro')
        else:
            ln[field][point] = ax[field].plot([], [], '-ro')

plt.show(block=False)


# Define a Class to store all the data
class LogPoint():
    def __init__(self, koordinates, fields):
        self.x = koordinates[0]
        self.y = koordinates[1]
        self.z = koordinates[2]

        self.time =[]
        self.fields = {fieldvalue: [] for fieldvalue in fields}


#Create an object for the results:
result = [LogPoint(point, logcomponents) for point in koordinates]

# Convert into NumPy Array for OperaFea Module to get the fieldvalues
npkoordinates = np.float_(koordinates)

"""
This function will evaluate after each simulation the field values
"""
def onTimeStepEnd():
    # Module/file scope variables must be declared global if changed
    global print_header

    operafea.output("\n --------- Data extraction at end of time step ---------\n")

    # Retrieveing Opera system variable TTIME
    ttime = operafea.getSysVar("TTIME")

    # Get the currently active simulation
    simu = operafea.currentSimulation()

    # Set up a flag (addFlag) allowing field output in every time step
    simu.addFlag('COMPUTEDATAPERTIMESTEP', True)

    #Create one string out of the fieldcomponents tuple without quotation marks for the Operafea function
    fieldcompstring = ", ".join(fieldcomponents).upper()
    if debug:
        print(fieldcompstring)

    # Use getFieldsAtCoords to get an opera object containing field info for each required point
    p = 0
    for point in npkoordinates:
        elem_ids = np.float_([])  # see documentation
        fields_info = simu.getFieldsAtCoords(fieldcompstring, point, elem_ids)
        # Store time for each point
        result[p].time.append(ttime)

        if debug:
            print(fields_info)
        # Must extract each field component from fields_info
        tempdata = {field.upper(): fields_info.getValue(field.upper())[0] for field in fieldcomponents}
        if debug:
            print(tempdata)
        for field in logcomponents:
            result[p].fields[field].append(fieldconversion(field,tempdata))
        p += 1

    # for point in range(len(koordinates)):
    #     jmod = np.sqrt(result[point].fields["RJX"]**2+result[point].fields["RJY"]**2+result[point].fields["RJZ"]**2)
    #     jy = result[point].fields["RJY"]
    #     jx = result[point].fields["RJX"]
    #     # bmod = np.sqrt(result[point].fields["rbx"]**2+result[point].fields["rby"]**2+result[point].fields["rbz"]**2)

    # Report to res file
    # operafea.output("Field of interest: J (Tesla)\n")
    # operafea.output("Coordinate (mm): ({:1.3g}, {:1.3g}, {:1.3g})\n".format(*xyz))
    # operafea.output("Times (s): {:1.5g}\n".format(ttime))
    # operafea.output("Field components (Tesla): ({:1.3g}, {:1.3g}, {:1.3g})\n".format(*b_vec))
    # operafea.output("Field modulus (Tesla): {:1.3g}\n".format(b_mod))
    # operafea.output(" ")
    # # Write results to a file
    # if print_header:  # on first call only
    #     print_header = False
    #     with open(outputfile, 'w') as f:
    #         # Delete old file and write header
    #         header_labels = ["/TTIME_(s)",
    #                          "x_(mm)",
    #                          "y_(mm)",
    #                          "z_(mm)",
    #                          "Bx_(T)",
    #                          "By_(T)",
    #                          "Bz_(T)",
    #                          "Bmod_(T)"]
    #         line = ('{:>13s} ' * 8).format(*header_labels)
    #         f.write(line + '\n')
    #
    # with open(outputfile, 'a+') as f:
    #     # Write time, position and field values in columns
    #     line = ('{:13.3E} ' * 8).format(ttime, xyz[0], xyz[1], xyz[2], bx, by, bz, b_mod)
    #     f.write(line + '\n')

    operafea.output(" ---- Data extraction at end of time step (complete) ----\n")


    for point in range(len(koordinates)):
        f = 0
        for field in logcomponents:
            ln[f][point][0].set_data(result[point].time, result[point].fields[field])
            if len(koordinates) > 1:
                ax[f][point].autoscale_view(True, True, True)
                ax[f][point].relim()
            else:
                ax[f].autoscale_view(True, True, True)
                ax[f].relim()
            f += 1

    fig.canvas.draw()

"""
This function will plot a graph at the end of the simulation
"""
def onSolverEnd():
    plt.show(block=True)


