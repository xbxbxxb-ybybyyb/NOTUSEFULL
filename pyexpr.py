from collections import * 
import pandas as pd
import numpy as np
import pdb
class basic_operator(object):
    def __init__(self, argnum):
        self.argnum_ = argnum
    def calc(self, arg):
        pass
    def calc(self, arg1, arg2):
        pass
    def calc(self, arg1, arg2, arg3):
        pass
    def argnum(self):
        return self.argnum_ 

class operator_add(basic_operator):
    def __init__(self):
        super(operator_add, self).__init__(2)
    def calc(self, arg1, arg2):
        return arg1 + arg2

class operator_sub(basic_operator):
    def __init__(self):
        super(operator_sub, self).__init__(2)
    def calc(self, arg1, arg2):
        return arg1 - arg2

class operator_mul(basic_operator):
    def __init__(self):
        super(operator_mul, self).__init__(2)
    def calc(self, arg1, arg2):
        return arg1 * arg2
class operator_div(basic_operator):
    def __init__(self):
        super(operator_div, self).__init__(2)
    def calc(self, arg1, arg2):
        return arg1 / arg2

class operator_div(basic_operator):
    def __init__(self):
        super(operator_div, self).__init__(2)
    def calc(self, arg1, arg2):
        return arg1 / arg2


class operator_svd(basic_operator):
    def __init__(self):
        super(operator_svd, self).__init__(2)


    def calc(self, arg1, arg2):
      """Return a new df
        X:raw input
        kp:kp
        axis:demean direction, if -1, do not demean
        allownan:if True, then will delete some all nan rows
        """
      X = arg1
      kp = arg2[0][0]
      axis = -1
      allownan = True

      ld = X.replace(-np.inf,np.nan)
      ld = ld.replace(np.inf,np.nan)
      ld = ld.replace(-np.nan,np.nan)
      ld = ld.dropna(axis=1,how='all')#delete col contains all nan
      ld = ld.dropna(axis=0,how='all')#delete row contains all nan
      ld = ld.dropna(axis=1,how='any')#delete col contains any nan
      
    
      if (allownan == False):
        if (ld.shape[0] != X.shape[0]):
          return pd.DataFrame()#null
    
    
      if (axis == 0):
        ld = ld - ld.mean(axis=0)
      elif (axis == 1):
        ld = ld.sub(ld.mean(axis=1), axis=0)
    
      from numpy.linalg import svd
      a = ld.values
      aa = a.dot(a.T)
      ww,dd,vv = svd(aa)
      for i in range(len(dd)): dd[i] = np.sqrt(dd[i])
      nv = ww.T.dot(a)
      s = nv.shape
      height = s[0]
      width = s[1]
      for i in range(height):
        for j in range(width):
          if (np.abs(dd[i]) > 1e-9):
            nv[i][j] = nv[i][j] / dd[i]
      for i in range(len(dd)):
        if (i < kp): dd[i] = 0
      res = ww.dot(np.diag(dd)).dot(nv)
      #step by step code
      #print(res1)
      #res = np.zeros([height, width], dtype='float32')
      #for rid in range(height):
      #  for i in range(width):
      #    for j in range(height):
      #      res[rid][i] = res[rid][i] + dd[j] * ww[rid][j] * nv[j][i]
      ans = pd.DataFrame(res, columns = ld.columns, index=ld.index)
      return ans


#class operator_sqrt : public basic_operator
#{
#public:
#	operator_sqrt() {argnum_ = 1 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        ans[i][j] = sqrt(fabs(arg1[i][j]))
#      }
#    }
#    return ans 
#  }
#}
#
#/* sin */
#class operator_sin : public basic_operator
#{
#public:
#	operator_sin() {argnum_ = 1 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        ans[i][j] = sin(arg1[i][j])
#      }
#    }
#    return ans 
#  }
#}
#
#class operator_cos : public basic_operator
#{
#public:
#	operator_cos() {argnum_ = 1 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        ans[i][j] = cos(arg1[i][j])
#      }
#    }
#    return ans 
#  }
#}
#
#/* lg , log10 */
#class operator_lg : public basic_operator
#{
#public:
#	operator_lg() {argnum_ = 1 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        ans[i][j] = log10(arg1[i][j])
#      }
#    }
#    return ans 
#  }
#}
#
#/* ln, nature logarithm  */
#class operator_ln : public basic_operator
#{
#public:
#	operator_ln() {argnum_ = 1 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        ans[i][j] = log(arg1[i][j])
#      }
#    }
#    return ans 
#  }
#}
#
#/* ln, nature logarithm  */
#class operator_abs : public basic_operator
#{
#public:
#	operator_abs() {argnum_ = 1 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        ans[i][j] = fabs(arg1[i][j])
#      }
#    }
#    return ans 
#  }
#}
#
#/* ln, nature logarithm  */
#class operator_sign: public basic_operator
#{
#public:
#	operator_sign() {argnum_ = 1 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        if (arg1[i][j] > 0) ans[i][j] = 1.0
#        else if (arg1[i][j] < 0) ans[i][j] = -1.0
#        else ans[i][j] = 0.0
#      }
#    }
#    return ans 
#  }
#}
#/* + */
#class operator_greater: public basic_operator
#{
#public:
#	operator_greater() {argnum_ = 2 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        if (arg1[i][j] > arg2[i][j]) ans[i][j] = 1.0
#        else if (arg1[i][j] < arg2[i][j]) ans[i][j] = -1.0
#        else ans[i][j] = 0.0
#      }
#    }
#    return ans 
#  }
#}
#
#class operator_less: public basic_operator
#{
#public:
#	operator_less() {argnum_ = 2 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        if (arg1[i][j] < arg2[i][j]) ans[i][j] = 1.0
#        else if (arg1[i][j] > arg2[i][j]) ans[i][j] = -1.0
#        else ans[i][j] = 0.0
#      }
#    }
#    return ans 
#  }
#}
#class operator_max: public basic_operator
#{
#public:
#	operator_max() {argnum_ = 2 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        if (arg1[i][j] < arg2[i][j]) ans[i][j] = arg2[i][j]
#      }
#    }
#    return ans 
#  }
#}
#
#class operator_min: public basic_operator
#{
#public:
#	operator_min() {argnum_ = 2 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        if (arg1[i][j] > arg2[i][j]) ans[i][j] = arg2[i][j]
#      }
#    }
#    return ans 
#  }
#}
#class operator_equal: public basic_operator
#{
#public:
#	operator_equal() {argnum_ = 2 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        if (arg1[i][j] == arg2[i][j]) ans[i][j] = 1.0
#        else ans[i][j] = 0.0
#      }
#    }
#    return ans 
#  }
#}
#class operator_or: public basic_operator
#{
#public:
#	operator_or() {argnum_ = 2 }
#	virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#    vector<vector<double>> ans = arg1
#    for (int i = 0i < arg1.size()++i) {
#      for (int j = 0j < arg1[i].size()++j) {
#        if (arg1[i][j] || arg2[i][j]) ans[i][j] = 1.0
#        else ans[i][j] = 0.0
#      }
#    }
#    return ans 
#  }
#}
#
#class operator_rank: public basic_operator
#{
#  public:
#    operator_rank() {argnum_ = 1 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        CRankUniform<double>()(ans[i])
#      }
#      return ans 
#    }
#}
#class operator_delay: public basic_operator
#{
#  public:
#    operator_delay() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          int bd = (int)(round(arg2[i][j]))
#          if (i - bd > 0) {
#            ans[i][j] = arg1[i - bd][j]
#          } else {
#            ans[i][j] = NAN
#          }
#        }
#      }
#      return ans 
#    }
#}
#class operator_condition: public basic_operator
#{
#  public:
#    operator_condition() {argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      vector<vector<double>> ans = arg2
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          if (!arg1[i][j]) ans[i][j] = arg3[i][j]
#        }
#      }
#      return ans 
#    }
#}
#class operator_correlation: public basic_operator
#{
#  public:
#    operator_correlation() {argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      int bd = (int)(round(arg3[0][0]))
#      vector<vector<double>> ans = cov(arg1, arg2, bd, 0.5, true)
#      return ans 
#    }
#}
#class operator_covariance: public basic_operator
#{
#  public:
#    operator_covariance() {argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      int bd = (int)(round(arg3[0][0]))
#      vector<vector<double>> ans = cov(arg1, arg2, bd, 0.5, False)
#      return ans 
#    }
#}
#class operator_scale: public basic_operator
#{
#  public:
#    operator_scale() {argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        double sum = 0
#        for (int j = 0j < arg1[i].size()++j) {
#          if (std::isnan(arg1[i][j])) continue
#          if (std::isinf (arg1[i][j])) continue
#          sum += fabs(arg1[i][j])
#        }
#        if (sum > 0) {
#          for (int j = 0j < arg1[i].size()++j) {
#            arg1[i][j] = arg1[i][j] / sum * arg2[i][j]
#          }
#        }
#      }
#      return ans 
#    }
#}
#class operator_delta: public basic_operator
#{
#  public:
#    operator_delta() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          int bd = (int)(round(arg2[i][j]))
#          if (i - bd > 0) {
#            ans[i][j] = arg1[i][j] - arg1[i - bd][j]
#          } else {
#            ans[i][j] = NAN
#          }
#        }
#      }
#      return ans 
#    }
#}
#class operator_signedpower: public basic_operator
#{
#  public:
#    operator_signedpower() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = pow(fabs(arg1[i][j]), arg2[i][j])
#        }
#      }
#      return ans 
#    }
#}
#class operator_decay_linear: public basic_operator
#{
#  public:
#    operator_decay_linear() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double up = 0.0
#          double down = 0.0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(arg1[i - z][j]) || std::isinf(arg1[i - z][j])) continue
#            up += arg1[i - z][j] * (bd - z)
#            down += (bd - z)
#          }
#          up = (down > 0)?up / down:NAN
#          ans[i][j] = up
#        }
#      }
#      return ans 
#    }
#}
#class operator_indneutralize: public basic_operator
#{
#  public:
#    operator_indneutralize() {argnum_ = 2 }
#    //virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) {
#    //  return 0
#    //}
#}
#class operator_ts_min: public basic_operator
#{
#  public:
#    operator_ts_min() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (arg1[i - z][j] < ans[i][j]) {
#              ans[i][j] = arg1[i - z][j]
#            }
#          }
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_max: public basic_operator
#{
#  public:
#    operator_ts_max() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (arg1[i - z][j] > ans[i][j]) {
#              ans[i][j] = arg1[i - z][j]
#            }
#          }
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_argmax: public basic_operator
#{
#  public:
#    operator_ts_argmax() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double v = NAN
#          int maxi = 0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(v) || arg1[i - z][j] > v) {
#              maxi = z
#              v = arg1[i - z][j]
#            }
#          }
#          ans[i][j] = maxi
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_argmin: public basic_operator
#{
#  public:
#    operator_ts_argmin() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double v = NAN
#          int mini = 0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(v) || arg1[i - z][j] < v) {
#              mini = z
#              v = arg1[i - z][j]
#            }
#          }
#          ans[i][j] = mini
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_rank: public basic_operator
#{
#  public:
#    operator_ts_rank() {argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      int r = arg1.size()
#      int c = arg1[0].size()
#      vector<vector<double>> ans = vector<vector<double>>(r, vector<double>(c, NAN))
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          if (i < bd - 1) continue
#          vector<double> t(bd, 0.0)
#          for (int z = 0z < bd++z) t[z] = arg1[i - z][j]
#          CRankUniform<double>()(t)
#          ans[i][j] = t[0]
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_sum: public basic_operator
#{
#  public:
#    operator_ts_sum() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double v = 0.0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(arg1[i - z][j]) || std::isinf(arg1[i - z][j])) continue
#            v += arg1[i - z][j]
#          }
#          ans[i][j] = v
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_product: public basic_operator
#{
#  public:
#    operator_ts_product() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double v = 1.0
#          int cnt = 0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(arg1[i - z][j]) || std::isinf(arg1[i - z][j])) continue
#            v *= arg1[i - z][j]
#            cnt += 1
#          }
#          if (cnt == 0) v = NAN
#          ans[i][j] = v
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_demean: public basic_operator
#{
#  public:
#    operator_ts_demean() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double v = 0.0
#          double c = 0.0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(arg1[i - z][j]) || std::isinf(arg1[i - z][j])) continue
#            v += arg1[i - z][j]
#            c += 1.0
#          }
#          if (c <= 1) {
#            ans[i][j] = 0.0
#          } else {
#            v /= c
#            ans[i][j] = arg1[i][j] - v
#          }
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_normalize: public basic_operator
#{
#  public:
#    operator_ts_normalize() {argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double v = 0.0
#          double v2 = 0.0
#          double c = 0.0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(arg1[i - z][j]) || std::isinf(arg1[i - z][j])) continue
#            v += arg1[i - z][j]
#            v2 += arg1[i - z][j] * arg1[i - z][j]
#            c += 1.0
#          }
#          if (c <= 1) {
#            ans[i][j] = 0.0
#          } else {
#            v /= c
#            v2 /= c
#            double sigma = sqrt(v2 - v * v)
#            if (sigma > 0) {
#              ans[i][j] = (arg1[i][j] - v) / sigma
#            }
#          }
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_std: public basic_operator
#{
#  public:
#    operator_ts_std() {argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double v = 0.0
#          double v2 = 0.0
#          double c = 0.0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(arg1[i - z][j]) || std::isinf(arg1[i - z][j])) continue
#            v += arg1[i - z][j]
#            v2 += arg1[i - z][j] * arg1[i - z][j]
#            c += 1.0
#          }
#          if (c <= 1) {
#            ans[i][j] = 0.0
#          } else {
#            v /= c
#            v2 /= c
#            ans[i][j] = sqrt(v2 - v * v)
#          }
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_skew: public basic_operator
#{
#  public:
#    operator_ts_skew() {argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          vector<double> lv
#
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(arg1[i - z][j]) || std::isinf(arg1[i - z][j])) continue
#            lv.push_back(arg1[i - z][j])
#          }
#          ans[i][j] = getSkewness(lv)
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_kurt: public basic_operator
#{
#  public:
#    operator_ts_kurt() {argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          vector<double> lv
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(arg1[i - z][j]) || std::isinf(arg1[i - z][j])) continue
#            lv.push_back(arg1[i - z][j])
#          }
#          ans[i][j] = getKurtosis(lv)
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_peak: public basic_operator
#{
#  public:
#    operator_ts_peak() {argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#
#          int bd = (int)(round(arg2[i][j]))
#          double up = 0.0
#          for (int z = 1z <= bd++z) {
#            if (i - z - 1 < 0) continue
#            double v0 = arg1[i - z][j]
#            double v1 = arg1[i - z - 1][j]
#            double v2 = arg1[i - z + 1][j]
#            if (std::isnan(v0) || std::isinf(v0)) continue
#            if (std::isnan(v1) || std::isinf(v1)) continue
#            if (std::isnan(v2) || std::isinf(v2)) continue
#            if (v0 > v1 && v0 > v2) up += 1.0
#          }
#          ans[i][j] = up / bd
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_upeak: public basic_operator
#{
#  public:
#    operator_ts_upeak() {argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double up = 0.0
#          for (int z = 1z <= bd++z) {
#            if (i - z - 1 < 0) continue
#            double v0 = arg1[i - z][j]
#            double v1 = arg1[i - z - 1][j]
#            double v2 = arg1[i - z + 1][j]
#            if (std::isnan(v0) || std::isinf(v0)) continue
#            if (std::isnan(v1) || std::isinf(v1)) continue
#            if (std::isnan(v2) || std::isinf(v2)) continue
#            if (v0 < v1 && v0 < v2) up += 1.0
#          }
#          ans[i][j] = up / bd
#        }
#      }
#      return ans 
#    }
#}
#
#class operator_ts_centroid: public basic_operator
#{
#  public:
#    operator_ts_centroid() { argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double up = 0.0
#          double down = 0.0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double v0 = arg1[i - z][j]
#            if (std::isnan(v0) || std::isinf(v0)) continue
#            up += (z + 1) * v0 * v0
#            down += v0 * v0
#          }
#          ans[i][j] = (down > 0)?up / down / bd - 0.5:NAN
#        }
#      }
#      return ans 
#    }
#}
#
#class operator_ts_meanabsdiff: public basic_operator
#{
#  public:
#    operator_ts_meanabsdiff() { argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double up = 0.0
#          double down = 0.0
#          for (int z = 0z < bd++z) {
#            if (i - z - 1 < 0) continue
#            double v0 = arg1[i - z][j]
#            double v1 = arg1[i - z - 1][j]
#            if (std::isnan(v0) || std::isinf(v0)) continue
#            if (std::isnan(v1) || std::isinf(v1)) continue
#            up += fabs(v0 - v1)
#            down += 1.0
#          }
#          ans[i][j] = (down > 0)?up / down:NAN
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_meandiff: public basic_operator
#{
#  public:
#    operator_ts_meandiff() { argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          if (i - bd < 0) {
#            ans[i][j] = NAN
#          } else {
#            ans[i][j] = arg1[i][j] - arg1[i - bd][j]
#          }
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_distance: public basic_operator
#{
#  public:
#    operator_ts_distance() { argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double up = 0.0
#          double down = 0.0
#          for (int z = 0z < bd++z) {
#            if (i - z - 1 < 0) continue
#            double v0 = arg1[i - z][j]
#            if (std::isnan(v0) || std::isinf(v0)) continue
#            up += sqrt(v0 * v0 + 1.0)
#            down += 1.0
#          }
#          ans[i][j] = (down > 0)?up / down - 1.0:NAN
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_peaktopeak: public basic_operator
#{
#  public:
#    operator_ts_peaktopeak() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double max = NAN
#          double min = NAN
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(max) || arg1[i - z][j] > max) max = arg1[i - z][j]
#            if (std::isnan(min) || arg1[i - z][j] < min) min= arg1[i - z][j]
#          }
#          ans[i][j]= max - min
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_peakitopeaki: public basic_operator
#{
#  public:
#    operator_ts_peakitopeaki() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double max = NAN
#          double maxi = NAN
#          double min = NAN
#          double mini = NAN
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(max) || arg1[i - z][j] > max) {
#              max = arg1[i - z][j]
#              maxi = z
#            }
#            if (std::isnan(min) || arg1[i - z][j] < min) {
#              min = arg1[i - z][j]
#              mini = z
#            }
#          }
#          ans[i][j] = maxi - mini
#        }
#      }
#      return ans 
#    }
#}
#
#class operator_ts_slope: public basic_operator
#{
#  public:
#    operator_ts_slope() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          //X = [x1, x2.. xn]
#          //Y = [x1, x2.. xn]
#          //
#          //[ sum(yi^2) sum(yi)  * [a] = [sum(xi * yi) 
#          //  sum(yi)   sum(1) ]   [b]    sum(xi)
#          //use A B C D to keep the 
#          // [A B  inverse = [D -B
#          //  C D]           -C  A] / (AD - BC) 
#          //
#          double A = 0
#          double B = 0//B = C
#          double D = 0
#          double XY = 0
#          double SUMY = 0
#
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x = bd - z
#            double y = arg1[i - z][j]
#            if (std::isnan(y) || std::isinf(y)) continue
#
#            A += x * x
#            B += x
#            D += 1.0
#
#            XY += x * y
#            SUMY += y
#          }
#          if (A * D - B * B <= 0) {
#            ans[i][j] = NAN
#            continue
#          }
#          double a = (D * XY - B * SUMY) / (A * D - B * B)
#          double b = (-B * XY + A * SUMY) / (A * D - B * B)
#          //residual = y[i][j] - (a * x[i][j] + b)
#          ans[i][j] = a//slope
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_intercept: public basic_operator
#{
#  public:
#    operator_ts_intercept() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          //X = [x1, x2.. xn]
#          //Y = [x1, x2.. xn]
#          //
#          //[ sum(yi^2) sum(yi)  * [a] = [sum(xi * yi) 
#          //  sum(yi)   sum(1) ]   [b]    sum(xi)
#          //use A B C D to keep the 
#          // [A B  inverse = [D -B
#          //  C D]           -C  A] / (AD - BC) 
#          //
#          double A = 0
#          double B = 0//B = C
#          double D = 0
#          double XY = 0
#          double SUMY = 0
#
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x = bd - z
#            double y = arg1[i - z][j]
#            if (std::isnan(y) || std::isinf(y)) continue
#
#            A += x * x
#            B += x
#            D += 1.0
#
#            XY += x * y
#            SUMY += y
#          }
#          if (A * D - B * B <= 0) {
#            ans[i][j] = NAN
#            continue
#          }
#          double a = (D * XY - B * SUMY) / (A * D - B * B)
#          double b = (-B * XY + A * SUMY) / (A * D - B * B)
#          //residual = y[i][j] - (a * x[i][j] + b)
#          ans[i][j] = b//slope
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_residual: public basic_operator
#{
#  public:
#    operator_ts_residual() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          //X = [x1, x2.. xn]
#          //Y = [x1, x2.. xn]
#          //
#          //[ sum(yi^2) sum(yi)  * [a] = [sum(xi * yi) 
#          //  sum(yi)   sum(1) ]   [b]    sum(xi)
#          //use A B C D to keep the 
#          // [A B  inverse = [D -B
#          //  C D]           -C  A] / (AD - BC) 
#          //
#          double A = 0
#          double B = 0//B = C
#          double D = 0
#          double XY = 0
#          double SUMY = 0
#
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x = bd - z
#            double y = arg1[i - z][j]
#            if (std::isnan(y) || std::isinf(y)) continue
#
#            A += x * x
#            B += x
#            D += 1.0
#
#            XY += x * y
#            SUMY += y
#          }
#          if (A * D - B * B <= 0) {
#            ans[i][j] = NAN
#            continue
#          }
#          double a = (D * XY - B * SUMY) / (A * D - B * B)
#          double b = (-B * XY + A * SUMY) / (A * D - B * B)
#          //residual = y[i][j] - (a * x[i][j] + b)
#          ans[i][j] = arg1[i][j] - (a * bd + b)
#        }
#      }
#      return ans 
#    }
#}
#
#class operator_ts_slopey: public basic_operator
#{
#  public:
#    operator_ts_slopey() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg3[i][j]))
#          //X = [x1, x2.. xn]
#          //Y = [x1, x2.. xn]
#          //
#          //[ sum(yi^2) sum(yi)  * [a] = [sum(xi * yi) 
#          //  sum(yi)   sum(1) ]   [b]    sum(xi)
#          //use A B C D to keep the 
#          // [A B  inverse = [D -B
#          //  C D]           -C  A] / (AD - BC) 
#          //
#          double A = 0
#          double B = 0//B = C
#          double D = 0
#          double XY = 0
#          double SUMY = 0
#
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x = arg2[i - z][j]
#            double y = arg1[i - z][j]
#            if (std::isnan(y) || std::isinf(y)) continue
#            if (std::isnan(x) || std::isinf(x)) continue
#
#            A += x * x
#            B += x
#            D += 1.0
#
#            XY += x * y
#            SUMY += y
#          }
#          if (A * D - B * B <= 0) {
#            ans[i][j] = NAN
#            continue
#          }
#          double a = (D * XY - B * SUMY) / (A * D - B * B)
#          double b = (-B * XY + A * SUMY) / (A * D - B * B)
#          //residual = y[i][j] - (a * x[i][j] + b)
#          ans[i][j] = a//slope
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_intercepty: public basic_operator
#{
#  public:
#    operator_ts_intercepty() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg3[i][j]))
#          //X = [x1, x2.. xn]
#          //Y = [x1, x2.. xn]
#          //
#          //[ sum(yi^2) sum(yi)  * [a] = [sum(xi * yi) 
#          //  sum(yi)   sum(1) ]   [b]    sum(xi)
#          //use A B C D to keep the 
#          // [A B  inverse = [D -B
#          //  C D]           -C  A] / (AD - BC) 
#          //
#          double A = 0
#          double B = 0//B = C
#          double D = 0
#          double XY = 0
#          double SUMY = 0
#
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x = arg2[i - z][j]
#            double y = arg1[i - z][j]
#            if (std::isnan(x) || std::isinf(x)) continue
#            if (std::isnan(y) || std::isinf(y)) continue
#
#            A += x * x
#            B += x
#            D += 1.0
#
#            XY += x * y
#            SUMY += y
#          }
#          if (A * D - B * B <= 0) {
#            ans[i][j] = NAN
#            continue
#          }
#          double a = (D * XY - B * SUMY) / (A * D - B * B)
#          double b = (-B * XY + A * SUMY) / (A * D - B * B)
#          //residual = y[i][j] - (a * x[i][j] + b)
#          ans[i][j] = b//slope
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_residualy: public basic_operator
#{
#  public:
#    operator_ts_residualy() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg3[i][j]))
#          //X = [x1, x2.. xn]
#          //Y = [x1, x2.. xn]
#          //
#          //[ sum(yi^2) sum(yi)  * [a] = [sum(xi * yi) 
#          //  sum(yi)   sum(1) ]   [b]    sum(xi)
#          //use A B C D to keep the 
#          // [A B  inverse = [D -B
#          //  C D]           -C  A] / (AD - BC) 
#          //
#          double A = 0
#          double B = 0//B = C
#          double D = 0
#          double XY = 0
#          double SUMY = 0
#
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x = arg2[i - z][j]
#            double y = arg1[i - z][j]
#            if (std::isnan(y) || std::isinf(y)) continue
#            if (std::isnan(x) || std::isinf(x)) continue
#
#            A += x * x
#            B += x
#            D += 1.0
#
#            XY += x * y
#            SUMY += y
#          }
#          if (A * D - B * B <= 0) {
#            ans[i][j] = NAN
#            continue
#          }
#          double a = (D * XY - B * SUMY) / (A * D - B * B)
#          double b = (-B * XY + A * SUMY) / (A * D - B * B)
#          //residual = y[i][j] - (a * x[i][j] + b)
#          ans[i][j] = arg1[i][j] - (a * arg2[i][j] + b)
#        }
#      }
#      return ans 
#    }
#}
#class operator_ts_residualr2y: public basic_operator
#{
#  public:
#    operator_ts_residualr2y() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg3[i][j]))
#          //X = [x1, x2.. xn]
#          //Y = [x1, x2.. xn]
#          //
#          //[ sum(yi^2) sum(yi)  * [a] = [sum(xi * yi) 
#          //  sum(yi)   sum(1) ]   [b]    sum(xi)
#          //use A B C D to keep the 
#          // [A B  inverse = [D -B
#          //  C D]           -C  A] / (AD - BC) 
#          //
#          double A = 0
#          double B = 0//B = C
#          double D = 0
#          double XY = 0
#          double SUMY = 0
#
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x = arg2[i - z][j]
#            double y = arg1[i - z][j]
#            if (std::isnan(y) || std::isinf(y)) continue
#            if (std::isnan(x) || std::isinf(x)) continue
#
#            A += x * x
#            B += x
#            D += 1.0
#
#            XY += x * y
#            SUMY += y
#          }
#          if (A * D - B * B <= 0) {
#            ans[i][j] = NAN
#            continue
#          }
#          double a = (D * XY - B * SUMY) / (A * D - B * B)
#          double b = (-B * XY + A * SUMY) / (A * D - B * B)
#          //residual = y[i][j] - (a * x[i][j] + b)
#          ans[i][j] = 0.0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x = arg2[i - z][j]
#            double y = arg1[i - z][j]
#            if (std::isnan(y) || std::isinf(y)) continue
#            if (std::isnan(x) || std::isinf(x)) continue
#            ans[i][j] += (y - (a * x + b)) * (y - (a * x + b))
#          }
#          ans[i][j] /= bd
#        }
#      }
#      return ans 
#    }
#}
#
#
#class operator_ts_residualyT: public basic_operator//daily regression
#{
#  public:
#    operator_ts_residualyT() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      vector<vector<double>> ans = arg1
#
#      for (int i = 0i < arg1.size()++i) {
#
#        //X = [x1, x2.. xn]
#        //Y = [x1, x2.. xn]
#        //
#        //[ sum(yi^2) sum(yi)  * [a] = [sum(xi * yi) 
#        //  sum(yi)   sum(1) ]   [b]    sum(xi)
#        //use A B C D to keep the 
#        // [A B  inverse = [D -B
#        //  C D]           -C  A] / (AD - BC) 
#        //
#        double A = 0
#        double B = 0//B = C
#        double D = 0
#        double XY = 0
#        double SUMY = 0
#
#        for (int z = 0z < arg1[i].size()++z) {
#          double x = arg2[i][z]
#          double y = arg1[i][z]
#          if (std::isnan(y) || std::isinf(y)) continue
#          if (std::isnan(x) || std::isinf(x)) continue
#
#          A += x * x
#          B += x
#          D += 1.0
#
#          XY += x * y
#          SUMY += y
#        }
#        if (A * D - B * B <= 0) {//not good
#          for (int z = 0z < arg1[i].size()++z) {
#            ans[i][z] = 0.0
#          }
#          continue
#        }
#        double a = (D * XY - B * SUMY) / (A * D - B * B)
#        double b = (-B * XY + A * SUMY) / (A * D - B * B)
#
#        for (int z = 0z < arg1[i].size()++z) {
#          ans[i][z] = arg1[i][z] - (a * arg2[i][z] + b)
#        }
#      }
#      for (int i = arg1.size() - 1i >= 0i--) {
#        for (int j = 0j < arg1[i].size()++j) {
#          int bd = (int)(round(arg3[i][j]))
#          double up = 0
#          double down = 0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            if (std::isnan(ans[i - z][j]) || std::isinf(ans[i - z][j])) continue
#            up += ans[i - z][j]
#            down += 1.0
#          }
#          up = (down > 0)?up / down:NAN
#          ans[i][j] = up
#        }
#      }
#      return ans 
#    }
#}
#
#
#class operator_ts_countbelowmean: public basic_operator
#{
#  public:
#    operator_ts_countbelowmean() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#
#          double cnt = 0
#          double sum = 0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x0 = arg1[i - z][j]
#            if (std::isnan(x0) || std::isinf(x0)) continue
#            cnt += 1
#            sum += x0
#          }
#          //if (cnt / bd <= fill_rate) continue
#          if (cnt < 0) continue
#          double mean = sum / cnt
#          double local_cnt = 0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x0 = arg1[i - z][j]
#            if (std::isnan(x0) || std::isinf(x0)) continue
#            if (x0 < mean) {
#              local_cnt += 1
#            }
#          }
#          ans[i][j] = local_cnt / (double)bd - 0.5
#        }
#      }
#      return ans 
#    }
#}
#
#class operator_ts_countabovemean: public basic_operator
#{
#  public:
#    operator_ts_countabovemean() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#
#          double cnt = 0
#          double sum = 0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x0 = arg1[i - z][j]
#            if (std::isnan(x0) || std::isinf(x0)) continue
#            cnt += 1
#            sum += x0
#          }
#          //if (cnt / bd <= fill_rate) continue
#          if (cnt < 0) continue
#          double mean = sum / cnt
#          double local_cnt = 0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x0 = arg1[i - z][j]
#            if (std::isnan(x0) || std::isinf(x0)) continue
#            if (x0 > mean) {
#              local_cnt += 1
#            }
#          }
#          ans[i][j] = local_cnt / (double)bd - 0.5
#        }
#      }
#      return ans 
#    }
#}
#
#class operator_ts_longeststrikeabovemean: public basic_operator
#{
#  public:
#    operator_ts_longeststrikeabovemean() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#
#          double cnt = 0
#          double sum = 0
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x0 = arg1[i - z][j]
#            if (std::isnan(x0) || std::isinf(x0)) continue
#            cnt += 1
#            sum += (x0)
#          }
#          //if (cnt / T <= fill_rate) continue
#          if (cnt <= 0) continue
#          double mean = sum / cnt
#          int local_cnt = 0
#          int max_cnt = 0
#
#          for (int z = 0z < bd++z) {
#            if (i - z < 0) continue
#            double x0 = arg1[i - z][j]
#            if (std::isnan(x0) || std::isinf(x0)) continue
#            if (x0 > mean) {
#              local_cnt += 1
#            } else {//stop counting and reset local_cnt
#              if (local_cnt > max_cnt) max_cnt = local_cnt
#              local_cnt = 0
#            }
#          }
#          ans[i][j] = (double)max_cnt / (double)bd//TODO this one's logic has problem
#        }
#      }
#      return ans 
#    }
#}
#
#
#
#class operator_ts_cidednormalized: public basic_operator
#{
#  public:
#    operator_ts_cidednormalized() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#
#          double cnt = 0
#          double sumx = 0
#          double sumx2 = 0
#          for (int z = 0z < bd++z) {
#            int offset = i - z
#            if (offset < 0) continue
#            if (std::isnan(arg1[offset][j]) || std::isinf(arg1[offset][j])) continue
#            cnt += 1
#            sumx += arg1[offset][j]
#            sumx2 += arg1[offset][j] * arg1[offset][j]
#          }
#          //if (cnt / T <= fill_rate) continue
#          if (cnt <= 0) continue
#          double mean = sumx / cnt
#          double sigma = sqrt(sumx2 / cnt - mean * mean)
#          if (1) {
#            if (sigma < 1e-7 || std::isnan(sigma) || std::isinf(sigma)) {
#              continue
#            }
#          }
#      
#          double local_res = 0
#          cnt = 0
#          for (int z = 0z < bd - 1++z) {//only x[i-T+2:i] - x[i-T+1:i-1]
#            if (i - z - 1 < 0) continue
#            double x0 = arg1[i - z][j]
#            double x1 = arg1[i - z - 1][j]
#            if (1) {
#              x0 = (x0 - mean) / sigma
#              x1 = (x1 - mean) / sigma
#            }
#            if (std::isnan(x0) || std::isinf(x0)) continue
#            if (std::isnan(x1) || std::isinf(x1)) continue
#
#            local_res += (x0 - x1) * (x0 - x1)//TODO:or div by T?
#            cnt += 1
#          }
#          if (cnt <= 0) continue
#          ans[i][j] = sqrt(local_res / cnt)
#        }
#      }
#      return ans 
#    }
#}
#
#
#class operator_ts_cided: public basic_operator
#{
#  public:
#    operator_ts_cided() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#
#          double cnt = 0
#          double sumx = 0
#          double sumx2 = 0
#          for (int z = 0z < bd++z) {
#            int offset = i - z
#            if (offset < 0) continue
#            if (std::isnan(arg1[offset][j]) || std::isinf(arg1[offset][j])) continue
#            cnt += 1
#            sumx += arg1[offset][j]
#            sumx2 += arg1[offset][j] * arg1[offset][j]
#          }
#          //if (cnt / T <= fill_rate) continue
#          if (cnt <= 0) continue
#          double mean = sumx / cnt
#          double sigma = sqrt(sumx2 / cnt - mean * mean)
#      
#          double local_res = 0
#          cnt = 0
#          for (int z = 0z < bd - 1++z) {//only x[i-T+2:i] - x[i-T+1:i-1]
#            if (i - z - 1 < 0) continue
#            double x0 = arg1[i - z][j]
#            double x1 = arg1[i - z - 1][j]
#            if (std::isnan(x0) || std::isinf(x0)) continue
#            if (std::isnan(x1) || std::isinf(x1)) continue
#
#            local_res += (x0 - x1) * (x0 - x1)//TODO:or div by T?
#            cnt += 1
#          }
#          if (cnt <= 0) continue
#          ans[i][j] = sqrt(local_res / cnt)
#        }
#      }
#      return ans 
#    }
#}
#
#class operator_ts_position: public basic_operator
#{
#  public:
#    operator_ts_position() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#
#          double cnt = 0 
#          double maxx = NAN
#          double minx = NAN
#          for (int z = 0z < bd++z) {
#            int offset = i - z
#            if (offset < 0) continue
#            if (std::isnan(arg1[offset][j]) || std::isinf(arg1[offset][j])) continue
#            if (std::isnan(maxx) || arg1[offset][j] > maxx) maxx = arg1[offset][j]
#            if (std::isnan(minx) || arg1[offset][j] < minx) minx = arg1[offset][j]
#          }
#          //if (cnt / T <= fill_rate) continue
#          if (cnt < 0) continue
#          if (maxx <= minx) continue//TODO
#          ans[i][j] = (arg1[i][j] - minx) / (maxx - minx)
#        }
#      }
#      return ans 
#    }
#}
#
#class operator_ts_ratiobeyondrsigma: public basic_operator
#{
#  public:
#    operator_ts_ratiobeyondrsigma() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          double cut = arg3[i][j]
#
#
#          double cnt = 0
#          double sumx = 0
#          double sumx2 = 0
#          for (int z = 0z < bd++z) {
#            int offset = i - z
#            if (offset < 0) continue
#            if (std::isnan(arg1[offset][j]) || std::isinf(arg1[offset][j])) continue
#            cnt += 1
#            sumx += arg1[offset][j]
#            sumx2 += arg1[offset][j] * arg1[offset][j]
#          }
#          if (cnt / bd <= 0.5) continue
#          double mean = sumx / cnt
#          double sigma = sqrt(sumx2 / cnt - mean * mean)
#          if (sigma < 1e-7 || std::isnan(sigma) || std::isinf(sigma)) continue
#
#          double local_res = 0
#          double down = 0
#          for (int z = 0z < bd++z) {
#            int offset = i - z
#            if (offset < 0) continue
#            if (std::isnan(arg1[offset][j]) || std::isinf(arg1[offset][j])) continue
#            if ((arg1[offset][j] - mean) / sigma > cut) {
#              local_res += fabs(arg1[offset][j] - mean)//TODO:or div by T?
#            }
#            down += fabs(arg1[offset][j] - mean)
#          }
#          ans[i][j] = (down > 0)?local_res / down:NAN
#        }
#      }
#      return ans 
#    }
#}
#
#
#
#
#class operator_ts_uptoall: public basic_operator
#{
#  public:
#    operator_ts_uptoall() { argnum_ = 2 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#
#          double up = 0
#          double down = 0
#          for (int z = 0z < bd++z) {
#            int offset = i - z
#            if (offset - 1 < 0) continue
#            double x0 = arg1[offset][j]
#            double x1 = arg1[offset - 1][j]
#
#            if (std::isnan(x0) || std::isinf(x0)) continue
#            if (std::isnan(x1) || std::isinf(x1)) continue
#            
#            up += fabs(x0 - x1)
#            down += (x0 > x1)?x0 - x1:0.0
#          }
#          ans[i][j] = (down > 0)?up / down:NAN
#        }
#      }
#      return ans 
#    }
#}
#
#
#
#class operator_ts_fftresidual: public basic_operator
#{
#  public:
#    operator_ts_fftresidual() { argnum_ = 3 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          int kp = (int)(round(arg3[i][j]))
#          
#          vector<double> a(bd, 0.0)
#          double up = 0
#          double down = 0
#          for (int z = 0z < bd++z) {
#            int offset = i - z
#            if (offset - 1< 0) continue
#            double x0 = arg1[offset][j]
#            if (std::isnan(x0) || std::isinf(x0)) continue
#            a[z] = x0
#          }
#          vector<pair<double, double>> im = normalize(a, kp)
#          vector<double> ireal = inormalize(im)
#          ans[i][j] = ireal[0]
#        }
#      }
#      return ans 
#    }
#}
#
#
#class operator_ts_fftpercent: public basic_operator
#{
#  public:
#    operator_ts_fftpercent() { argnum_ = 3 }
#
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        for (int j = 0j < arg1[i].size()++j) {
#          ans[i][j] = NAN
#          int bd = (int)(round(arg2[i][j]))
#          int kp = (int)(round(arg3[i][j]))
#          
#          vector<double> a(bd, 0.0)
#          double up = 0
#          double down = 0
#          for (int z = 0z < bd++z) {
#            int offset = i - z
#            if (offset - 1 < 0) continue
#            double x0 = arg1[offset][j]
#            if (std::isnan(x0) || std::isinf(x0)) continue
#            a[z] = x0
#          }
#          ans[i][j] = fftpercent(a, kp)
#        }
#      }
#      return ans 
#    }
#}
#
#
#class operator_ts_svd: public basic_operator
#{
#  public:
#    operator_ts_svd() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        int bd = (int)(round(arg2[i][0]))
#        int kp = (int)(round(arg3[i][0]))
#
#        int height = bd
#        int width = arg1[0].size()//stock size
#
#        Fmatrix<float> a(height, width)
#
#        vector<float> sigv
#        sigv.reserve(height * width)
#        for (int z = 0z < height++z) {
#          int offset = i - z
#          if (offset < 0) continue
#          for (int j = 0j < width++j) {//width = stock size
#            sigv.push_back(arg1[offset][j])
#          }
#        }
#        float cutoff = 0.001
#        int pos_lower = floor(height * width * cutoff)
#        int pos_upper = height * width - 1 - pos_lower
#        assert(pos_lower < pos_upper)
#        nth_element(sigv.begin(), sigv.begin() + pos_lower, sigv.end())
#        float lower_bound = sigv[pos_lower]
#        nth_element(sigv.begin(), sigv.begin() + pos_upper, sigv.end())
#        float upper_bound = sigv[pos_upper]
#
#
#        for (int z = 0z < height++z) {
#          for (int j = 0j < width++j) {
#            a(z, j) = 0.0
#            int offset = i - z
#            if (offset < 0) continue
#            float v = arg1[offset][j]
#            if (v > upper_bound) v = upper_bound
#            if (v < lower_bound) v = lower_bound
#            a(z, j) = v
#          }
#        }
#
#        for (int z = 0z < height++z) {
#          float adj = 0
#          for (int j = 0j < width++j) {
#            adj += a(z, j)
#          }
#          adj /= width
#          for (int j = 0j < width++j) {
#            a(z, j) -= adj
#          }
#          for (int j = 0j < width++j) {
#            assert(!std::isnan(a(z, j)))
#          }
#        }
#
#        Fmatrix<float> aT = CMatrixTranspose<float>()(a)
#        Fmatrix<float> aa = a * aT
#        Fmatrix<float> ww(height, height)
#        Fmatrix<float> dd(height, 1)
#        Fmatrix<float> vv(height, height)
#        svd(aa, ww, dd, vv)
#        Fmatrix<float> wt = CMatrixTranspose<float>()(ww)
#        Fmatrix<float> nv = wt * a
#        for (int z = 0z < height++z) {
#          dd(z, 0) = sqrt(dd(z, 0))
#        }
#        for (int z = 0z < height++z) {
#          for (int j = 0j < width++j) {
#            if (fabs(dd(z, 0)) < 1e-10) {
#              nv(z, j) = 0.0
#            } else {
#              nv(z, j) /= dd(z, 0)
#            }
#          }
#        }
#        vector<float> eg(height, 0)
#        for (int z = 0z < height++z) {
#          eg[z] = dd(z, 0)
#          if (z < kp) eg[z] = 0
#        }
#
#        for (int k = 0k < width++k) {
#          ans[i][k] = 0
#          for (int j = 0j < height++j) {
#            ans[i][k] += eg[j] * ww(0, j) * nv(j, k)
#          }
#        }
#      }
#      return ans 
#    }
#}
#
#
#
#
#class operator_ts_zca: public basic_operator
#{
#  public:
#    operator_ts_zca() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      vector<vector<double>> ans = arg1
#      for (int i = 0i < arg1.size()++i) {
#        int bd = (int)(round(arg2[i][0]))
#        int kp = (int)(round(arg3[i][0]))
#        int height = bd
#        int width = arg1[0].size()//stock size
#        Fmatrix<float> a(height, width)
#        vector<float> sigv
#        sigv.reserve(height * width)
#        for (int z = 0z < height++z) {
#          int offset = i - z
#          if (offset < 0) continue
#          for (int j = 0j < width++j) {//width = stock size
#            sigv.push_back(arg1[offset][j])
#          }
#        }
#        float cutoff = 0.001
#        int pos_lower = floor(height * width * cutoff)
#        int pos_upper = height * width - 1 - pos_lower
#        assert(pos_lower < pos_upper)
#        nth_element(sigv.begin(), sigv.begin() + pos_lower, sigv.end())
#        float lower_bound = sigv[pos_lower]
#        nth_element(sigv.begin(), sigv.begin() + pos_upper, sigv.end())
#        float upper_bound = sigv[pos_upper]
#
#
#        for (int z = 0z < height++z) {
#          for (int j = 0j < width++j) {
#            a(z, j) = 0.0
#            int offset = i - z
#            if (offset < 0) continue
#            float v = arg1[offset][j]//a(0, :) has the latest info(di)
#            if (v > upper_bound) v = upper_bound
#            if (v < lower_bound) v = lower_bound
#            a(z, j) = v
#          }
#        }
#
#        for (int z = 0z < height++z) {
#          float adj = 0
#          for (int j = 0j < width++j) {
#            adj += a(z, j)
#          }
#          adj /= width
#          for (int j = 0j < width++j) {
#            a(z, j) -= adj
#          }
#          for (int j = 0j < width++j) {
#            assert(!std::isnan(a(z, j)))
#          }
#        }
#
#        Fmatrix<float> aT = CMatrixTranspose<float>()(a)
#        Fmatrix<float> aa = a * aT
#        
#        for (int i = 0i < height++i) {
#          for (int j = 0j < height++j) {
#            aa(i, j) /= width
#          }
#        }
#
#        Fmatrix<float> ww(height, height)
#        Fmatrix<float> dd(height, 1)
#        Fmatrix<float> vv(height, height)
#        svd(aa, ww, dd, vv)
#        Fmatrix<float> wt = CMatrixTranspose<float>()(ww)
#        Fmatrix<float> nv = wt * a
#
#
#        for (int i = 0i < height++i) {
#          dd(i, 0) = 1.0 / sqrt(dd(i, 0) + 1e-7)
#          if (i < kp) {
#            dd(i, 0) = 0.0
#          }
#          for (int j = 0j < height++j) {
#            vv(i, j) = vv(i, j) * dd(i, 0)
#          }
#        }
#        //3.zca
#        Fmatrix<float> zca = ww * vv
#        //4.transform
#        vector<vector<float> > res(height, vector<float>(width, 0.0))
#        for (int i = 0i < height++i) {
#          for (int j = 0j < width++j) {
#            for (int k = 0k < height++k) {
#              //res[i][j] = res[i][j] + zca(i, k) * v[k][j]
#              res[i][j] = res[i][j] + zca(i, k) * a(k, j)
#            }
#          }
#          for (int k = 0k < width++k) {
#            ans[i][k] = res[0][k]
#          }
#          break//just need first line
#        }
#      }
#      return ans 
#    }
#}
#
#
#
#




#//1. SVDResidual svd (8 16 32) * (1 2 3 4) =12(done)
#//2. SVDResidualStd svd (8 16 32) * (1 2 3 4) + std = 12(done)
#//
#//3. SpectrumFlattenSVDResidual (8 16 32) * (1 2 3 4) =12
#//4. SpectrumFlattenSVDResidualStd (8 16 32) * (1 2 3 4) =12
#//
#//5. ClusteredSVDResidual cluster svd (8 16 32) * (1 2 3 4) = 12
#//6. ClusteredSVDResidualStd cluster svd (8 16 32) * (1 2 3 4) = 12
#//7. RegResidual (pe cap std) * (32 64) 
#//8. QuadracticRegResidual (pe cap std) * (32 64) 
#//9. KernelRegResidual (pe cap std) * (32 64) 
#//10. ClusteredRegResidual (pe cap std) * (32 64) 
#//
#//11. SVDWithRisk
#//svd with pe (32 64) * (1 2 3 4) = 8
#//svd with cap (32 64) * (1 2 3 4) = 8
#//svd with h - l (32 64) * (1 2 3 4) = 8
#//
#//12. FFT3D
#//clustered fft FFF (1 2 3) * (1 2 3 4 5) * (16  32 64) 
#//
#//
#//13. RegResidualSVD
#//pe cap h - l adjusted
#//{
#//cluster demean 8 16 32 64
#//svd (8 16 32) * (1 2 3 4) =12
#//svd (8 16 32) * (1 2 3 4) + std = 12
#//}
#
#//14. ClusterDemean cluster demean 8 16 32 64
#
#
#class SVDResidual: public basic_operator
#{
#  public:
#    SVDResidual() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      //row[r - 1] is the latest info
#      int kp = (int)(round(arg2[0][0]))
#      vector<double> ans = SVDInfo(arg1, kp, 0, -1)
#      return vector<vector<double>>(1, ans)
#    }
#}
#
#
#class SVDResidualStd: public basic_operator
#{
#  public:
#    SVDResidualStd() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      //row[r - 1] is the latest info
#      //arg1:signal
#      //arg2:kp = component
#      //arg3:bd, bd for std
#      int r = arg1.size()
#      int c = arg1[0].size()
#      int kp = (int)(round(arg2[0][0]))
#      int bd = (int)(round(arg3[0][0]))
#      assert(bd <= r)
#      vector<double> ans = SVDInfo(arg1, kp, 1, bd)
#      return vector<vector<double>>(1, ans)
#    }
#}
#
#class SpectrumFlattenSVDResidual: public basic_operator
#{
#  public:
#    SpectrumFlattenSVDResidual() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      //row[r - 1] is the latest info
#      int kp = (int)(round(arg2[0][0]))
#      vector<vector<double>> adjsig = Flatten(arg1)
#      vector<double> ans = SVDInfo(adjsig, kp, 0, -1)
#
#      return vector<vector<double>>(1, ans)
#    }
#}
#
#
#class SpectrumFlattenSVDResidualStd: public basic_operator
#{
#  public:
#    SpectrumFlattenSVDResidualStd() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      //row[r - 1] is the latest info
#      //arg1:signal
#      //arg2:kp = component
#      //arg3:bd, bd for std
#      int r = arg1.size()
#      int c = arg1[0].size()
#      int kp = (int)(round(arg2[0][0]))
#      int bd = (int)(round(arg3[0][0]))
#      assert(bd <= r)
#
#      vector<vector<double>> adjsig = Flatten(arg1)
#      vector<double> ans = SVDInfo(adjsig, kp, 1, bd)
#
#      return vector<vector<double>>(1, ans)
#    }
#}
#
#
#
#//5. ClusteredSVDResidual cluster svd (8 16 32) * (1 2 3 4) = 12
#//
#//6. ClusteredSVDResidualStd cluster svd (8 16 32) * (1 2 3 4) = 12
#//7. RegResidual (pe cap std) * (32 64) 
#
#
#class RegResidual: public basic_operator
#{
#  public:
#    RegResidual() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#
#      int r = arg1.size()
#      int c = arg1[0].size()
#      vector<double> ans(c, NAN)
#      for (int j = 0j < arg1[0].size()++j) {
#        int bd = r
#        vector<double> xs
#        vector<double> ys
#
#        for (int z = 0z < bd++z) {
#          double x = arg2[z][j]
#          double y = arg1[z][j]
#          if (std::isnan(y) || std::isinf(y)) continue
#          if (std::isnan(x) || std::isinf(x)) continue
#          ys.push_back(y)
#          xs.push_back(x)
#        }
#        vector<double> coef = fitLinear<double>(xs, ys)
#        ans[j] = arg1[r - 1][j] - (coef[0] + arg2[r - 1][j] * coef[1])
#      }
#      return vector<vector<double>>(1, ans)
#    }
#}
#
#
#//8. QuadracticRegResidual (pe cap std) * (32 64) 
#
#class QuadracticRegResidual: public basic_operator
#{
#  public:
#    QuadracticRegResidual() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#
#      int r = arg1.size()
#      int c = arg1[0].size()
#      vector<double> ans(c, NAN)
#      for (int j = 0j < arg1[0].size()++j) {
#        int bd = r
#        vector<double> xs
#        vector<double> ys
#
#        for (int z = 0z < bd++z) {
#          double x = arg2[z][j]
#          double y = arg1[z][j]
#          if (std::isnan(y) || std::isinf(y)) continue
#          if (std::isnan(x) || std::isinf(x)) continue
#          ys.push_back(y)
#          xs.push_back(x)
#        }
#        vector<double> coef = fitQuadratic<double>(xs, ys)
#        ans[j] = arg1[r - 1][j] - (coef[0] + coef[1] * arg2[r - 1][j] + coef[2] * arg2[r - 1][j] * arg2[r - 1][j])
#      }
#      return vector<vector<double>>(1, ans)
#    }
#}
#
#
#
#//9. KernelRegResidual (pe cap std) * (32 64) 
#
#//10. ClusteredRegResidual (pe cap std) * (32 64) 
#//
#//11. SVDWithRisk
#//svd with pe (32 64) * (1 2 3 4) = 8
#//svd with cap (32 64) * (1 2 3 4) = 8
#//svd with h - l (32 64) * (1 2 3 4) = 8
#//
#class SVDWithRisk: public basic_operator
#{
#  public:
#    SVDWithRisk() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#      //row[r - 1] is the latest info
#      int kp = (int)(round(arg3[0][0]))
#      vector<vector<double>> adjsig = arg1
#      for (int i = 0i < arg1.size()++i) {
#        adjsig[i].insert(adjsig[i].end(), arg2[i].begin(), arg2[i].end())
#      }
#      for (int j = 0j < adjsig[0].size()++j) {
#        double sum = 0
#        double sum2 = 0
#        double cnt = 0.0
#        
#        
#        for (int i = 0i < adjsig.size()++i) {
#          double v = adjsig[i][j]
#          if (std::isnan(v) || std::isinf(v)) continue
#          sum += v
#          sum2 += v * v
#          cnt += 1.0
#        }
#        double mean = sum / cnt
#        double sigma = sqrt(sum2 / cnt - mean * mean)
#        if (sigma < 1e-7) continue
#        
#        for (int i = 0i < adjsig.size()++i) {
#          double v = adjsig[i][j]
#          adjsig[i][j] = (adjsig[i][j] - mean) / sigma
#        }
#      }
#      
#      vector<double> res = SVDInfo(adjsig, kp, 0, -1)
#      vector<double> ans(res.begin(), res.begin() + arg1[0].size())
#      return vector<vector<double>>(1, ans)
#    }
#}
#
#//
#//12. FFT3D
#//clustered fft FFF (1 2 3) * (1 2 3 4 5) * (16  32 64) 
#//
#//
#//13. RegResidualSVD
#//pe cap h - l adjusted
#//{
#//cluster demean 8 16 32 64
#//svd (8 16 32) * (1 2 3 4) =12
#//svd (8 16 32) * (1 2 3 4) + std = 12
#//}
#//
#class RegResidualSVD: public basic_operator
#{
#  public:
#    RegResidualSVD() { argnum_ = 3 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2, vector<vector<double>> &arg3) { 
#
#      int r = arg1.size()
#      int c = arg1[0].size()
#      vector<double> ans(c, NAN)
#      vector<vector<double>> adjsig(r, vector<double>(c, NAN))
#      
#      for (int j = 0j < arg1[0].size()++j) {
#        int bd = r
#        vector<double> xs
#        vector<double> ys
#
#        for (int z = 0z < bd++z) {
#          double x = arg2[z][j]
#          double y = arg1[z][j]
#          if (std::isnan(y) || std::isinf(y)) continue
#          if (std::isnan(x) || std::isinf(x)) continue
#          ys.push_back(y)
#          xs.push_back(x)
#        }
#        vector<double> coef = fitLinear<double>(xs, ys)
#        for (int z = 0z < bd++z) {
#          adjsig[z][j] = arg1[z][j] - (coef[0] + arg2[z][j] * coef[1])
#        }
#      }
#
#      int kp = (int)(round(arg3[0][0]))
#      vector<double> res = SVDInfo(adjsig, kp, 0, -1)
#
#      return vector<vector<double>>(1, res)
#    }
#}
#
#//14. ClusterDemean cluster demean 8 16 32 64
#//
#//
#//
#
#
#class ClusterDemean: public basic_operator
#{
#  public:
#    ClusterDemean() { argnum_ = 2 }
#    virtual vector<vector<double>> calc(vector<vector<double>> &arg1, vector<vector<double>> &arg2) { 
#      //row[r - 1] is the latest info
#      int r = arg1.size()
#      int c = arg1[0].size()
#      int div = (int)(round(arg2[0][0]))
#      vector<pair<int, int>> cluster = Cluster2D(arg1, div)
#      
#      vector<float> sum(div * div, 0)
#      vector<float> cnt(div * div, 0)
#
#      for (int i = 0i < c++i) {
#        double v = arg1[r - 1][i]
#
#        if (!std::isnan(v) && !std::isinf(v)) {
#          int ind = cluster[i].first * div + cluster[i].second
#          if (ind < 0) continue
#          sum[ind] += v
#          cnt[ind] += 1.0
#        }
#      }
#      for (int i = 0i < div * div++i) {
#        sum[i] = (cnt[i] > 0)?sum[i] / cnt[i]:NAN
#      }
#      vector<double> res(c, NAN)
#      for (int i = 0i < c++i) {
#        double v = arg1[r - 1][i]
#        if (!std::isnan(v) && !std::isinf(v)) {
#          int ind = cluster[i].first * div + cluster[i].second
#          if (ind < 0) continue
#          res[i] = v - sum[ind]
#        }
#      }
#      return vector<vector<double>>(1, res)
#    }
#}








class OperatorVecFactory(object):
    @staticmethod
    def create(ops):
        if(ops == "add"):
            return operator_add()
        elif(ops == "sub"):
            return operator_sub()
        elif(ops == "mul"):
            return operator_mul()
        elif(ops == "svd"):
            return operator_svd()
        else:
            return None

    @staticmethod
    def create_char(ops):
        if(ops == '+'):
            return operator_add()
        elif(ops == '-'):
            return operator_sub()
        elif(ops == '*'):
            return operator_mul()
        else:
            return None



def get_ops():
  res = []
  res.append('add')
  res.append('sub')
  res.append('mul')
  res.append('svd')
  return set(res)


from enum import Enum
class OPTOR_TYPE_VEC(Enum):
   OT_OPERATOR = 1
   OT_OPERAND = 2

class SInfo(object):
    def __init__(self):
      self.operatorp = None
      self.operand = []
      self.vn = ''

class OptorVec(object):
    @staticmethod
    def create_char(opr):
      bop = OperatorVecFactory.create_char(opr) 
      if(bop == None): return None
      op = OptorVec()
      op.val.operatorp = bop
      op.type = OPTOR_TYPE_VEC.OT_OPERATOR 
      return op

    @staticmethod
    def create(opr):
      bop = OperatorVecFactory.create(opr) 
      if (bop == None):return None
      op = OptorVec()
      op.val.operatorp = bop
      op.type = OPTOR_TYPE_VEC.OT_OPERATOR 
      return op

    @staticmethod
    def create_operand_double(opn):
      op = OptorVec()
      op.type = OPTOR_TYPE_VEC.OT_OPERAND 
      op.val.vn = str(opn)#Convert.ToString(opn) 
      return op
    @staticmethod
    def create_operand(opn):
      op = OptorVec()
      op.type = OPTOR_TYPE_VEC.OT_OPERAND 
      op.val.vn = opn
      return op
  
    def __init__(self):
      self.val = SInfo()
      self.type = None


class ExpressionVec:
    @staticmethod
    def get_ops():
        res = {}
        res['max'] = 0
        res['add'] = 0
        res['mul'] = 0
        res['sub'] = 0
        return res
    @staticmethod
    def priority(opr):
        if (opr == '+'):return 1
        if (opr == '-'):return 1
        if (opr == '*'):return 2
        if (opr == '/'):return 2
        if (opr == '%'):return 2
        if (opr == '^'):return 2
        if (opr == '('):return 3
        if (opr == ')'):return 3
        return 0
    @staticmethod
    def read_operand(ss, beg, end, operand):
      operand = 0
      dot = False
      rate = 1
      neg = False
      if((beg != end) and ((ss[beg]) == '-')):
        beg = beg + 1
        neg = true
      while (beg != end):
        ch = ss[beg]
        if (ch in '0123456789'):
          if (dot):
            rate *= 0.1
            operand += (ord(ch) - ord('0')) * rate
          else:
            operand = operand * 10 + ord(ch) - ord('0')
        elif (ch == '.'):
          if (dot == False):
            dot = True
          else:
            return [True, beg, end, operand]
        else:
          break
        beg = beg + 1

      if (neg):operand *= -1
      return [True, beg, end, operand]


    @staticmethod
    def read_function(ss, beg, end, funcname):
      ch = ''
      funcname = ''
      while (beg != end):
        ch = ss[beg]
        if(ch.isspace() or ch == '(' or ch == '*' or ch == '+' or ch == '-' or ch == '\\' or ch == ')' or ch == ',' or ch == '/' or ch == '^'):
          break
        funcname = funcname + ch
        beg = beg + 1
      return [True , beg, end, funcname]

    @staticmethod
    def postexpr(mexpr, optors):
      ops_set = get_ops()
      operator_stack = deque([])
      it = 0
      end = len(mexpr)
      operand = 0.0
      optors = []#new List<OptorVec>()
      lach = '$'#//Convert.ToChar(-1)
      ch = '$'#//Convert.ToChar(-1)
      while (it != end):
        lach = ch
        ch = mexpr[it]
        if ((ch.isdigit()) or ch == '.' or (ch == '-' and (lach == '$' or lach == '('))):
          [res, it, end, operand] = ExpressionVec().read_operand(mexpr, it, end, operand)
          if (res == False):return [False, optors]
          opp = OptorVec().create_operand(operand)
          
          if (opp == None):return [False, optors]
          optors.append(opp)
          continue
        elif (ch.isalpha()):
          funcname = ''
          [res,it,end,funcname] = ExpressionVec().read_function(mexpr, it, end, funcname)
          if (res == False):return [False, optors]

          if (funcname in ops_set):
            operator_stack.append(funcname)
          else:
            opp = OptorVec().create_operand(funcname)
            if (opp == None):return [False, optors]
            optors.append(opp)
          continue
        elif (ch == ','):
          while(len(operator_stack) > 0):
            tops = operator_stack[-1]
            topch = tops[0]
            if (topch == '('):
              break
            else:
              op = None 
              operator_stack.pop()
              if (topch.isalpha()):
                op = OptorVec().create(tops)
              else:
                op = OptorVec().create_char(topch)
              if (op == None):return [False, optors]
              optors.append(op)
        elif (ch == '+' or ch == '-' or ch == '*' or ch == '/' or ch == '%' or ch == '^'):
          tops = ''
          topch = ''
          if (len(operator_stack) == 0):
            operator_stack.append(ch)
            it = it +1
            continue
        
          tops = operator_stack[-1]
          topch = tops[0]
          if (topch.isalpha()):return [False, optors]
          
          if (topch != '(' and ExpressionVec().priority(ch) > ExpressionVec().priority(topch)):
            operator_stack.append(ch)
          else:
            while (len(operator_stack) > 0):
              tops = operator_stack[-1]
              topch = tops[0]
              if (topch.isalpha()):return [False, optors]
              if (topch != '(' and ExpressionVec().priority(ch) <= ExpressionVec().priority(topch)):
                operator_stack.pop()
                opp =  OptorVec().create_char(topch)
                if (opp == None):return [False,optors]
                optors.append(opp)
              else:
                break
        
            operator_stack.append(ch)
        elif (ch == '('):
          operator_stack.append(ch)
        elif (ch == ')'):
          while (len(operator_stack) > 0):
            tops = ''
            topch = ''
            tops = operator_stack[-1]
            operator_stack.pop()
            topch = tops[0]
            if (topch.isalpha()):return [False,optors]
            if (topch != '('):
              opp = OptorVec().create_char(topch)
              if (opp == None):return [False,optors]
              optors.append(opp)
            else:
              if (len(operator_stack) > 0):
                tops = operator_stack[-1]
                topch = tops[0]
                if (topch.isalpha()):
                  operator_stack.pop()
                  opp = OptorVec().create(tops)
                  if (opp == None): return [False,optors]
                  optors.append(opp)
                break
        elif (not ch.isspace()):
          return [False,optors]
        it = it + 1

      while(len(operator_stack) > 0):	
        ltops = ''
        opp = None
        ltops = operator_stack[-1]
        operator_stack.pop()
        if (len(ltops) > 1):
          opp = OptorVec().create(ltops)
        else:
          opp = OptorVec().create_char(ltops[0])
          
        if (opp == None):return [False,optors]
        optors.append(opp)
      return [True,optors]

    @staticmethod
    def eval_postexpr(optors, result):
      operand_stack = deque([])#new Stack<Vector<Vector<double>>>()
      for it in optors: 
        if (it.type == OPTOR_TYPE_VEC.OT_OPERAND):
          operand_stack.append(it.val.operand)
        else:
          opp = it.val.operatorp
          argnum = opp.argnum()
          if (len(operand_stack) < argnum):
            return [False,result]
          d1 = None
          d2 = None
          d3 = None
          if (argnum > 0):
            d1 = operand_stack.pop()
          if (argnum > 1):
            d2 = operand_stack.pop()
          if (argnum > 2):
            d3 = operand_stack.Pop()

          if (argnum == 1):
              result = it.val.operatorp.calc(d1)
          elif (argnum == 2):
              result = it.val.operatorp.calc(d2, d1)
          elif (argnum == 3):
              result = it.val.operatorp.calc(d3, d2, d1)
          else:
              return [False,result]
            
          operand_stack.append(result)
          
      if (len(operand_stack) != 1):
        return [False,result]
      else:
        result = operand_stack[-1]
      return [True,result]



def debug1():
  optors_ = []
  Expr = 'b*a + 5 * a * a +a + a +b - b * (a + 5) + add(a, mul(b , 5))'
  [res, optors_] = ExpressionVec().postexpr(Expr, optors_)
  if (res == False):
    print("cant not parse:"+Expr)
    
  a = pd.DataFrame(np.random.rand(5, 7))
  b = pd.DataFrame(np.random.rand(5, 7))
  c = pd.DataFrame(np.ones((5, 7))) * 5
  for it in optors_:
    if (it.type == OPTOR_TYPE_VEC.OT_OPERAND):
      dmgr = it.val.vn
      if (dmgr == 'a'):
        it.val.operand = a
      elif (dmgr == 'b'):
        it.val.operand = b
      else:
        it.val.operand = c
  #foreach(var it in local_optors) {
  #  if (it.type == OPTOR_TYPE_VEC.OT_OPERAND) {
  #    String dmgr = it.val.vn;
  #    it.val.operand = Query(dmgr, valid_id, Backdays, di);
  #  }
  #}
  result = None
  [res, result] = ExpressionVec.eval_postexpr(optors_, result)
  print(result)
  print(b*a + 5 * a * a +a + a +b - b * (a + 5) + (a + b * 5))

def debug2():
  optors_ = []
  Expr = 'svd(a, kp) + b'
  [res, optors_] = ExpressionVec().postexpr(Expr, optors_)
  if (res == False):
    print("cant not parse:"+Expr)
  a = pd.DataFrame(np.random.rand(5, 7))
  b = pd.DataFrame(np.random.rand(5, 7))
  c = pd.DataFrame(np.ones((5, 7))) * 5
  kp = pd.DataFrame(np.ones((5, 7))) * 1

  for it in optors_:
    if (it.type == OPTOR_TYPE_VEC.OT_OPERAND):
      dmgr = it.val.vn
      if (dmgr == 'a'):
        it.val.operand = a
      elif (dmgr == 'b'):
        it.val.operand = b
      elif (dmgr == 'c'):
        it.val.operand = c
      else:
        it.val.operand = kp

  result = None
  [res, result] = ExpressionVec.eval_postexpr(optors_, result)
  print(result)
  print(a)
  #print(b*a + 5 * a * a +a + a +b - b * (a + 5) + (a + b * 5))

if __name__=='__main__':
    debug2()
