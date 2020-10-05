import torch

from common.config import config
from common.utils import *
from data.data import get_all_data

from torch_geometric.data import InMemoryDataset


class RCDataset(InMemoryDataset):
    def __init__(self, root, transform=None, pre_transform=None):
        super(RCDataset, self).__init__(root, transform, pre_transform)
        self.data, self.slices, self.ex = torch.load(self.processed_paths[0])

    @property
    def raw_file_names(self):
        return []

    @property
    def processed_file_names(self):
        if not config.available:
            config.read_config()
        return get_dataset_path()

    def download(self):
        pass

    def process(self):
        data_list, ex_list = get_all_data()

        if self.pre_filter is not None:
            data_list = [data for data in data_list if self.pre_filter(data)]
            ex_list = [data for data in ex_list if self.pre_filter(data)]

        if self.pre_transform is not None:
            data_list = [self.pre_transform(data) for data in data_list]
            ex_list = [self.pre_transform(data) for data in ex_list]

        data, slices = self.collate(data_list)
        torch.save((data, slices, ex_list), self.processed_paths[0])

    def get_examples(self):
        return self.ex
