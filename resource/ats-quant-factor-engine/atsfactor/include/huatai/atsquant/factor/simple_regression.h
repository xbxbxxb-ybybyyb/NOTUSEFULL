#pragma once

#include <algorithm>
#include <cmath>

/**
 * @brief 最小二乘回归模型
 * 线程不安全, 请在多线程调用单实例方法时自行外部做线程同步
 */
namespace huatai::atsquant::factor {

class SimpleRegression {
public:
  // ---------------------Public methods--------------------------------------
  SimpleRegression();

  SimpleRegression(bool include_intercept);

  /**
   * @brief
   * Adds the observation (x,y) to the regression data set.
   * @param x independent variable value
   * @param y dependent variable value
   */
  void addData(double x, double y);

  /**
   * Appends data from another regression calculation to this one.
   *
   * <p>The mean update formulae are based on a paper written by Philippe
   * P&eacute;bay:
   * <a
   * href="http://prod.sandia.gov/techlib/access-control.cgi/2008/086212.pdf">
   * Formulas for Robust, One-Pass Parallel Computation of Covariances and
   * Arbitrary-Order Statistical Moments</a>, 2008, Technical Report
   * SAND2008-6212, Sandia National Laboratories.</p>
   *
   * @param reg model to append data from
   * @since 3.3
   */
  void append(const SimpleRegression &reg);

  /**
   * @brief Clears all data from the model.
   */
  void clear();

  /**
   * @brief Returns the slope of the estimated regression line.
   */
  double getSlope();

  /**
   * Returns <a href="http://mathworld.wolfram.com/CorrelationCoefficient.html">
   * Pearson's product moment correlation coefficient</a>,
   * usually denoted r.
   * @return Pearson's r
   */
  double getR();

  /**
   * @brief Returns the intercept of the estimated regression line, if
   * {@link #hasIntercept()} is true; otherwise 0.
   * @return the intercept of the regression line if the model includes an
   * intercept; 0 otherwise
   */
  double getIntercept();

  /**
   * Returns the number of observations that have been added to the model.
   *
   * @return n number of observations that have been added.
   */
  long getN();

  inline double getRSquare();

  inline double getTotalSumSquares();

  inline double getSumSquaredErrors();

private:
  inline double getIntercept(double slope);

private:
  /** sum of x values */
  double sumX = 0;
  /** total variation in x (sum of squared deviations from xbar) */
  double sumXX = 0;
  /** sum of y values */
  double sumY = 0;
  /** total variation in y (sum of squared deviations from ybar) */
  double sumYY = 0;
  /** sum of products */
  double sumXY = 0;
  /** number of observations */
  long n = 0;
  /** mean of accumulated x values, used in updating formulas */
  double xbar = 0;
  /** mean of accumulated y values, used in updating formulas */
  double ybar = 0;
  /** include an intercept or not */
  bool hasIntercept;
};

} // namespace huatai::atsquant::factor