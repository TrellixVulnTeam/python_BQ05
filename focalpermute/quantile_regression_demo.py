#pylint: skip-file
"""
quantile_regression_demo.py


OVERVIEW

Most of us are familiar with the charts that pediatricians use that show
percentiles of weight and height as a function of age; generating such a chart
from a small sample of data requires quantile regression or similar methods.
(When working with a large enough sample of data, one can bin the data, i.e.,
divide the x-axis into intervals and calculate percentiles independently for
each interval.  But, this approach uses the data inefficiently and is unworkable
when sample sizes are small).

Quantiles and percentiles are the same except for a factor of 100, e.g., the
30th percentile is the 0.3 quantile.

This Python script demonstrates that one can perform quantile regression using
only Python, NumPy, and SciPy.  The only other dependency is on matplotlib,
which is used to plot the data and the quantile estimates.


In detail, the script does the following:


(1) Model parameters are assigned.  (Currently, these are hardwired into the
code).


(2) The program generates an artificial bivariate sample of data (x, y) as
follows:

- x is generated by drawing from a distribution that is uniform on [x_min,
x_max], where x_min and x_max are currently 0 and 1, respectively.

- y is then generated according to a normal distribution having mean -0.5 + x
and standard deviation 1.0 + 0.5 * x.

(All of this can be changed, e.g., one could choose to make the mean of y
quadratic in x).


(3) The code defines an objective function based on the tilted absolute value
function (see references for motivation).


(4) The SciPy optimization package is then used to optimize (minimize) the
objective function.


(5) Using the matplotlib module, the code plots a scatter diagram of the data
with an overlay of percentile lines.


NOTES

My initial approach to this problem was to use the rpy2 interface to the R
statistical environment to invoke the R quantreg package, but the rpy2 module is
severely buggy, and I was unable to make this work.


REFERENCES

1. Journal article, 'Quantile Regression',
http://www.econ.uiuc.edu/~roger/research/rq/QRJEP.pdf

2. Powerpoint slides, 'Robust Statistics and Quantile Regression',
http://www.savbb.sk/~grendar/pdf/robust_quantreg.pdf

3. For an introduction to the Rpy2 interface between Python and R:

http://rpy.sourceforge.net/rpy2/doc-2.1/html/introduction.html

4. Defining R formulas and the associated data is tricky.  For discussion and
examples, see the following:

http://rpy.sourceforge.net/rpy2/doc-2.3/html/robjects_formulae.html


AUTHOR

Dr. Phillip M. Feldman
"""

# Section 1: Import from modules.

from matplotlib import pyplot
import numpy, pdb
from numpy import array, pi
from numpy.polynomial.polynomial import polyval
from scipy.optimize import fmin


# Section 2: Define tilted absolute value function.

def tilted_abs(rho, x):
   """
   OVERVIEW

   The tilted absolute value function is used in quantile regression.


   INPUTS

   rho: This parameter is a probability, and thus takes values between 0 and 1.

   x: This parameter represents a value of the independent variable, and in
   general takes any real value (float) or NumPy array of floats.
   """

   return x * (rho - (x < 0))


# Section 3: Get user input parameters.  Currently, these are hardwired into the
# code.

# `N` is the number of random data points to be generated:
N= 3000

if   N <= 20:
   symbol_size= 100
elif N <= 200:
   symbol_size= 50
else:
   symbol_size= 25

x_min= 0.0; x_max= 1.0

# Define mean and standard deviation of y as functions of x using lambda
# notation:
y_mean= lambda x: -0.5 + x
y_std = lambda x: 1.0 + 0.5 * x

# Define number of polynomial coefficients.  (The degree of the model is one
# more than the number of coefficients).  Specify 2 for a linear model, 3 for a
# quadratic model, and so on.
N_coefficients= 3

fractions= [0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9]

# Define seed (list of integers) for random number generator:
seed= [1, 2, 4]


# Section 4: Generate random datasets x and y.

# Create a random number stream:
RNG= numpy.random.RandomState(seed)

x= RNG.uniform(low=x_min, high=x_max, size=N)
y= y_mean(x) + y_std(x)*RNG.normal(loc=0.0, scale=1.0, size=N)

y_min= y.min(); y_max= y.max()

# Find indices that would sort x values into ascending order:
indices= numpy.argsort(x)

# Apply this sort order to both x and y:
x= x[indices]
y= y[indices]


# Section 5 (deactivated): Use the rpy2 interface to the R statistical
# environment to invoke the quantreg package to estimate quantiles of y as a
# function of x.

# # The R command-prompt syntax that one would use is as follows:

# #    library(quantreg)
# #    formula= ???
# #    fit1 <- rq(formula, tau=fractions)

# R.initr()
# R.library(quantreg)

# formula= R_objects.Formula('y ~ x')
# env= formula.environment
# env['x']= x
# env['y']= y

# fit1= R_objects.rq(formula, tau=fractions)


# Section 6: Estimate quantiles via direct optimization.

def model(x, beta):
   """
   This example defines the model as a polynomial, where the coefficients of the
   polynomial are passed via `beta`.
   """

   return polyval(x, beta)


def objective(beta, rho):
   """
   The objective function to be minimized is the sum of the tilted absolute
   values of the differences between the observations and the model.
   """
   return tilted_abs(rho, y - model(x, beta)).sum()


# Define starting point for optimization:
beta_0= numpy.zeros(N_coefficients)
if N_coefficients >= 2:
   beta_0[1]= 1.0

# `beta_hat[i]` will store the parameter estimates for the quantile
# corresponding to `fractions[i]`:
beta_hat= []

for i, fraction in enumerate(fractions):
   beta_hat.append( fmin(objective, x0=beta_0, args=(fraction,), xtol=1e-8,
     disp=True, maxiter=3000) )


# Section 7: Plot the data with overlays of estimated quantiles.

# Create figure window:
fig= pyplot.figure(figsize=[9,7], dpi=120, facecolor=[1,1,1])

# Plot (x,y) pairs on a scatter diagram.  The argument `s` specifies the symbol
# area in units of points squared.
p1= pyplot.scatter(x, y, s=symbol_size)
pyplot.xlim([x_min, x_max])
pyplot.ylim([y_min, y_max])
pyplot.title("Scatter Diagram with Quantiles Corresponding to\n"
  "the Fractions %s\n" % str(fractions)[1:-1], size=18)
pyplot.xlabel("x", size=18)
pyplot.ylabel("y", size=18)

# Enable 'hold' so that lines will be plotted as overlays on scatter diagram
# rather than in separate figure windows:
pyplot.hold(True)

# Draw a line for each quantile:
for i, fraction in enumerate(fractions):
   pyplot.plot(x, polyval(x, beta_hat[i]), linewidth=2)

pyplot.grid(True)

# Nothing is displayed until we invoke `show`:
pyplot.show()
