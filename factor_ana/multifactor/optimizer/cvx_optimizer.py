__author__ = "Software Authors: Xu Deyuan"
__copyright__ = "Copyright (C) 2019 HTSC"
__license__ = "Private"
__version__ = "1.0"
import numpy as np
import cvxpy as cvx
class CvxOptimizer:
    def __init__(self,name='cvxopt'):
        self._cov_mtx=None
        self._idiosyn_mtx=None
        self._fct_beta_vec=None
        self._fct_expo_mtx=None
        self._mu_vec=None
        self._risk_aversion=None
        self._eta=1
        self._penalty_coeff=0.003
        self._m=None
        self._n=None
        self._rules=dict()
        self._w=None
        self._w0=None
        self._name=name
        self._solver=None
        self.verbose=True
        self.status=None
    @property
    def cov_mtx(self):
        return self._cov_mtx
    @cov_mtx.setter
    def cov_mtx(self,value):
        i,j=value.shape
        if i==j:
            if self._m is None:
                self._m=i
            else:
                if self._m!=i:
                    if i==self._n:
                        self._m=i
                    else:
                        raise AssertionError
            self._cov_mtx=value
        else:
            raise AssertionError
    @cov_mtx.deleter
    def cov_mtx(self):
        del self._cov_mtx
    @property
    def idiosyn_mtx(self):
        return self._idiosyn_mtx
    @idiosyn_mtx.setter
    def idiosyn_mtx(self,value):
        i,j=value.shape
        if i==j:
            if self._n is None:
                self._n=i
            else:
                if self._n!=i:
                    raise AssertionError
            self._idiosyn_mtx=value
        else:
            raise AssertionError
    @idiosyn_mtx.deleter
    def idiosyn_mtx(self):
        del self._idiosyn_mtx
    @property
    def fct_beta_vec(self):
        return self._fct_beta_vec
    @fct_beta_vec.setter
    def fct_beta_vec(self,value):
        value=np.reshape(value,-1)
        if self._m is None:
            self._m=value.size
        else:
            if self._m!=value.size:
                raise AssertionError
        self._fct_beta_vec=value
    @fct_beta_vec.deleter
    def fct_beta_vec(self):
        del self._fct_beta_vec
    @property
    def fct_expo_mtx(self):
        return self._fct_expo_mtx
    @fct_expo_mtx.setter
    def fct_expo_mtx(self,value):
        i,j=value.shape
        if self._n is None:
            self._n=i
        else:
            if self._n!=i:
                raise AssertionError
        if self._m is None:
            self._m=j
        else:
            if self._m!=j and self._m!=self._n:
                raise AssertionError
        self._fct_expo_mtx=value
    @fct_expo_mtx.deleter
    def fct_expo_mtx(self):
        del self._fct_expo_mtx
    @property
    def mu_vec(self):
        return self._mu_vec
    @mu_vec.setter
    def mu_vec(self,value):
        value=np.reshape(value,-1)
        if self._n is None:
            self._n=value.size
        else:
            if self._n!=value.size:
                raise AssertionError
        self._mu_vec=value
    @mu_vec.deleter
    def mu_vec(self):
        del self._mu_vec
    @property
    def risk_aversion(self):
        return self._risk_aversion
    @risk_aversion.setter
    def risk_aversion(self,value):
        if value>=0:
            self._risk_aversion=float(value)
        else:
            raise AssertionError
    @risk_aversion.deleter
    def risk_aversion(self):
        del self._risk_aversion
    @property
    def penalty_coeff(self):
        return self._penalty_coeff
    @penalty_coeff.setter
    def penalty_coeff(self,value):
        if value>=0:
            self._penalty_coeff=float(value)
        else:
            raise AssertionError
    @penalty_coeff.deleter
    def penalty_coeff(self):
        del self._penalty_coeff
    @property
    def eta(self):
        return self._eta
    @eta.setter
    def eta(self,value):
        if value>=0:
            self._eta=float(value)
        else:
            raise AssertionError
    @eta.deleter
    def eta(self):
        del self._eta
    @property
    def m(self):
        return self._m
    @property
    def n(self):
        return self._n
    @property
    def rules(self):
        return self._rules
    @property
    def w(self):
        return self._w
    @property
    def w0(self):
        return self._w0
    @w0.setter
    def w0(self,value):
        value=np.reshape(value,-1)
        if self._n is None:
            self._n=value.size
        else:
            if self._n!=value.size:
                raise AssertionError
        self._w0=value
    @w0.deleter
    def w0(self):
        del self._w0
    def add_rule(self,rule_name,rule_str):
        if type(rule_name)is str and type(rule_str)is str:
            self._rules[rule_name]=rule_str
        else:
            raise AssertionError
    @property
    def name(self):
        return self._name
    @property
    def solver(self):
        if self._solver is None:
            return cvx.ECOS
        else:
            return self._solver
    @solver.setter
    def solver(self,value):
        if value is None:
            self._solver=cvx.ECOS
        else:
            self._solver=value
    def check_run(self):
        self._w=cvx.Variable(self.n)
        if self.risk_aversion is None:
            self.risk_aversion=0
        conditions=[]
        conditions.append(self.mu_vec is not None)
        if not np.all(conditions):
            raise AssertionError
    def run(self):
        constraints_str=None
        penalty=None
        if len(self.rules)>0:
            constraints_str='['+', '.join(self.rules.values())+']'
        rtn=self.mu_vec*self.w
        risk=cvx.quad_form(self.w,self.cov_mtx)if self.cov_mtx is not None else 0
        if self.w0 is not None:
            # penalty=self.penalty_coeff*cvx.sum_entries(cvx.power(cvx.abs(self.w-self.w0),self.eta))
            penalty=self.penalty_coeff*cvx.sum(cvx.power(cvx.abs(self.w-self.w0),self.eta))

        if penalty is not None:
            if constraints_str is not None:
                cvx_problem=cvx.Problem(cvx.Maximize(rtn-self.risk_aversion*risk-penalty),eval(constraints_str))
            else:
                cvx_problem=cvx.Problem(cvx.Maximize(rtn-self.risk_aversion*risk-penalty))
        else:
            if constraints_str is not None:
                cvx_problem=cvx.Problem(cvx.Maximize(rtn-self.risk_aversion*risk),eval(constraints_str))
            else:
                cvx_problem=cvx.Problem(cvx.Maximize(rtn-self.risk_aversion*risk))
        cvx_problem.solve(solver=self.solver,verbose=self.verbose)
        self.status=cvx_problem.status
