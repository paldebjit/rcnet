import torch

import numpy as np
import torch.nn.functional as F
import torch_geometric.transforms as T

from data.constants import ZERO_LABEL_COUNT
from nn.dataset import RCDataset
from nn.model import RCNet

from torch_geometric.data import DataLoader
from sklearn.metrics import *


###################################################
#from torch_geometric.datasets import Planetoid
#
#dataset = 'Cora'
#path = "./data/"
#dataset = Planetoid(path, dataset, transform=T.NormalizeFeatures())
###################################################
dataset = RCDataset("./", transform=T.NormalizeFeatures())
dataset = dataset.shuffle()

total = len(dataset)
train = int(0.5*total)
test  = total - train
print("Total: ", total, "Train: ", train, "Test: ", test)

train_ds = dataset[:train]
test_ds = dataset[train:]

train_loader = DataLoader(train_ds, shuffle=True)
test_loader = DataLoader(test_ds, shuffle=True)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = RCNet(dataset.num_features, 1).to(device)
opt = torch.optim.Adam(model.parameters(), lr=0.001)


def train():
    model.train()

    for data in train_loader:
        data = data.to(device)

        opt.zero_grad()

        output = model(data)[data.mask]
        target = data.y[data.mask].float().unsqueeze(1)
        loss = F.binary_cross_entropy_with_logits(output, target, pos_weight=torch.Tensor([ZERO_LABEL_COUNT/10]).to(device)) 
        loss.backward()

        opt.step()

def eval():

    model.eval()

    preds = { 'train': [], 'test': [] }
    label = { key: [] for key in preds.keys() }
    unmasked_preds = { key: [] for key in preds.keys() }

    def tmp(loader, key):
        with torch.no_grad():
            for data in loader:
                data = data.to(device)
                um_prd = torch.round(torch.sigmoid(model(data)))
                prd = um_prd[data.mask]
                lbl = data.y[data.mask]
    
                preds[key].append( prd.detach().cpu().numpy() )
                label[key].append( lbl.detach().cpu().numpy() )
                unmasked_preds[key].append( um_prd.detach().cpu().numpy() )
        
    tmp(train_loader, 'train')
    tmp(test_loader, 'test')

    accs = []
    bal_acc = []
    prec = []
    recall = []
    tps = []
    fps = []
    tns = []
    fns = []
    total_pos = []

    for key in preds.keys():
        p = np.concatenate(preds[key])
        l = np.concatenate(label[key])

        accs.append( balanced_accuracy_score(l, p) )
        bal_acc.append( balanced_accuracy_score(l, p, adjusted=True) )

        recall.append( recall_score(l, p) )
        prec.append( precision_score(l, p) )

        tn, fp, fn, tp = confusion_matrix(l, p).ravel()
        tps.append(tp)
        fps.append(fp)
        tns.append(tn)
        fns.append(fn)

        total_pos.append( np.sum(np.concatenate(unmasked_preds[key])) )

    print("\tAccuracy: ", [key + ": " + str(accs[i]) for i, key in enumerate(preds.keys())])
    print("\tBal Accuracy: ", [key + ": " + str(bal_acc[i]) for i, key in enumerate(preds.keys())])
    print("\tRecall: ", [key + ": " + str(recall[i]) for i, key in enumerate(preds.keys())])
    print("\tPrecision: ", [key + ": " + str(prec[i]) for i, key in enumerate(preds.keys())])
    print("\tTP: ", [key + ": " + str(tps[i]) for i, key in enumerate(preds.keys())])
    print("\tFP: ", [key + ": " + str(fps[i]) for i, key in enumerate(preds.keys())])
    print("\tTN: ", [key + ": " + str(tns[i]) for i, key in enumerate(preds.keys())])
    print("\tFN: ", [key + ": " + str(fns[i]) for i, key in enumerate(preds.keys())])
    #print("\tTotal pos: ", [key + ": " + str(total_pos[i]) for i, key in enumerate(preds.keys())])


for epoch in range(1, 501):
    print("Epoch: ", epoch)
    train()
    eval()
