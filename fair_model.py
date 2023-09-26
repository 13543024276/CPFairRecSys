# -*- coding: utf-8 -*-
"""fair_model.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Ht0Pca_Up3E76hE6mhjr-m8mo45BUAmm

<a href="https://colab.research.google.com/github/rahmanidashti/CPFairRecSys/blob/main/fair_model.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

## Install packages
"""

# Install MIP and Gurobipy for optimization purpose


"""## Config"""

# Swtich to tensoflow 1 to use Cornac
# %tensorflow_version 1.x
import tensorflow as tf
tf.__version__

# import packages
import os
import numpy as np
from collections import defaultdict
from tqdm import tqdm

from itertools import product
from sys import stdout as out
from mip import Model, xsum, maximize, BINARY

import cornac
from cornac.eval_methods import BaseMethod, RatioSplit
from cornac.models import MostPop, UserKNN, ItemKNN, MF, PMF, BPR, NeuMF, WMF, HPF, CVAE, VAECF, NMF
from cornac.metrics import Precision, Recall, NDCG, AUC, MAP, FMeasure, MRR
from cornac.data import Reader
import exception

from cornac.utils import cache

"""## Download datasets, user, and item groups"""

# download datasets: train, test, tune
def download_dataset():
  #迭代数据集名称，然后看看是否是目录存在的
    #目录不存在，建立目录！创建目录
    #目录存在，不用管
  ds_root_path = "datasets/"
  for dataset in ds_names:
    dataset_path = os.path.join(ds_root_path, dataset)

    if not os.path.isdir(dataset_path):
      os.makedirs(dataset_path)
      print("Directory '%s' is created." % dataset_path)
    else:
      print("Directory '%s' is exist." % dataset_path)

    # -nc: skip downloads that would download to existing files.

    try:

      os.system(f'curl -o {dataset_path}/{dataset}_train.txt -L https://raw.githubusercontent.com/rahmanidashti/CPFairRecSys/main/datasets/{dataset}/{dataset}_train.txt')
      os.system(f'curl -o {dataset_path}/{dataset}_test.txt -L  https://raw.githubusercontent.com/rahmanidashti/CPFairRecSys/main/datasets/{dataset}/{dataset}_test.txt')
      os.system(f"curl -o {dataset_path}/{dataset}_tune.txt -L https://raw.githubusercontent.com/rahmanidashti/CPFairRecSys/main/datasets/{dataset}/{dataset}_tune.txt")
      print(f"{dataset}: The train, tune, and test sets downloaded.")
    except exception as e:
      print(e)

# dowanload user groups: active and inactive
def download_user_groups():
  user_root_path = "user_groups/"
  for dataset in ds_names:
    for ugroup in ds_users:
      user_groups_path = os.path.join(user_root_path, dataset, ugroup)

      if not os.path.isdir(user_groups_path):
        os.makedirs(user_groups_path)
        print("Directory '%s' is created." % user_groups_path)
      else:
        print("Directory '%s' is exist." % user_groups_path)

      # -nc: skip downloads that would download to existing files.

      try:
        os.system(f"curl -o {user_groups_path}\\active_ids.txt -L https://raw.githubusercontent.com/rahmanidashti/CPFairRecSys/main/datasets/{dataset}/groups/users/{ugroup}/active_ids.txt")
        os.system(f"curl -o {user_groups_path}\\inactive_ids.txt -L https://raw.githubusercontent.com/rahmanidashti/CPFairRecSys/main/datasets/{dataset}/groups/users/{ugroup}/inactive_ids.txt")

        print(f"{dataset}: User groups on '{ugroup}' downloaded.")
      except Exception as e:
        print(e)

# dowanload item groups: short-head and long-tail
def download_item_groups():
  item_root_path = "item_groups/"
  for dataset in ds_names:
    for igroup in ds_items:
      item_groups_path = os.path.join(item_root_path, dataset, igroup)

      if not os.path.isdir(item_groups_path):
        os.makedirs(item_groups_path)
        print("Directory '%s' is created." % item_groups_path)
      else:
        print("Directory '%s' is exist." % item_groups_path)

      # -nc: skip downloads that would download to existing files.
    try:
      os.system(f"curl -o {item_groups_path}\\shorthead_items.txt -L https://raw.githubusercontent.com/rahmanidashti/CPFairRecSys/main/datasets/{dataset}/groups/items/{igroup}/shorthead_items.txt")
      os.system(f"curl -o {item_groups_path}\\longtail_items.txt -L https://raw.githubusercontent.com/rahmanidashti/CPFairRecSys/main/datasets/{dataset}/groups/items/{igroup}/longtail_items.txt")
      print(f"{dataset}: Item groups on '{igroup}' downloaded.")
    except Exception as e:
      print(e)



"""## Load `Cornac` data and model"""

# reading the train, test, and val sets
def read_data(dataset):
  """
  Read the train, test, and tune file using Cornac reader class

  Parameters
  ----------
  dataset : the name of the dataset
    example: 'MovieLens100K'

  Returns
  ----------
  train_data:
    The train set that is 70% of interactions
  tune_data:
    The tune set that is 10% of interactions
  test_data:
    The test set that is 20% of interactions
  """
  reader = Reader()
  train_data = reader.read(fpath=f"datasets/{dataset}/{dataset}_train.txt", fmt='UIR', sep='\t')
  tune_data = reader.read(fpath=f"datasets/{dataset}/{dataset}_tune.txt", fmt='UIR', sep='\t')
  test_data = reader.read(fpath=f"datasets/{dataset}/{dataset}_test.txt", fmt='UIR', sep='\t')
  return train_data, tune_data, test_data

# load data into Cornac evaluation method
def load_data(train_data, test_data):
  """
  load data into Cornac evaluation method

  Parameters
  ----------
  train_data:
    train_data from Reader Class
  test_data:
    test_data from Reader Class

  Returns
  ----------
  eval_method:
    Instantiation of a Base evaluation method using the provided train and test sets
  """
  # exclude_unknowns (bool, default: False) – Whether to exclude unknown users/items in evaluation.
  # Instantiate a Base evaluation method using the provided train and test sets
  eval_method = BaseMethod.from_splits(
      train_data=train_data, test_data=test_data, rating_threshold=1.0, exclude_unknowns=True, verbose=True
  )

  return eval_method

# running the cornac
def run_model(eval_method):
  """
  running the cornac

  Parameters
  ----------
  eval_method:
    Cornac's evaluation protocol

  Returns
  ----------
  exp:
    Cornac's Experiment
  """

  models = [
            # MostPop(),
            # UserKNN(k=20, similarity="cosine", weighting="bm25", name="UserKNN-BM25"),
            # ItemKNN(k=20, similarity="cosine", name="ItemKNN-Cosine"),
            # BPR(k=50, max_iter=200, learning_rate=0.001, lambda_reg=0.001, verbose=True),
            # WMF(k=50, max_iter=50, learning_rate=0.001, lambda_u=0.01, lambda_v=0.01, verbose=True, seed=123),
            # HPF(k=50, seed=123, hierarchical=False, name="PF"),
            VAECF(k=10, autoencoder_structure=[20], act_fn="tanh", likelihood="mult", n_epochs=100, batch_size=100, learning_rate=0.001, beta=1.0, seed=123, use_gpu=True, verbose=True),
            # NeuMF(num_factors=9, layers=[32, 16, 8], act_fn="tanh", num_epochs=5, num_neg=3, batch_size=256, lr=0.001, seed=42, verbose=True)
            ]

  # define metrics to evaluate the models
  metrics = [
            AUC(), MAP(), MRR(), NDCG(k=10), Recall(k=10)
            # Precision(k=5), Precision(k=10), Precision(k=20),  Precision(k=50),
            # Recall(k=5), Recall(k=10), Recall(k=20), Recall(k=50),
            # FMeasure(k=5), FMeasure(k=10), FMeasure(k=20), FMeasure(k=50),
            # NDCG(k=5), NDCG(k=10), NDCG(k=20), NDCG(k=50)
            ]

  # put it together in an experiment, voilà!
  exp = cornac.Experiment(eval_method=eval_method, models=models, metrics=metrics)
  exp.run()

  return exp

"""## Load user and item groups"""

# Create a set of IDs for each users group
# Creat a matrix U which shows the user and the groups of the user
def read_user_groups(user_group_fpath: str, gid) -> set:
  """
    这个函数的作用：
      填写用户组进U标识，并且构造一个集合user_ids
  """

  user_group = open(user_group_fpath, 'r').readlines()
  user_ids = set()
  for eachline in user_group:
    uid = eachline.strip()
    # convert uids to uidx
    uid = eval_method.train_set.uid_map[uid]
    uid = int(uid)
    user_ids.add(uid)
    U[uid][gid] = 1
  return user_ids

# read test data
#这个方法在干什么玩意呢？
  #1-我们通过遍历训练数据集中的边关系，然后就能统计出，每个物品的交互次数字典，以及用户的交互物品集
  # test_file===>test_checkins:ground true 交互集合（字典）如：{0：{0,1,3}}
def read_ground_truth(test_file):
  """
  Read test set data

  Parameters
  ----------
  test_file:
    The test set data

  Returns
  ----------
  ground_truth:
    A dictionary includes user with actual items in test data
  """
  ground_truth = defaultdict(set)
  truth_data = open(test_file, 'r').readlines()
  for eachline in truth_data:
    uid, iid, _ = eachline.strip().split()

    # convert uids to uidx
    uid = eval_method.train_set.uid_map[uid]
    # convert iids to iidx
    iid = eval_method.train_set.iid_map[iid]

    uid, iid = int(uid), int(iid)
    ground_truth[uid].add(iid)
  return ground_truth

# read train data

#这个方法在干什么玩意呢？
  #1-我们通过遍历训练数据集中的边关系，然后就能统计出，每个物品的交互次数字典，以及用户的交互物品集
  # train_file===>pop_items{1:1,2:3}[有交互的物品次数] train_checkins交互集合（字典）如：{0：{0,1,3}}
def read_train_data(train_file):
  """
  Read test set data

  Parameters
  ----------
  train_file:
    The train_file set data

  Returns
  ----------
  train_checkins:
    A dictionary includes user with items in train data
  pop: dictionary
    A dictionary of all items alongside of its occurrences counter in the training data
    example: {1198: 893, 1270: 876, 593: 876, 2762: 867}
  """
  train_checkins = defaultdict(set)
  pop_items = dict()
  train_data = open(train_file, 'r').readlines()

  for eachline in train_data:
    uid, iid, _ = eachline.strip().split()

    # convert uids to uidx
    uid = eval_method.train_set.uid_map[uid]
    # convert iids to iidx
    iid = eval_method.train_set.iid_map[iid]

    uid, iid = int(uid), int(iid)
    # a dictionary of popularity of items
    if iid in pop_items.keys():
      pop_items[iid] += 1
    else:
      pop_items[iid] = 1
    train_checkins[uid].add(iid)
  return train_checkins, pop_items

"""## Metrics"""

def catalog_coverage(predicted: list, catalog: list) -> float:
  """
  Computes the catalog coverage for k lists of recommendations
  Parameters
  ----------
  predicted : a list of lists
      Ordered predictions
      example: [['X', 'Y', 'Z'], ['X', 'Y', 'Z']]
  catalog: list
      A list of all unique items in the training data
      example: ['A', 'B', 'C', 'X', 'Y', Z]
  k: integer
      The number of observed recommendation lists
      which randomly choosed in our offline setup
  Returns
  ----------
  catalog_coverage:
      The catalog coverage of the recommendations as a percent rounded to 2 decimal places
  ----------
  Metric Defintion:
  Ge, M., Delgado-Battenfeld, C., & Jannach, D. (2010, September).
  Beyond accuracy: evaluating recommender systems by coverage and serendipity.
  In Proceedings of the fourth ACM conference on Recommender systems (pp. 257-260). ACM.
  """
  predicted_flattened = [p for sublist in predicted for p in sublist]
  L_predictions = len(set(predicted_flattened))
  catalog_coverage = round(L_predictions / (len(catalog) * 1.0) * 100, 2)
  # output: precent (%)
  return catalog_coverage

def novelty(predicted: list, pop: dict, u: int, k: int) -> float:
  """
  Computes the novelty for a list of recommended items for a user
  Parameters
  ----------
  predicted : a list of recommedned items
      Ordered predictions
      example: ['X', 'Y', 'Z']
  pop: dictionary
      A dictionary of all items alongside of its occurrences counter in the training data
      example: {1198: 893, 1270: 876, 593: 876, 2762: 867}
  u: integer
      The number of users in the training data
  k: integer
      The length of recommended lists per user
  Returns
  ----------
  novelty:
      The novelty of the recommendations in system level
  mean_self_information:
      The novelty of the recommendations in recommended top-N list level
  ----------
  Metric Defintion:
  Zhou, T., Kuscsik, Z., Liu, J. G., Medo, M., Wakeling, J. R., & Zhang, Y. C. (2010).
  Solving the apparent diversity-accuracy dilemma of recommender systems.
  Proceedings of the National Academy of Sciences, 107(10), 4511-4515.
  """
  self_information = 0
  for item in predicted:
    if item in pop.keys():
      item_popularity = pop[item] / u
      item_novelty_value = np.sum(-np.log2(item_popularity))
    else:
      item_novelty_value = 0
    self_information += item_novelty_value
  novelty_score = self_information / k
  return novelty_score

def precisionk(actual, predicted):
  return 1.0 * len(set(actual) & set(predicted)) / len(predicted)

def recallk(actual, predicted):
  return 1.0 * len(set(actual) & set(predicted)) / len(actual)

def ndcgk(actual, predicted):
  idcg = 1.0
  dcg = 1.0 if predicted[0] in actual else 0.0
  for i, p in enumerate(predicted[1:]):
    if p in actual:
      dcg += 1.0 / np.log(i+2)
    idcg += 1.0 / np.log(i+2)
  return dcg / idcg

"""## Load User and Item Matrices"""

# Here we saved the results of scores and you can read them from repo to do your experiments.
# S is a matrix to store user's scores on each item
# P incldues the indecies of topk ranked items
# Sprime saves the scores of topk ranked items

'''
  这个函数有什么用？
    获取S：所有用户对于所有物品的评分分数矩阵
    P：就是所有用户的Topk物品：没有select后的topK
'''
def load_ranking_matrices(model, total_users, total_items, topk):
  S = np.zeros((total_users, total_items))
  P = np.zeros((total_users, topk))

  # for model in exp.models:
  print(model.name)
  for uid in tqdm(range(total_users)):
    S[uid] = model.score(uid)
    P[uid] = np.array(list(reversed(model.score(uid).argsort()))[:topk])

  return S, P

# Ahelp is a binary matrix in which an element of its is 1 if the corresponding element in P (which is an item index) is in ground truth.
# Actually is shows whether the rankied item in P is included in ground truth or not.

def load_ground_truth_index(total_users, topk, P, train_checkins):
  Ahelp = np.zeros((total_users, topk))
  for uid in tqdm(range(total_users)):
    for j in range(topk):
      # convert user_ids to user_idx
      # convert item_ids to item_idx
      if P[uid][j] in train_checkins[uid]:
        Ahelp[uid][j] = 1
  return Ahelp

# create a set of IDs for each users group
'''
  这个矩阵就是帮迭代物品分组标识矩阵+收集对应的物品集合进行返回
'''
def read_item_groups(item_group_fpath: str, gid) -> set:
  item_group = open(item_group_fpath, 'r').readlines()
  item_ids = set()
  for eachline in item_group:
    iid = eachline.strip()
    # convert iids to iidx
    iid = eval_method.train_set.iid_map[iid]
    iid = int(iid)
    item_ids.add(iid)
    I[iid][gid] = 1
  return item_ids

'''
  这个函数的作用是：对各个用户的top-k物品进行分组记录，得到分组矩阵：Ihelp 这个是三维的(total_users, topk, no_item_groups)
'''
def read_item_index(total_users, topk, no_item_groups):
  Ihelp = np.zeros((total_users, topk, no_item_groups))
  for uid in range(total_users):
    for lid in range(topk):
      # convert item_ids to item_idx
      if P[uid][lid] in shorthead_item_ids:
        Ihelp[uid][lid][0] = 1
      elif P[uid][lid] in longtail_item_ids:
        Ihelp[uid][lid][1] = 1
  return Ihelp

"""## Evaluation"""

def metric_per_group(group, W):
  NDCG10 = list()
  Pre10 = list()
  Rec10 = list()
  Novelty10 = list()
  predicted = list()
  All_Predicted = list()

  for uid in tqdm(group):
    if uid in ground_truth.keys():
      for j in range(50):
        if W[uid][j].x == 1:
          predicted.append(P[uid][j])
      copy_predicted = predicted[:]
      All_Predicted.append(copy_predicted)
      NDCG = ndcgk(actual=ground_truth[uid], predicted=predicted)
      Pre = precisionk(actual=ground_truth[uid], predicted=predicted)
      Rec = recallk(actual=ground_truth[uid], predicted=predicted)
      Novelty = novelty(predicted=predicted, pop=pop_items, u=eval_method.total_users, k=10)

      NDCG10.append(NDCG)
      Pre10.append(Pre)
      Rec10.append(Rec)
      Novelty10.append(Novelty)

      # cleaning the predicted list for a new user
      predicted.clear()

  catalog = catalog_coverage(predicted=All_Predicted, catalog=pop_items.keys())
  return round(np.mean(NDCG10), 5), round(np.mean(Pre10), 5), round(np.mean(Rec10), 5), round(np.mean(Novelty10), 5), catalog

def metric_on_all(W):
  """
  """
  predicted_user = list()
  NDCG_all = list()
  PRE_all = list()
  REC_all = list()
  Novelty_all = list()
  All_Predicted = list()


  for uid in tqdm(range(eval_method.total_users)):
    if uid in ground_truth.keys():
      for j in range(50):
        if W[uid][j].x == 1:
          predicted_user.append(P[uid][j])

      copy_predicted = predicted_user[:]
      All_Predicted.append(copy_predicted)

      NDCG_user = ndcgk(actual=ground_truth[uid], predicted=predicted_user)
      PRE_user = precisionk(actual=ground_truth[uid], predicted=predicted_user)
      REC_user = recallk(actual=ground_truth[uid], predicted=predicted_user)
      Novelty_user = novelty(predicted=predicted_user, pop=pop_items, u=eval_method.total_users, k=10)

      NDCG_all.append(NDCG_user)
      PRE_all.append(PRE_user)
      REC_all.append(REC_user)
      Novelty_all.append(Novelty_user)

      # cleaning the predicted list for a new user
      predicted_user.clear()

  catalog = catalog_coverage(predicted=All_Predicted, catalog=pop_items.keys())
  return round(np.mean(NDCG_all), 5), round(np.mean(PRE_all), 5), round(np.mean(REC_all), 5), round(np.mean(Novelty_all), 5), catalog

"""## Fairness"""

def fairness_optimisation(fairness='N', uepsilon=0.000005, iepsilon = 0.0000005):
  print(f"Runing fairness optimisation on '{fairness}', {format(uepsilon, 'f')}, {format(iepsilon, 'f')}")
  # V1: No. of users
  # V2: No. of top items (topk)
  # V3: No. of user groups
  # V4: no. og item groups
  V1, V2, V3, V4 = set(range(eval_method.total_users)), set(range(topk)), set(range(no_user_groups)), set(range(no_item_groups))

  # initiate model
  model = Model()

  # W is a matrix (size: user * top items) to be learned by model
  #W = [[model.add_var(var_type=BINARY) for j in V2] for i in V1]
  W = [[model.add_var() for j in V2] for i in V1]
  user_dcg = [model.add_var() for i in V1]
  user_ndcg = [model.add_var() for i in V1]
  group_ndcg_v = [model.add_var() for k in V3]
  item_group = [model.add_var() for k in V4]

  user_precision=[model.add_var() for i in V1]
  group_precision=[model.add_var() for k in V3]

  user_recall=[model.add_var() for i in V1]
  group_recall= [model.add_var() for k in V3]

  if fairness == 'N':
    ### No Fairness ###
    model.objective = maximize(xsum((S[i][j] * W[i][j]) for i in V1 for j in V2))
  elif fairness == 'C':
    ### C-Fairness: NDCG_Best: group_ndcg_v[1] - group_ndcg_v[0] ###
    model.objective = maximize(xsum((S[i][j] * W[i][j]) for i in V1 for j in V2) - uepsilon * (group_ndcg_v[1] - group_ndcg_v[0]))
  elif fairness == 'P':
    model.objective = maximize(xsum((S[i][j] * W[i][j]) for i in V1 for j in V2) - iepsilon * (item_group[0] - item_group[1]))
  elif fairness == 'CP':
    model.objective = maximize(xsum((S[i][j] * W[i][j]) for i in V1 for j in V2) - uepsilon * (group_ndcg_v[1] - group_ndcg_v[0]) - iepsilon * (item_group[0] - item_group[1]))

  # first constraint: the number of 1 in W should be equal to top-k, recommending top-k best items
  k = 10
  for i in V1:
      model += xsum(W[i][j] for j in V2) == k
  #这个设计思想太棒了，使得编码更加简洁易懂，
  for i in V1:
    user_idcg_i = 7.137938133620551

    model += user_dcg[i] == xsum((W[i][j] * Ahelp[i][j]) for j in V2)
    model += user_ndcg[i] == user_dcg[i] / user_idcg_i

    model += user_precision[i]==xsum((W[i][j] * Ahelp[i][j]) for j in V2) / k
    model += user_recall[i]==xsum((W[i][j] * Ahelp[i][j]) for j in V2) / len(train_checkins[i])

  for k in V3:
    model += group_ndcg_v[k] == xsum(user_dcg[i] * U[i][k] for i in V1)
    model += group_precision[k] == xsum(user_precision[i] * U[i][k] for i in V1)
    model += group_recall[k] == xsum(user_recall[i] * U[i][k] for i in V1)

  for k in V4:
    model += item_group[k]== xsum(W[i][j] * Ihelp[i][j][k] for i in V1 for j in V2)

  for i in V1:
    for j in V2:
      model += W[i][j] <= 1
  # optimizing
  model.optimize()

  return W, item_group

"""## Run"""

def write_results():
  ndcg_ac, pre_ac, rec_ac, novelty_ac, coverage_ac = metric_per_group(group=active_user_ids, W=W)
  ndcg_iac, pre_iac, rec_iac, novelty_iac, coverage_iac = metric_per_group(group=inactive_user_ids, W=W)
  ndcg_all, pre_all, rec_all, novelty_all, coverage_all = metric_on_all(W=W)
  if fair_mode == 'N':
    results.write(f"{dataset},{model.name},{u_group}%,{i_group}%,{fair_mode},-,-,{ndcg_all},{ndcg_ac},{ndcg_iac},{pre_all},{pre_ac},{pre_iac},{rec_all},{rec_ac},{rec_iac},{novelty_all},{novelty_ac},{novelty_iac},{coverage_all},{coverage_ac},{coverage_iac},{item_group[0].x},{item_group[1].x},{eval_method.total_users * 10}=={item_group[0].x + item_group[1].x}")
  elif fair_mode == 'C':
    results.write(f"{dataset},{model.name},{u_group}%,{i_group}%,{fair_mode},{format(user_eps, '.7f')},-,{ndcg_all},{ndcg_ac},{ndcg_iac},{pre_all},{pre_ac},{pre_iac},{rec_all},{rec_ac},{rec_iac},{novelty_all},{novelty_ac},{novelty_iac},{coverage_all},{coverage_ac},{coverage_iac},{item_group[0].x},{item_group[1].x},{eval_method.total_users * 10}=={item_group[0].x + item_group[1].x}")
  elif fair_mode == 'P':
    results.write(f"{dataset},{model.name},{u_group}%,{i_group}%,{fair_mode},-,{format(item_eps, '.7f')},{ndcg_all},{ndcg_ac},{ndcg_iac},{pre_all},{pre_ac},{pre_iac},{rec_all},{rec_ac},{rec_iac},{novelty_all},{novelty_ac},{novelty_iac},{coverage_all},{coverage_ac},{coverage_iac},{item_group[0].x},{item_group[1].x},{eval_method.total_users * 10}=={item_group[0].x + item_group[1].x}")
  elif fair_mode == 'CP':
    results.write(f"{dataset},{model.name},{u_group}%,{i_group}%,{fair_mode},{format(user_eps, '.7f')},{format(item_eps, '.7f')},{ndcg_all},{ndcg_ac},{ndcg_iac},{pre_all},{pre_ac},{pre_iac},{rec_all},{rec_ac},{rec_iac},{novelty_all},{novelty_ac},{novelty_iac},{coverage_all},{coverage_ac},{coverage_iac},{item_group[0].x},{item_group[1].x},{eval_method.total_users * 10}=={item_group[0].x + item_group[1].x}")
  results.write('\n')


"""## Run Config"""

# dataset congfig
ds_names = ["Gowalla"]
ds_users = ['005']
ds_items = ['020']

###
no_user_groups = 2
no_item_groups = 2
topk = 50 # this is not a length of recommendation ist, it is only the first topk items for the optimisation

#获取书籍集
download_dataset()
#获取用户组数据：没有返回值，说明保存在磁盘
download_user_groups()
download_item_groups()



#真正核心的调度算法在这
# 1: Iterate over the datasets
#首先获取到数据集的训练，验证，测试二部图，其中以三元组的形式，形成list
#然后借助corac方法，统计相应的信息，比如训练和测试集的节点个数，
#
for dataset in ds_names:
  print(f"Datasets: {dataset}")

  # read train, tune, test datasets
  #获取训练数据集，验证集，测试集:都是一个list，每个元素为三元组（）
  train_data, tune_data, test_data = read_data(dataset=dataset)

  # load data into Cornac and create eval_method
  eval_method = load_data(train_data=train_data, test_data=test_data)

  #获取训练数据集和测试集的总用户和物品数
  total_users = eval_method.total_users
  total_items = eval_method.total_items

  # 用户的交互物品集，  物品的交互频次字典
  train_checkins, pop_items = read_train_data(train_file = f"datasets/{dataset}/{dataset}_train.txt")
  # load ground truth dict          test_checkins:ground true 交互集合（字典）如：{0：{0,1,3}}
  ground_truth = read_ground_truth(test_file = f"datasets/{dataset}/{dataset}_test.txt")
  # run Cornac models and create experiment object including models' results
  exp = run_model(eval_method=eval_method)
  # 4: read user groups
    #这里有个维度，那就是到底使用百分之几作为用户的分隔阈值
  for u_group in ds_users:
    # 用户群组标识矩阵
    U = np.zeros((total_users, no_user_groups))
    # 帮忙更新U且返回ids的集合
    active_user_ids = read_user_groups(user_group_fpath = f"user_groups/{dataset}/{u_group}/active_ids.txt", gid = 0)
    inactive_user_ids = read_user_groups(user_group_fpath = f"user_groups/{dataset}/{u_group}/inactive_ids.txt", gid = 1)
    print(f"ActiveU: {len(active_user_ids)}, InActive: {len(inactive_user_ids)}, All: {len(active_user_ids) + len(inactive_user_ids)}")
    len_sizes = [len(active_user_ids), len(inactive_user_ids)]
    # 5: read item groups
    for i_group in ds_items:
      # read matrix I for items and their groups
      I = np.zeros((total_items, no_item_groups))
      # read item groups
      shorthead_item_ids = read_item_groups(item_group_fpath = f"item_groups/{dataset}/{i_group}/shorthead_items.txt", gid = 0)
      longtail_item_ids = read_item_groups(item_group_fpath = f"item_groups/{dataset}/{i_group}/longtail_items.txt", gid = 1)
      print(f"No. of Shorthead Items: {len(shorthead_item_ids)} and No. of Longtaill Items: {len(longtail_item_ids)}")
      # 2: iterate over the models
      for model in exp.models:
        #创建算法的结果输出文档
        results = open(f"results_{dataset}_{model.name}.csv", 'w')
        results.write("Dataset,Model,GUser,GItem,Type,User_EPS,Item_EPS,ndcg_ALL,ndcg_ACT,ndcg_INACT,Pre_ALL,Pre_ACT,Pre_INACT,Rec_ALL,Rec_ACT,Rec_INACT,Nov_ALL,Nov_ACT,Nov_INACT,Cov_ALL,Cov_ACT,Cov_INACT,Short_Items,Long_Items,All_Items\n")
        print(f"> Model: {model.name}")
        # load matrix S and P'''
        #   这个函数有什么用？
        #     获取S：所有用户对于所有物品的评分分数矩阵
        #     P：就是所有用户的Topk物品：没有select后的topK
        # '''
        S, P = load_ranking_matrices(model=model, total_users=total_users, total_items=total_items, topk=topk)
        # load matrix Ahelp：这个呢！就是模型泛化后，形成的top-k物品，然后有哪些是已经被推荐过了，就是训练数据集里的
        Ahelp = load_ground_truth_index(total_users=total_users, topk=topk, P=P, train_checkins=train_checkins)
        # load matrix Ihelp
        Ihelp = read_item_index(total_users=total_users, topk=50, no_item_groups=no_item_groups)
        # iterate on fairness mode: user, item, user-item
        for fair_mode in ['N', 'C']:
          if fair_mode == 'N':
            W, item_group = fairness_optimisation(fairness=fair_mode)
            write_results()
          elif fair_mode == 'C':
            for user_eps in [0.003, 0.0005, 0.0001, 0.00005, 0.000005]:
              W, item_group = fairness_optimisation(fairness=fair_mode, uepsilon=user_eps)
              write_results()
          elif fair_mode == 'P':
            for item_eps in [0.003, 0.0005, 0.0001, 0.00005, 0.000005]:
              W, item_group = fairness_optimisation(fairness=fair_mode, iepsilon=item_eps)
              write_results()
          elif fair_mode == 'CP':
            for user_eps in [0.003, 0.0005, 0.0001, 0.00005, 0.000005]:
              for item_eps in [0.003, 0.0005, 0.0001, 0.00005, 0.000005]:
                W, item_group = fairness_optimisation(fairness=fair_mode, uepsilon=user_eps, iepsilon=item_eps)
                write_results()
        results.close()

