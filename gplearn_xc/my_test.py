import numpy as np
import matplotlib.pyplot as plt 

x0 = np.arange(-1, 1, 1/10.)
x1 = np.arange(-1, 1, 1/10.)
x0, x1 = np.meshgrid(x0, x1)
y_truth = x0**2 - x1**2 + x1 - 1

ax = plt.figure().gca(projection='3d')
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
surf = ax.plot_surface(x0, x1, y_truth, rstride=1, cstride=1,
                        color='green', alpha=0.5)
plt.show()



from sklearn.utils import check_random_state

rng = check_random_state(0)

# Training samples
X_train = rng.uniform(-1, 1, 100).reshape(50, 2)
y_train = X_train[:, 0]**2 - X_train[:, 1]**2 + X_train[:, 1] - 1

# # Testing samples
# X_test = rng.uniform(-1, 1, 100).reshape(50, 2)
# y_test = X_test[:, 0]**2 - X_test[:, 1]**2 + X_test[:, 1] - 1


from gplearn.genetic import SymbolicRegressor
from gplearn.genetic import SymbolicTransformer
# est_gp = SymbolicRegressor(population_size=5000,
#                             generations=20, stopping_criteria=0.01,
#                             p_crossover=0.7, p_subtree_mutation=0.1,
#                             p_hoist_mutation=0.05, p_point_mutation=0.1,
#                             max_samples=0.9, verbose=1,
#                             parsimony_coefficient=0.01, random_state=0,feature_names = ['A','B'])

est_gp = SymbolicTransformer(population_size=5000,
                            generations=20, stopping_criteria=0.01,
                            p_crossover=0.7, p_subtree_mutation=0.1,
                            p_hoist_mutation=0.05, p_point_mutation=0.1,
                            max_samples=0.9, verbose=1,
                            parsimony_coefficient=0.01, random_state=0,feature_names = ['A','B'])

est_gp.fit(X_train, y_train)


# for program in est_gp._programs[-1][:20]:
#     print(program)
#     print(program.raw_fitness_)


 def reset(self, new_df=None):
        # 初始化
        self.balance = initial_account_balance ##初始金额
        self.net_worth = initial_account_balance ##目前净值
        self.max_net_worth = initial_account_balance ##最大净值
        self.shares_held = 0 ##持仓
        self.cost_basis = 0 ##平均成本
        self.total_shares_sold = 0 ##卖出量
        self.total_sales_value = 0 ##卖出价值

        # 传给环境测试集
        if new_df:
            self.df = new_df
        self.current_step = 0
        return self._next_observation()