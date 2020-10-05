import torch

import matplotlib.pyplot as plt
import numpy as np
import torch.nn.functional as F
import torch_geometric.transforms as T

from data.constants import ZERO_LABEL_COUNT
from nn.dataset import RCDataset
from nn.model import RCNet

from sklearn.metrics import *
from torch_geometric.data import DataLoader


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
train = int(0.8*total)
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
        _, cnt = torch.unique(target, return_counts=True, sorted=True)
        wt = cnt[0]//cnt[1]
        loss = F.binary_cross_entropy_with_logits(output, target, pos_weight=torch.Tensor([10]).to(device)) 
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

    return bal_acc


train_hist = []
test_hist = []
epochs = range(1, 151)
for epoch in epochs:
    print("Epoch: ", epoch)
    train()
    metric = eval()
    train_hist.append(metric[0])
    test_hist.append(metric[1])


# Evaluate on the example
model.eval()
ex = dataset.get_examples()
with torch.no_grad():
    for data in ex:
        data = data.to(device)
        prob = torch.sigmoid(model(data))
        pred = torch.round(prob)
        for i, p in enumerate(pred):
            if p == 1:
                print(data.name[i], prob[i][0].cpu().numpy())

        true_label = [data.name[i] for i, l in enumerate(data.y) if l == 1]
        print(true_label)

# Plot P-R curve 
label = []
preds = []
with torch.no_grad():
    for data in test_loader:
        data = data.to(device)
        prob = torch.sigmoid(model(data))
        label.append( data.y[data.mask].detach().cpu().numpy() )
        preds.append( prob[data.mask].detach().cpu().numpy() )
    
label = np.concatenate(label)
preds = np.concatenate(preds)
p, r, _ = precision_recall_curve(label, preds)

fig = plt.figure(figsize=(16,16))
ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
ax.set_xlabel("Recall", fontsize=14)
ax.set_ylabel("Precision", fontsize=14)
ax.tick_params(axis='both', which='major', labelsize=12)
ax.plot(r, p)
plt.show()


# Plot Histories
fig = plt.figure(figsize=(16,9))
ax = fig.add_axes([0.1,0.1,0.8,0.8])
ax.set_xlabel("Iteration", fontsize=14)
ax.set_title("Metric evolution", fontsize=18)
ax.tick_params(axis='both', which='major', labelsize=12)
ax.plot(epochs, train_hist, label="Train Metric")
ax.plot(epochs, test_hist, label="Test Metric")
ax.legend(fontsize=12)
plt.show()

