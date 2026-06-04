#include "huatai/atsquant/factor/simple_regression.h"
#include <cmath>
#include <limits>

using namespace std;

namespace huatai::atsquant::factor {

void SimpleRegression::addData(double x, double y) {
  if (n == 0) {
    xbar = x;
    ybar = y;
  } else {
    if (hasIntercept) {
      double fact1 = 1.0 + n;
      double fact2 = n / (1.0 + n);
      double dx = x - xbar;
      double dy = y - ybar;
      sumXX += dx * dx * fact2;
      sumYY += dy * dy * fact2;
      sumXY += dx * dy * fact2;
      xbar += dx / fact1;
      ybar += dy / fact1;
    }
  }
  if (!hasIntercept) {
    sumXX += x * x;
    sumYY += y * y;
    sumXY += x * y;
  }
  sumX += x;
  sumY += y;
  n++;
}

void SimpleRegression::clear() {
  sumX = 0;
  sumXX = 0;
  sumY = 0;
  sumYY = 0;
  sumXY = 0;
  n = 0;
}

double SimpleRegression::getSlope() {
  if (n < 2) {
    return NAN;
    // not enough data
  }
  if (fabs(sumXX) < 10 * std::numeric_limits<double>::min()) {
    return NAN;
    // not enough variation in x
  }
  return sumXY / sumXX;
}

double SimpleRegression::getR() {
  double b1 = getSlope();
  double result = sqrt(getRSquare());
  if (b1 < 0) {
    result = -result;
  }
  return result;
}

double SimpleRegression::getRSquare() {
  double ssto = getTotalSumSquares();
  return (ssto - getSumSquaredErrors()) / ssto;
}

long SimpleRegression::getN() { return n; }

double SimpleRegression::getTotalSumSquares() {
  if (n < 2) {
    return NAN;
  }
  return sumYY;
}

double SimpleRegression::getSumSquaredErrors() {
  if (fabs(sumXX) < std::numeric_limits<double>::min()) {
    return NAN;
  }
  return max(0.0, sumYY - sumXY * sumXY / sumXX);
}

double SimpleRegression::getIntercept(double slope) {
  if (hasIntercept) {
    if (n == 0) {
      return NAN;
    }
    return (sumY - slope * sumX) / n;
  }
  return 0;
}

double SimpleRegression::getIntercept() { return hasIntercept ? getIntercept(getSlope()) : 0.0; }

SimpleRegression::SimpleRegression(bool include_intercept) { hasIntercept = include_intercept; }

SimpleRegression::SimpleRegression() : hasIntercept(true) {}

void SimpleRegression::append(const SimpleRegression &reg) {
  if (n == 0) {
    xbar = reg.xbar;
    ybar = reg.ybar;
    sumXX = reg.sumXX;
    sumYY = reg.sumYY;
    sumXY = reg.sumXY;
  } else {
    if (hasIntercept) {
      double fact1 = reg.n / (double)(reg.n + n);
      double fact2 = n * reg.n / (double)(reg.n + n);
      double dx = reg.xbar - xbar;
      double dy = reg.ybar - ybar;
      sumXX += reg.sumXX + dx * dx * fact2;
      sumYY += reg.sumYY + dy * dy * fact2;
      sumXY += reg.sumXY + dx * dy * fact2;
      xbar += dx * fact1;
      ybar += dy * fact1;
    } else {
      sumXX += reg.sumXX;
      sumYY += reg.sumYY;
      sumXY += reg.sumXY;
    }
  }
  sumX += reg.sumX;
  sumY += reg.sumY;
  n += reg.n;
}
} // namespace huatai::atsquant::factor