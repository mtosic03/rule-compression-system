import pandas as pd
import numpy as np
from collections import defaultdict
import re

class RuleCompressor:
    def __init__(self):
        self.dataset=None
        self.rules=[]
        self.compressed_rules=[]
        self.predicate_stats={}
        self.rules_coverage={}
        self.rule_patterns={}

    #Loading data from tsv file
    def load_data(self,path):
        try:
            self.dataset = pd.read_csv(path, delimiter='\t')
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    #Loading data from txt file
    def load_rules(self,path):
        try:
            with open(path,'r') as file:
                self.rules=[line.strip() for line in file if line.strip()]
                return True
        except Exception as e:
            print(f"Error :{e}")
            return False

    #Parsing rules from txt to structure format
    def parse_rule(self,rule):
        lhs=rule.split(' => ')[0]
        predicates=[]

        for pred in re.split(' AND ',lhs):
            pred=pred.strip()
            if pred.startswith('NOT '):
                predicates.append(('NOT',pred[4:]))
            else:
                predicates.append(('',pred))

        return predicates
    #Evaluates a single predicate for a single row of data, checks if the predicate exists in the data
    def evaluate_predicates(self,predicate,record):
        negation, pred_name = predicate

        if pred_name not in record or pd.isna(record[pred_name]):
            return None
        value = record[pred_name]
        res = bool(value)

        return not res if negation == 'NOT' else res
    #Evaluates the entire rule for one row of data
    def evaluate_rule(self,predicates,record):
        results=[]
        for predicate in predicates:
            res=self.evaluate_predicates(predicate,record)
            if res is None:
                continue
            results.append(res)
        return all(results) if results else False
    #Calculates coverage and precision for each rule
    def calculate_rule_coverage(self):
        old_donors=self.dataset[self.dataset['donor_is_old']==True]
        young_donors=self.dataset[self.dataset['donor_is_old']==False]

        for i,rule in enumerate(self.rules):
            predicates=self.parse_rule(rule)

            tp = sum(1 for _, record in old_donors.iterrows()
                     if self.evaluate_rule(predicates, record))
            fp = sum(1 for _, record in young_donors.iterrows()
                     if self.evaluate_rule(predicates, record))

            coverage=tp/len(old_donors) if len(old_donors)>0 else 0
            precision=tp/(tp+fp) if tp+fp>0 else 0

            self.rules_coverage[i] = {
                'rule': rule,
                'predicates': predicates,
                'tp': tp,
                'fp': fp,
                'coverage': coverage,
                'precision': precision,
                'score': coverage * precision
            }
    #Finds redundant rules that can be removed
    def find_redundant_rules(self):
        redudant_rules=set()

        for i,rule_i in self.rules_coverage.items():
            for j,rule_j in self.rules_coverage.items():
                if i==j:
                    continue
                if(rule_i['coverage']<=rule_j['coverage'] and
                rule_i['precision']<=rule_j['precision'] and
                len(rule_i['predicates']) > len(rule_j['predicates'])):
                    redudant_rules.add(i)
                    break

        return redudant_rules
    #Groups similar rules that use the same predicates for later merging
    def group_similar_rules(self):
        rule_groups=defaultdict(list)

        for i,rule_data in self.rules_coverage.items():
            pred_names=sorted([p[1] for p in rule_data['predicates']])
            signature='_'.join(pred_names)
            rule_groups[signature].append(i)

        similar_groups = {k: v for k, v in rule_groups.items() if len(v) > 1}
        return similar_groups
    #Merging rules
    def merge_rules(self,rule_indices):
        if not rule_indices:
            return None

        best_index=max(rule_indices,key=lambda i:self.rules_coverage[i]['score'])
        return self.rules_coverage[best_index]['rule']
    #The main function that compresses the rule set using previously implemented functions
    def compress_rules(self):
        self.calculate_rule_coverage()

        redudant_rules=self.find_redundant_rules()
        similar_groups=self.group_similar_rules()
        kept_rules=[]

        for group_indices in similar_groups.values():
            merged_rule=self.merge_rules(group_indices)
            if merged_rule:
                kept_rules.append(merged_rule)

        used_indices=set()
        for group in similar_groups.values():
            used_indices.update(group)

        for i,rule_data in self.rules_coverage.items():
            if i not in redudant_rules and i not in used_indices:
                kept_rules.append(rule_data['rule'])

        rule_scores=[]

        for rule in kept_rules:
            predicates=self.parse_rule(rule)

            complexity=len(predicates)
            score=0

            for i,data in self.rules_coverage.items():
                if data['rule']==rule:
                    score=data['score']
                    break
            adjust_score=score/(complexity**0.5)
            rule_scores.append((rule,adjust_score))

        rule_scores.sort(key=lambda x:x[1],reverse=True)

        self.compressed_rules=[rule for rule,_ in rule_scores]
        return self.compressed_rules

    def save_compressed_rules(self,output_path):
        try:
            with open(output_path,'w') as file:
                for rule in self.compressed_rules:
                    file.write(f"{rule}\n")
                print(f"Saved {len(self.compressed_rules)} compressed rules to {output_path}.")
                return True
        except Exception as e:
            print(f"Error :{e}")
            return False

def main():
    compressor=RuleCompressor()

    dataset_path= "dataset.tsv"
    rules_path="rules.txt"
    output_path="rules_compressed.txt"

    if not compressor.load_data(dataset_path):
        return
    if not compressor.load_rules(rules_path):
        return

    compressor.compress_rules()
    compressor.save_compressed_rules(output_path)

if __name__ == '__main__':
    main()
