import torch
import torch.nn.functional as F
import numpy as np


def TP(q, tau=12, beta=0.5):
    """subjectively-inspired temporal pooling"""
    q = torch.unsqueeze(q, 0)
    qm = -float('inf') * torch.ones((1, 1, tau - 1)).to(q.device)
    qp = 10000.0 * torch.ones((1, 1, tau - 1)).to(q.device)  #

    '''
        torch.nn.functional.max_pool1d(input,          输入张量
                            kernel_size,               池化区域大小
                            stride=None,               步长
                            padding=0,                 填充
                            dilation=1,                
                            ceil_mode=False,           True：ceil; False: floor
                            return_indices=False)
    '''
    qm_cat_q = torch.cat((qm, -q), 2)
    l = -F.max_pool1d(qm_cat_q, tau, stride=1)
    print("qm_cat_q = ", qm_cat_q)
    print("max_pool = ", l)

    q_q_cat_qp_qp = torch.cat((q * torch.exp(-q), qp * torch.exp(-qp)), 2)
    q_cat_qp = torch.cat((torch.exp(-q), torch.exp(-qp)), 2)
    print("q_q_cat_qp_qp = ", q_q_cat_qp_qp)
    print("q_cat_qp = ", q_cat_qp)

    m = F.avg_pool1d(q_q_cat_qp_qp, tau, stride=1)
    n = F.avg_pool1d(q_cat_qp, tau, stride=1)
    print("m = ", m , " n = ", n)
    m = m / n
    return beta * m + (1 - beta) * l

if __name__ == "__main__":
    p = [[1., 2., 3., 4., 5.]]
    p_out = TP(torch.from_numpy(np.array(p).astype(np.float32)))
    ans = torch.mean(p_out)
    print(p_out)
    print("ans = " + str(ans))