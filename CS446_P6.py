import math, copy
from pprint import pprint
from operator import itemgetter

class EffectivenessMeasures():
    def __init__(self):
        self.qid = []
        self.qid_NDCG = {}
        self.qrels = {}
        self.trec = {}

    def input_files(self, qrels, file=[]):
        # take qrel and parse it
        # 1: query id   3: doc id   4: relevancy 
        qrels = open(qrels, 'r')
        qrels = qrels.readlines()
        for line in qrels:
            columns = line.split()
            if not self.qrels.has_key(columns[0]):
                self.qrels[columns[0]] = {}
                self.qid.append(columns[0])

            self.qrels[columns[0]][columns[2]] = columns[3]

        # take trecrun files
        for f in file:
            trec = open(f, 'r')
            trec = trec.readlines()
            # for each query id
            for line in trec:
                columns = line.split()
                if not self.trec.has_key(columns[0]):
                    # query id, doc, rank, score, not text
                    self.trec[columns[0]] = []
                temp = [columns[0], columns[2], int(columns[3]), columns[4]]
                self.trec[columns[0]].append(temp)

    def mean(self, l):
        # each item in list
        counter = 0
        sum = 0
        for items in l:
            if items != 0:
                sum += items
                counter += 1

        if sum == 0 or counter == 0:
            return 0
        return sum/counter

    def NDCG(self, value=20):
        # for all queries
        ndcg_mean = []
        for qid in self.qid:
            if self.trec.has_key(qid):
                dcg_list = []
                # doc ids of first n values
                doc_id_list = []
                for val in range(value):
                    if len(self.trec[qid]) > val:
                        doc_id_list.append(self.trec[qid][val][1])

                # cross ref doc id with qrels
                for doc in doc_id_list:
                    if self.qrels[qid].has_key(doc):
                        dcg_list.append(int(self.qrels[qid][doc]))
                    else:
                        dcg_list.append(0)

                # original list
                original_list = copy.deepcopy(dcg_list)
                value = len(doc_id_list)
                    
                # run helper
                dcg_list = self.NDCG_helper(value, dcg_list)
        
                # ideal dcg: sort original dcg
                idcg_list = sorted(original_list, reverse=True)
                idcg_list = self.NDCG_helper(value, idcg_list)

                # normalized
                ndcg = []
                for i in range(value):
                    if dcg_list[i] == 0 or idcg_list[i] == 0:
                        ndcg.append(0)
                    else:
                        ndcg.append(dcg_list[i]/idcg_list[i])
                self.qid_NDCG[qid] = ndcg
                mean = self.mean(ndcg)
                ndcg_mean.append(mean)
                print qid, mean

        print self.mean(ndcg_mean)
        return self.mean(ndcg_mean)
        
    def NDCG_helper(self, value, dcg_list):
        # start algorithm
        temp = []
        for rank in range(value):
            result = dcg_list[rank]
            if dcg_list[rank] != 0 and math.log(rank+1, 2) != 0:
                result = (dcg_list[rank]/math.log(rank+1, 2))
            temp.append(result)
        dcg_list = copy.deepcopy(temp)

        # cumulative
        temp = []
        for cdcg in range(len(dcg_list)):
            if cdcg == 0:
                temp.append(dcg_list[cdcg])
            else:
                temp.append(dcg_list[cdcg] + temp[cdcg-1])
        dcg_list = copy.deepcopy(temp)

        return dcg_list

    def get_relevant_values(self, qid, value):
        rel_list = []
        for rank in range(value):
            did = self.trec[qid][rank][1]
            if self.qrels[qid].has_key(did):
                rel_list.append(float(self.qrels[qid][did]))
            else:
                rel_list.append(0)
        return rel_list

    def precision(self, qid, value):
        # relevant & retrieved from retrieved
        if self.trec.has_key(qid):
            precision_list = []
            if value > len(self.trec[qid]):
                value = len(self.trec[qid])
            rel_list = self.get_relevant_values(qid, value)
            # calc precision
            relevant = 0
            for rank in range(value):
                if rel_list[rank] != 0:
                    relevant += 1
                p = float(relevant)/(rank + 1)
                precision_list.append(p)
            #pprint(precision_list)
            return precision_list
        return [0]

    def recall(self, qid, value):
        # relevant & retrieved from relevant
        if self.trec.has_key(qid):
            recall_list = []
            if value > len(self.trec[qid]):
                value = len(self.trec[qid])
            rel_list = self.get_relevant_values(qid, value)

            # calc recall
            relevant = 0
            for rank in range(value):
                if rel_list[rank] != 0:
                    relevant += 1
                if len(rel_list) - rel_list.count(0) == 0:
                    p = 0
                else:
                    p = float(relevant)/(len(rel_list) - rel_list.count(0))
                recall_list.append(p)
            #pprint(recall_list)
            return recall_list
        else:
            return [0]

    def F1(self, qid, value):
        # 2RP/(R+P)
        if not self.trec.has_key(qid):
            return [0]

        F1 = []
        # if value is bigger than len of query items
        if value > len(self.trec[qid]):
            value = len(self.trec[qid])
        
        precision = self.precision(qid, value)
        #pprint(precision)
        recall = self.recall(qid, value)
        #pprint(recall)
        for rank in range(len(precision)):
            result = self.F1_helper(precision[rank], recall[rank])
            F1.append(result)
        #pprint(F1)
        return F1

    def F1_helper(self, p, r):
        if r == 0 or p == 0:
            return 0

        return (2 * r * p)/(r + p)

    def average_precision(self, qid):
        if not self.trec.has_key(qid):
            return 0

        # for each query
        relevant = self.get_relevant_values(qid, len(self.trec[qid]))
        precision = self.precision(qid, len(self.trec[qid]))
        av = []
        for rank in range(len(self.trec[qid])):
            if relevant[rank] > 0:
                av.append(precision[rank])
        if sum(av) == 0 or len(av) == 0:
            return 0
        result = self.mean(av)
        #print qid, result
        return result

    def sort_trec_by_ranks(self):
        # sort by ranks
        for qid in self.qid:
            counter = 0
            if self.trec.has_key(qid):
                self.trec[qid] = copy.deepcopy(sorted(self.trec[qid], key=itemgetter(2)))

                # add fillers to unknown ranks
                temp = []
                for item in self.trec[qid]:
                    counter += 1
                    if counter != item[2]:
                        for x in range(item[2] - counter):
                            temp.append([qid, None, counter, 0])
                            counter += 1
                        temp.append(item)

                self.trec[qid] = copy.deepcopy(temp)
        return

# main
if __name__ == '__main__':
    trec_files = ['stress.trecrun']
    EM = EffectivenessMeasures()
    EM.input_files('qrels', trec_files)
    # if stress.trecrun
    if trec_files.count('stress.trecrun') > 0:
        EM.sort_trec_by_ranks()
    # NDCG@20
    #EM.NDCG()
    val = []
    #for qid in EM.qid:
        # P@5
        #val.append(EM.mean(EM.precision(qid, 5)))
        # P@10
        #val.append(EM.mean(EM.precision(qid, 10)))
        # R@10
        #val.append(EM.mean(EM.recall(qid, 10)))
        # F1@10
        #val.append(EM.mean(EM.F1(qid, 10)))
        # AP: lower result due to inclusion of all the queries
        #val.append(EM.average_precision(qid))
    #print EM.mean(val)