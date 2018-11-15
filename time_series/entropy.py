import numpy as np
import math
import random
import matplotlib.pyplot as plt
from numpy.random import rand


def generate_data_from_uniform_distribution(N=1000):
    return rand(N)


class entropy_function:
    def __init__(self, u, m, r):
        self.u = u
        self.N = len(u)
        self.m = m
        self.r = r

    # 幅mで、uから切り取ったX(ベクトル)の集合を作る
    def extract_X_vectors(self, delta=1):
        X_vectors = []
        for i in range(self.N - self.m + 1):
            X_vectors.append(self.u[i:self.m * delta + i: delta])
            assert len(self.u[i:self.m * delta + i: delta]) == self.m

        assert len(X_vectors) == self.N - self.m + 1

        return X_vectors

    def Chebyshev_distance(self, vector_1, vector_2):
        # 各座標の差の絶対値の最大値を返す
        return max([abs(vector_1[i] - vector_2[i]) for i in range(len(vector_1))])

    def count_c(self, X_vectors, i, not_equal=False):
        count = 0
        for j in range(self.N - self.m + 1):
            if self.Chebyshev_distance(X_vectors[j], X_vectors[i]) <= self.r:
                if not_equal and j == i:
                    continue

                count += 1

        return count / (self.N - self.m + 1.0)


def ApEn(u, m, r):
    N = len(u)
    func = entropy_function(u, m, r)

    assert isinstance(m, int)   # mは整数
    assert abs(r) == r      # rは正の実数

    def _phi(m):
        X_vectors = func.extract_X_vectors()
        c_m_i_list = []
        for i in range(N - m + 1):
            c_m_i_list.append(func.count_c(X_vectors, i))
        return (N - m + 1.0) ** (-1) * sum(np.log(c_m_i_list))

    return abs(_phi(m) - _phi(m+1))


def SampEn(u, m, r, delta=1):
    N = len(u)
    func = entropy_function(u, m, r)

    assert isinstance(m, int)  # mは整数
    assert abs(r) == r  # rは正の実数

    def _phi(m):
        X_vectors = func.extract_X_vectors(delta=delta)
        c_m_i_list = []
        for i in range(N - m + 1):
            c_m_i_list.append(func.count_c(X_vectors, i, not_equal=True))
        return sum(c_m_i_list)

    return -np.log(_phi(m+1) / _phi(m))


if __name__ == "__main__":

    _ = ApEn([85, 80, 89] * 17, m=2, r=3)
    # assert round(ApEn([85, 80, 89] * 17, m=2, r=3), 9) == 0.000010996   # wikiから

    u = generate_data_from_uniform_distribution(N=2000)
    ap_res = [ApEn(u, m=2, r=r) for r in np.logspace(0, 2, 20) / 100]

    samp_res = [SampEn(u, m=2, r=r) for r in np.logspace(0, 2, 20) / 100]

    x = [r for r in np.logspace(0, 2, 20) / 100]
    plt.xscale("log")
    plt.scatter(x, ap_res)
    plt.scatter(x, samp_res)
    plt.show()

