# Name:			CellAnalyzer.py
# Summary:		Methods to extract characteristics from cell IV curves and provides interpretable graphs.
#   
# Limitations:  Currently only supports 2-probe measurements.
# Refinement:	Clean up comments.

#import dependencies  
import numpy as np
import pandas as pd
from scipy.stats import linregress
from functools import cached_property

from src.utils.CsvFile import CsvFile



# Name:			__init__
# Summary:		.
# Desc:			Constructs the R_on data handler
# Refinement:	.
#
# Input:		csvItem : csvItem
#                   Item containing metadata of the CSV file
#               set_thresh : float
#                   Hyperparameter controlling detection of Set/Form voltage. See `set_voltage()` for more info
#               linear_thresh : float
#                   Hyperparameter controlling 
# Output:		.

# Name:			.
# Summary:		.
# Desc:			Takes the csv file and returns a pandas data frame
# Refinement:	.
#
# Input:		None.
# Output:		.
def calcDataFrame(csv_file: CsvFile, set_thresh: float=0.9, linear_thresh: float=5e-3) -> pd.DataFrame:
    df = pd.DataFrame({
        'AI': csv_file.probeA_current,
        'AV': csv_file.probeA_voltage,
        'Time': csv_file.timeAxis
    })

    return df

# Name:			.
# Summary:		.
# Desc:			Calculates the set voltage for a set or form CSV file.
#    
#               Checks when the current crosses `set_thresh * Icc`. Result is cached after first calculation.
# Refinement:	.
#
# Input:		None.
# Output:		voltage : float or None
#                   Returns voltage of the last crossing instance. Returns `None` if 
#                   no crossing is found (e.g. non-conductive cell that remains in nano-Ampère range)    
def calcSetVoltage(csv_file, df, set_thresh: float=0.9):  #self.df
    if not csv_file.activity in ['set', 'form']:
        raise Exception(f"set_voltage() called on data from {csv_file.activity}")  #{self.activity()}: {self.file}
    
    # get the compliance current from the CSV file name
    units = {'uA': 1e-6, 'mA': 1e-3}
    icc = float(csv_file.complianceCurrent) * units.get(csv_file.complianceCurrentUnits, 1)

    # we're going to assume that the cell has set after it achieves 90% of Icc
    threshold = set_thresh * icc

    series = df['AI'].values >= threshold
    d = np.diff(series)

    # to avoid janky starting curves, take the last time the current crossed the threshold
    crosses = np.argwhere(d)

    if len(crosses) == 0:
        return None

    # argwhere will return output in form of shape (n_crossings, 1),
    # so take the last instance and then remove the value from the 0d np array
    idx = crosses[-1][0]
    voltage = df.at[idx, 'AV'] # get the voltage at the crossing

    return voltage

# Name:			.
# Summary:		.
# Desc:			.
# Refinement:	.
#
# Input:		None.
# Output:		The first index of data corresponding to a nonlinear jump, as a __.
def __linear_idx(df, linear_thresh: float=5e-3):
    # theory here is that the 2nd derivative of the linear portion of the current data will be 0,
    # while the sudden nonlinear jumps will have a nonzero 2nd derivative
    # so this gives us a signal and we compare the jumps against the `linear_thresh` hyperparameter
    #
    # Formula comes from https://en.wikipedia.org/wiki/Finite_difference#Higher-order_differences (see second order central derivative formula)

    i = df['AI'].values
    v = df['AV'].values

    # take the average voltage steps as 'dv' for derivative di/dv
    dv = np.mean(np.diff(v))
    # use convolution to perform the second order formula, will crop off first and last data element
    di2 = np.convolve(i, np.array([1, -2, 1]), mode='valid')

    didv2 = di2 / dv ** 2

    # check for large jumps in 2nd derivative against hyperparameter
    # giving a binary signal
    series = np.abs(didv2) >= linear_thresh
    # take difference of binary signal to find 'crossing points'
    d = np.diff(series)

    jumps = np.argwhere(d)

    if len(jumps) == 0:
        return None

    # first instance of a major jump
    idx = np.min(jumps) + 1   # add +1 since this index really starts at 1 for the data series due to the mode='valid' in convolution
    
    return idx

# Name:			.
# Summary:		.
# Desc:			Returns the region where the algorithm thinks the curve is sufficiently linear
#    
#               Only works on reset curves
# Refinement:	.
#
# Input:		.
# Output:		(v_min, v_max) : A tuple consisting of the linear voltage region    
def linear_voltage_regime(df):
    v = df['AV'].values

    if __linear_idx(df):
        v = v[:__linear_idx(df)]

    return v.min(), v.max()

# Name:			.
# Summary:		.
# Desc:			Tries to determine the R_on for a cell using the reset curve
#    
#               After calculation, the R2 value of the linear fit will be stored in the `r2` property.
#               Makes use of `linear_thresh` hyperparameter. Value is cached after first call, accessed by property not method.
#
#               On resistance is calculated by fitting a line to linear region of IV curve. Then, resistance is 1 / slope of that line.
# Refinement:	.
#
# Input:		.
# Output:		resistance : float or None
#                   Detected R_on of the cell, or `None` if the data was too nonlinear
#               r2 : float
#                   Linear best fit quality, indirectly returned in property `r2`.
def calcResistance(csv_file, df):
    if not csv_file.activity == 'reset':
        raise Exception(f"resistance() called on data from {csv_file.activity}")
    
    idx = __linear_idx(df)
    i = df['AI'].values
    v = df['AV'].values

    # crop data if we found nonlinearities
    if idx is not None:
        i, v = i[:idx], v[:idx]

    # now we will take the data up until idx and perform a linear fit to it to obtain the resistance
    s_on, _, r, _, _ = linregress(v[:idx], i[:idx])
    r_on = 1 / s_on     # slope of IV curve is conductance
    r2 = r ** 2    # store R^2 value from linear fit too

    return r_on, r2  #add r2 as an output 

# Name:			.
# Summary:		.
# Desc:			Calculates the true ramp rate of the data in V/s.
# Refinement:	.
#
# Input:		.
# Output:		.    
def calcRampRate(csv_file, df) -> float:
    if csv_file.activity == 'observe':
        raise Exception(f"ramp_rate() called on data from observe")

    v = np.abs(df['AV'].values)
    series = v >= 1
    d = np.diff(series)

    crosses = np.argwhere(d)

    if len(crosses) == 0:
        return df['AV'][-1] / df['Time'][-1]
    
    else:
        idx = crosses[0][0]

        return df['AV'][idx] / df['Time'][idx]

# Name:			.
# Summary:		Calculates the amount of energy being input into the system as a cumulative distribution
#               only works on successful resets at this time, as the voltage at compliance current is not
#               properly handled yet
# Desc:			.
# Refinement:	.
#
# Input:		.
# Output:		.    
def energy_input(csv_file, df) -> np.ndarray:
    if not csv_file.activity in ['observe', 'reset']:
        raise Exception(f"energy_input() called on data from not from observe or reset")

    
    time = df['Time']
    i = df['AI']
    v = np.abs(df['AV'])


    #calculate the length of each timestep using a discrete first order derivative
    dt = np.convolve(time, np.array([-0.5, 0, 0.5]), mode='same')

    e = i * v * dt
    e = np.cumsum(e, 0)
    #the last measurement in the array will have a large negative time value so to keep things simple
    #the last value in the distribution is just set to match the one immediately prior
    e[len(e) - 1] = e[len(e) - 2]
    return e

# Name:			.
# Summary:		.
# Desc:			.
# Refinement:	.
#
# Input:		.
# Output:		.
def plot_energy(csv_file, df, outfile: str):
    
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set_palette('pastel')
    
    fig = plt.figure(figsize=(10, 4), dpi=300)
    fig.patch.set_facecolor('white')
    sns.lineplot(x=df.Time, y=energy_input(csv_file, df))
    plt.xlabel("Time (seconds)")
    plt.ylabel("Energy (J)")

    plt.savefig(outfile)
    plt.close()
    
# Name:			.
# Summary:		.
# Desc:			Plots IV-curve annotated with what the algorithm interpreted from the data, and saves in `outfile`
# Refinement:	.
#
# Input:		.
# Output:		.
def plot(csv_file, df, outfile: str, set_thresh: float=0.9):
    #import libs
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    #
    sns.set_palette('pastel')

    # create high quality figure and plot IV curve
    fig = plt.figure(figsize=(10, 4), dpi=300)
    fig.patch.set_facecolor('white')
    sns.lineplot(x=df.AV, y=df.AI)
    plt.xlabel("Voltage $V$ [V]")
    plt.ylabel("Current $I$ [A]")

    # here we draw a vertical red line at the voltage where the cell was set
    # and put the voltage in the title
    if csv_file.activity in ['set', 'form']:
        if calcSetVoltage(csv_file, df, set_thresh) is None:
            plt.title(f'{csv_file.activity}: No thresh detected')
        else:
            plt.title(f'{csv_file.activity}: {calcSetVoltage(csv_file, df, set_thresh):.2f} V')
            plt.vlines(calcSetVoltage(csv_file, df, set_thresh), df.AI.min(), df.AI.max(), colors='r')

    # draw a light gray background region behind where the data was linear
    # and put the resistance/R2 values in the title
    elif csv_file.activity == 'reset':
        r_on, r2 = calcResistance(csv_file, df)
        if r_on is None:
            plt.title('reset: Too nonlinear')
        else:
            plt.title(f'Reset: (R_on = {r_on:.2f} Ω, R2 = {r2:.3f})')
            x_min, x_max = linear_voltage_regime(df)
            plt.axvspan(x_min, x_max, facecolor='0.95', zorder=-100)
    
    plt.savefig(outfile)
    plt.close()
