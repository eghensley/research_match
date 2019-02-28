import os
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()
while cur_path.split('/')[-1] != 'research_match':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))
    
from pymongo import MongoClient
import _config
from collections import Counter
import json
import pandas as pd
import math
import numpy as np
from sklearn.utils.class_weight import compute_class_weight
from progress_bar import progress
import random
from copy import deepcopy
from sklearn.preprocessing import MinMaxScaler
import operator 
import matplotlib.pyplot as plt

def exp_decay(p, t, r = .5):
    a = p * math.exp(r*t*-1)
    return(a)
    
with open(os.path.join(cur_path, 'test_nlu.json')) as f:
    _test_data = json.load(f)
    
    
mongodb_client = MongoClient(_config.mongodb_creds)
DB = mongodb_client['marine_science']


data = {}
for entry in DB['research_gate'].find():
    if 'abstract' not in entry.keys():
        continue
    else:
        if 'nlu' not in entry['abstract'].keys():
            continue
        else:
            data[entry['_id']] = entry['abstract']['nlu']
    

def find_corpus():
    all_kws = []
    all_conc = []
    all_cat = []
    
    for k,v in data.items():
#        if str(k) == '5c5257606ac7b328a31d83ba':
#            asdfasdf
        for kw in v['keywords']:
            all_kws.append(kw['text'].replace(' ', '_').lower())
        for con in v['concepts']:
            all_conc.append(con['text'].replace(' ', '_').lower())
            
        for cat in v['categories']:
            _cat_len = len(cat['label'].split('/'))
            for _cat_split in range(_cat_len-1):
                all_cat.append('/'.join(cat['label'].split('/')[0:_cat_split + 2]).replace(' ', '_').lower())
        
    return(all_kws, all_conc, all_cat)
    

def find_weights():
    all_kws, all_conc, all_cat = find_corpus()
#    all_kws_set = set(all_kws)
#    all_conc_set = set(all_conc)
#    all_cat_set = set(all_cat)

#    in_scope_kws = set([i for i,j in Counter(all_kws).most_common()])
#    kw_weights_ = {j:k for j,k in zip(np.unique([i for i in all_kws if i in in_scope_kws]), compute_class_weight('balanced', np.unique([i for i in all_kws if i in in_scope_kws]), [i for i in all_kws if i in in_scope_kws]))}
    kw_weights_ = {j:k for j,k in zip(np.unique(all_kws), compute_class_weight('balanced', np.unique(all_kws), all_kws))}
    use_kws_ = set(kw_weights_.keys())
    
#    in_scope_conc = set([i for i,j in Counter(all_conc).most_common()])
#    conc_weights_ = {j:k for j,k in zip(np.unique([i for i in all_conc if i in in_scope_conc]), compute_class_weight('balanced', np.unique([i for i in all_conc if i in in_scope_conc]), [i for i in all_conc if i in in_scope_conc]))}
    conc_weights_ = {j:k for j,k in zip(np.unique(all_conc), compute_class_weight('balanced', np.unique(all_conc), all_conc))}
    use_conc_ = set(conc_weights_.keys())
    
    exp_cats = []
    for dif_cat in all_cat:
        _cat_len = len(dif_cat.split('/'))
        for _cat_split in range(_cat_len-1):
            exp_cats.append('/'.join(dif_cat.split('/')[0:_cat_split + 2]))
#    in_scope_cat = set([i for i,j in Counter(exp_cats).most_common()])
#    cat_weights_ = {j:k for j,k in zip(np.unique([i for i in exp_cats if i in in_scope_cat]), compute_class_weight('balanced', np.unique([i for i in exp_cats if i in in_scope_cat]), [i for i in exp_cats if i in in_scope_cat]))}
    cat_weights_ = {j:k for j,k in zip(np.unique(exp_cats), compute_class_weight('balanced', np.unique(exp_cats), exp_cats))}
    use_cat_ = set(cat_weights_.keys())
    
    return(use_kws_, kw_weights_, use_conc_, conc_weights_, use_cat_, cat_weights_)


def _gen_indices():
    use_kws, kw_weights, use_conc, conc_weights, use_cat, cat_weights = find_weights()

    _kw_index = {i:[] for i in use_kws}
    _conc_index = {i:[] for i in use_conc}
    _cat_index = {i:[] for i in use_cat}
    
    total_docs = len(data)
    for doc_num, (idx,v) in enumerate(data.items()):   
        
        for doc_kw in v['keywords']:
            _kw_index[doc_kw['text'].replace(' ', '_').lower()] += [{'doc_id': idx, 'score': doc_kw['relevance'] * kw_weights[doc_kw['text'].replace(' ', '_').lower()]}]
        
        for doc_conc in v['concepts']:
            _conc_index[doc_conc['text'].replace(' ', '_').lower()] += [{'doc_id': idx, 'score': doc_conc['relevance'] * conc_weights[doc_conc['text'].replace(' ', '_').lower()]}]

        for doc_cat in v['categories']:
            _cat_index[doc_cat['label'].replace(' ', '_').lower()] += [{'doc_id': idx, 'score': doc_cat['score'] * cat_weights[doc_cat['label'].replace(' ', '_').lower()]}]

        progress(doc_num + 1, total_docs)

    print('\n')
    return(_kw_index, _conc_index, _cat_index)


def validate_results():
    kw_index, conc_index, cat_index = _gen_indices()
    
    with open(os.path.join(cur_path, 'test_nlu.json')) as f:
        test_data = json.load(f)

    test_cat = test_data['test']['categories']
    cat_matches = {}
    for _cat in test_cat:
        _cat_full_score = _cat['score']
        for _exp_num, (_cat_exp) in enumerate(reversed(_cat['label'].split('/'))):
            if _cat_exp == '':
                continue
            if _exp_num == 0:
                _cat_exp_ = _cat['label'].replace(' ','_').lower()
            else:
                _cat_exp_ = '/'.join(_cat['label'].split('/')[:-_exp_num]).replace(' ', '_').lower()            
            
            if _cat_exp_ in cat_index.keys():
                for match_doc in cat_index[_cat_exp_]:
                    if match_doc['doc_id'] not in cat_matches.keys():
                        cat_matches[match_doc['doc_id']] = {'cat_score': match_doc['score'] * exp_decay(_cat_full_score, _exp_num), 'cat_count': 1}
                    else:
                        cat_matches[match_doc['doc_id']]['cat_score'] += match_doc['score'] * exp_decay(_cat_full_score, _exp_num)
                        cat_matches[match_doc['doc_id']]['cat_count'] += 1 
                    
    test_conc = test_data['test']['concepts']
    conc_matches = {}
    for _conc in test_conc:
        if _conc['text'].replace(' ','_').lower() in conc_index.keys():
            for match_doc in conc_index[_conc['text'].replace(' ','_').lower()]:
                if match_doc['doc_id'] not in conc_matches.keys():
                    conc_matches[match_doc['doc_id']] = {'conc_score': match_doc['score'] * _conc['relevance'], 'conc_count': 1}
                else:
                    conc_matches[match_doc['doc_id']]['conc_score'] += match_doc['score'] * _conc['relevance']
                    conc_matches[match_doc['doc_id']]['conc_count'] += 1
       
    test_kw = test_data['test']['keywords']
    kw_matches = {}
    for _kw in test_kw:
        if _kw['text'].replace(' ','_').lower() in kw_index.keys():
            for match_doc in kw_index[_kw['text'].replace(' ','_').lower()]:
                if match_doc['doc_id'] not in kw_matches.keys():
                    kw_matches[match_doc['doc_id']] = {'kw_score': match_doc['score'] * _kw['relevance'], 'kw_count': 1}
                else:
                    kw_matches[match_doc['doc_id']]['kw_score'] += match_doc['score'] * _kw['relevance']
                    kw_matches[match_doc['doc_id']]['kw_count'] += 1   
    
    kw_match_df = pd.DataFrame.from_dict(kw_matches).T
    conc_match_df = pd.DataFrame.from_dict(conc_matches).T
    cat_match_df = pd.DataFrame.from_dict(cat_matches).T
    
    all_matches = kw_match_df.join(conc_match_df).join(cat_match_df)
    all_matches.fillna(0, inplace = True)
    
    
    match2 = [
    'https://www.researchgate.net/publication/324546499_Patterns_drivers_and_effects_of_alligator_movement_behavior_and_habitat_use',
    'https://www.researchgate.net/publication/329186922_Sympatry_or_syntopy_Investigating_drivers_of_distribution_and_co-occurrence_for_two_imperiled_sea_turtle_species_in_Gulf_of_Mexico_neritic_waters',
    'https://www.researchgate.net/publication/325706625_Multiple_predator_effects_on_juvenile_prey_survival',
    'https://www.researchgate.net/publication/328857625_Clayton_D_2017_Feeding_Behavior_A_Review_in_Fishes_out_of_water_biology_and_ecology_of_mudskippers_ed_by_Zeehan_Jaafar_and_Edward_O_Murdy_CRC_Press_Pp_237-275']
    
    match1 = [
    'https://www.researchgate.net/publication/330703032_Spatial_contraction_of_demersal_fish_populations_in_a_large_marine_ecosystem',
    'https://www.researchgate.net/publication/330695197_When_good_animals_love_restored_habitat_in_bad_neighborhoods_ecological_traps_for_eastern_cottontails_in_agricultural_landscapes',
    'https://www.researchgate.net/publication/318863709_Foraging_feeding_and_physiological_stress_responses_of_wild_wood_mice_to_increased_illumination_and_common_genet_cues',
    'https://www.researchgate.net/publication/330621769_Prioritization_of_landscape_connectivity_for_the_conservation_of_Peary_caribou',
    'https://www.researchgate.net/publication/324131672_Advances_in_ecological_research_regarding_rhesus_macaques_Macaca_mulatta_in_China']
    
    match1idx = []
    match2idx = []
    
    for url_tag in match2:
        docc = [i for i in DB['research_gate'].find({"url_tag": url_tag.replace('https://www.researchgate.net/', '')})]
        match2idx.append(docc[0]['_id'])
    for url_tag in match1:
        docc = [i for i in DB['research_gate'].find({"url_tag": url_tag.replace('https://www.researchgate.net/', '')})]
        match1idx.append(docc[0]['_id'])
        
    all_matches['validation'] = [2 if i in match2idx else (1 if i in match1idx else 0) for i in all_matches.index]
    return(all_matches)

def rand_coef_test(matches_df):
#    matches_df = all_matches
    coefficients = {}
    for var in ['kw_count', 'kw_score', 'conc_count', 'conc_score']:
        coefficients[var] = random.randint(0, 101)
    coeff_total = np.sum([i for i in coefficients.values()])
    for var in ['kw_count', 'kw_score', 'conc_count', 'conc_score']:
        coefficients[var] = coefficients[var]/coeff_total
    
    match_df = deepcopy(matches_df)
    match_df['total_score'] = (match_df['kw_score']*coefficients['kw_score']) + (match_df['kw_count']*coefficients['kw_count']) + (match_df['conc_score']*coefficients['conc_score']) + (match_df['conc_count']*coefficients['conc_count'])
    match_df.sort_values('total_score', inplace = True, ascending = False)
    match_df.reset_index(inplace = True)
    loc2 = match_df.loc[match_df['validation'] == 2].index
    loc1 = match_df.loc[match_df['validation'] == 1].index
    
    match_score = np.sum([exp_decay(2, i) for i in loc2]) + np.sum([exp_decay(1, i) for i in loc1])

    iter_result = {'params': coefficients, 'score': match_score}
    return(iter_result)

def parameter_search():
#    total_trials = 1000
    all_matches = validate_results()
#    all_test_res = {}
    for col in ['kw_count', 'kw_score', 'conc_count', 'conc_score', 'cat_score', 'cat_count']:
        all_matches[col] = MinMaxScaler(feature_range=(-1, 1)).fit_transform(all_matches[col].values.reshape(-1,1))
    prev_best_score = 0
    prev_best_params = {}
    
    while prev_best_score < 9.700349393342249:
        test_res = rand_coef_test(all_matches)  
        if test_res['score'] > prev_best_score:
            print('~~ Improved Search Results ~~')
            print(' Match Score: %.3f' % (test_res['score']))
            print(test_res['params'])
            print()
            prev_best_score = test_res['score']
            prev_best_params = test_res['params']


class Gen_Search:

    def __init__(self, initial_pop_size, elite_size, mutation_rate, number_iterations):
        self.init_pop = initial_pop_size
        self.current_gen = 0
        self.max_gen = number_iterations
        self.data = validate_results()
        self.genes = ['kw_count', 'kw_score', 'conc_count', 'conc_score', 'cat_score', 'cat_count']
        for col in self.genes:
            self.data[col] = MinMaxScaler(feature_range=(-1, 1)).fit_transform(self.data[col].values.reshape(-1,1))
        self.population = self.initial_population()
        self.num_elite = int(elite_size * self.init_pop)
        self.mut_rate = mutation_rate
        self.results = {}
        self.fitness_results = self.rank_coef()
        self.selection_results = []
        self.matingpool = []
        self.children = []
        

    def score_coef(self, coefficients):
        match_df = deepcopy(self.data)
        match_df['total_score'] = (match_df['kw_score']*coefficients['kw_score']) + (match_df['kw_count']*coefficients['kw_count']) + (match_df['conc_score']*coefficients['conc_score']) + (match_df['conc_count']*coefficients['conc_count']) + (match_df['cat_count']*coefficients['cat_count']) + + (match_df['cat_score']*coefficients['cat_score'])
        match_df.sort_values('total_score', inplace = True, ascending = False)
        match_df.reset_index(inplace = True)
        loc2 = match_df.loc[match_df['validation'] == 2].index
        loc1 = match_df.loc[match_df['validation'] == 1].index
        match_score = np.sum([exp_decay(2, i) for i in loc2]) + np.sum([exp_decay(1, i) for i in loc1])
        return(match_score)
        
    def create_weights(self):
        weight_coef = {}
        for var in self.genes:
            weight_coef[var] = random.randint(-100, 101)
        return(weight_coef)      
        
    def initial_population(self):
        population = []
        for i in range(0, self.init_pop):
            population.append(self.create_weights())
        return(population)

    def rank_coef(self):
        fit_res = {}
        for i, (individual) in enumerate(self.population):
            fit_res[i] = self.score_coef(individual)
        fitness_res = sorted(fit_res.items(), key = operator.itemgetter(1), reverse = True)
        self.results[self.current_gen] = {'best_score':np.max([i[1] for i in fitness_res]), 
                                        'pop_std': np.std([i[1] for i in fitness_res]), 
                                        'pop_mean': np.std([i[1] for i in fitness_res]), 
                                        'best_params': self.population[fitness_res[0][0]]}    
        return(fitness_res)

    def selection(self):    
        selectionresults = []
        df = pd.DataFrame(np.array(self.fitness_results), columns=["Index","Fitness"])
        df['cum_sum'] = df.Fitness.cumsum()
        df['cum_perc'] = 100*df.cum_sum/df.Fitness.sum()
        
        for i in range(0, self.num_elite):
            selectionresults.append(self.fitness_results[i][0])
        for i in range(0, len(self.fitness_results) - self.num_elite):
            pick = 100*random.random()
            for i in range(0, len(self.fitness_results)):
                if pick <= df.iat[i,3]:
                    selectionresults.append(self.fitness_results[i][0])
                    break
        self.selection_results = selectionresults

    def gen_mating_pool(self):
        mating_pool = []
        for i in range(0, len(self.selection_results)):
            index = self.selection_results[i]
            mating_pool.append(self.population[index])
        self.matingpool = mating_pool

    def breed(self, parent1, parent2):
    #    parent1, parent2 = pool[i], pool[len(gen_data.matingpool)-i-1]
        child = {}
        genes = parent1.keys()
        for k in genes:
            if random.random() < .5:
                child[k] = parent1[k]
            else:
                child[k] = parent2[k]
        return child

    def breed_population(self):      
        self.children = []
        length = len(self.matingpool) - self.num_elite
        pool = random.sample(self.matingpool, len(self.matingpool))
    
        for i in range(0,self.num_elite):
            self.children.append(self.matingpool[i])
        
        for i in range(0, length):
            child = self.breed(pool[i], pool[len(self.matingpool)-i-1])
            self.children.append(child)

    def mutate(self, individual):
    #    individual = gen_data.population[ind]
        for swapped in self.genes:
            if(random.random() < self.mut_rate):
                swapWith = random.choice([i for i in self.genes if i != swapped])
                
                gene1 = individual[swapped]
                gene2 = individual[swapWith]
                
                individual[swapped] = gene2
                individual[swapWith] = gene1
        return(individual)

    def mutate_population(self):
        mutated_pop = []
        
        for ind in range(0, len(self.population)):
            mutated_idv = self.mutate(self.population[ind])
            mutated_pop.append(mutated_idv)
        self.population = mutated_pop     

    def next_generation(self):
        self.selection()
        self.gen_mating_pool()
        self.breed_population()
        self.mutate_population()
        self.current_gen += 1
        self.fitness_results = self.rank_coef()

    def simulate(self):
        for gen in range(self.max_gen):
            self.next_generation()
            progress(self.current_gen + 1, self.max_gen)
        print('\n')
    
    
gen_data = Gen_Search(100, 0, .3, 100)
gen_data.simulate()

scores = [i['best_score'] for i in gen_data.results.values()]
stds = np.array([i['pop_std'] for i in gen_data.results.values()])
means = np.array([i['pop_mean'] for i in gen_data.results.values()])
best_params = [i['best_params'] for i in gen_data.results.values()]

fig, ax1 = plt.subplots(1)
ax1.plot(gen_data.results.keys(), scores, c = 'r')
ax2 = ax1.twinx()
ax2.plot(gen_data.results.keys(), means, c = 'b')
ax2.fill_between(gen_data.results.keys(), means+stds, means-stds, facecolor='blue', alpha=0.2)
ax1.set_title('Genetic Algorithm Improvements')
ax1.set_xlabel('Generation')
ax1.set_ylabel('Score')


#fig, ax = plt.subplots(1)
#ax.plot(gen_data.results.keys(), scores)
#ax.fill_between(gen_data.results.keys(), means+stds, means-stds, facecolor='blue', alpha=0.5)
#ax.set_title('Genetic Algorithm Improvements')
#ax.set_xlabel('Generation')
#ax.set_ylabel('Score')

#if __name__ == '__main__':
#    parameter_search()



