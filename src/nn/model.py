import torch
import torch.nn.functional as F

from torch_geometric.nn import GraphConv


class RCNet(torch.nn.Module):
    def __init__(self, in_dim, out_dim):
        super(RCNet, self).__init__()

        inter_dim = 64

        self.conv1 = GraphConv(in_dim, inter_dim, 'mean')
        self.conv2 = GraphConv(inter_dim, out_dim)

    def forward(self, data):
        x = data.x
        ei = data.edge_index

        x = F.relu(self.conv1(x, ei))
        x = F.dropout(x, p=0.5)
        x = self.conv2(x, ei)

        return x
