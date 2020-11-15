import json
import pandas as pd
import itertools


# ------------------ FORCE GRAPH ---------------- #
# This code set the colors equal to black for papers and the colors
# in colorlist.json for the other keywords
force_graph = False
if force_graph:
    with open('papers.json') as f:
        papers = json.load(f)

    with open('colorlist.json') as f:
        colors = json.load(f)

    nodes = []
    existing_nodes = []
    links = []

    def iterate(dictionary, group_col, col_dict):
        for d_key, d_value in dictionary.items():
            if d_key == 'name':
                source = d_value
                if d_value not in existing_nodes:
                    if d_value in col_dict.keys():
                        nodes.append({"id": d_value, "group": col_dict[d_value]})
                    else:
                        nodes.append({"id": d_value, "group": group_col})
                    existing_nodes.append(d_value)
            else:
                for v_item in d_value:
                    links.append({"source": source, "target": v_item['name'], "value": 1})
                    if isinstance(v_item, dict):
                        iterate(v_item, group_col, col_dict)
                        continue
    iterate(papers, 'black', colors)

    outdict = {"nodes": nodes, "links": links}
    with open('result.json', 'w') as fp:
        json.dump(outdict, fp)


# ------------------ HIERARCHICAL EDGE BUNDLING ---------------- #
edge_graph = False
if edge_graph:
    all_nodes = []
    he_existing_nodes = []
    out_dict2 = {}
    df = pd.read_csv('keywords.csv')
    for index, row in df.iterrows():
        # split the string into a list of keywords
        keys = row.keywords.split(';')
        keys = [k.lstrip() for k in keys]
        if 'Post-hoc' in keys:
            keys.remove('Post-hoc')
            keys = ['flare.Post-hoc.'+k for k in keys]
        elif 'Ante-hoc' in keys:
            keys.remove('Ante-hoc')
            keys = ['flare.Ante-hoc.'+k for k in keys]
        else:
            keys = ['flare.Other.'+k for k in keys]
        all_nodes = all_nodes + keys
        comb = list(itertools.combinations(keys, 2))
        for item in comb:
            if str(item[0]+item[1]) in out_dict2:
                out_dict2[str(item[0] + item[1])]['size'] += 1
            elif str(item[1]+item[0]) in out_dict2:
                out_dict2[str(item[1] + item[0])]['size'] += 1
            else:
                he_existing_nodes.append(item[0])
                out_dict2[str(item[0] + item[1])] = {'name': item[0], 'size': 1, 'imports': [item[1]]}

    all_nodes = list(set(all_nodes))
    he_existing_nodes = list(set(he_existing_nodes))

    out_list = []
    for key, value in out_dict2.items():
        out_list.append(value)

    missing_nodes = [x for x in all_nodes if x not in he_existing_nodes]

    for item in missing_nodes:
        out_list.append({'name': item, 'size': 1, 'imports': []})

    # Joining dictionaries with same name
    index_list = []
    for i in range(len(out_list)):
        for j in range(i+1, len(out_list)):
            if out_list[i]['name'] == out_list[j]['name']:
                out_list[i]['size'] = out_list[i]['size'] + out_list[j]['size']
                out_list[i]['imports'] = out_list[i]['imports'] + out_list[j]['imports']
                index_list.append(j)

    index_list = list(set(index_list))
    for index in sorted(index_list, reverse=True):
        out_list.pop(index)

    print(len(out_list))

    with open('flare.json', 'w') as fp:
        json.dump(out_list, fp)


# --------------------------------- WORD CLOUD --------------------------------#
word_cloud = False
if word_cloud:
    df = pd.read_csv('keywords.csv')
    text = []
    for index, row in df.iterrows():
        # split the string into a list of keywords
        keys = row.keywords.split(';')
        keys = [k.lstrip() for k in keys]
        text = text + keys

    utext = [(i, text.count(i)) for i in set(text)]

    out_list = []
    for item in utext:
        out_list.append({"text": item[0], "size": item[1]})

    with open('wordcloud.json', 'w') as fp:
        json.dump(out_list, fp)

    comm = """
    wordcloud = WordCloud(
        width = 1000,
        height = 500,
        background_color = 'white',
        stopwords = STOPWORDS).generate(str(text))
    fig = plt.figure(
        figsize = (40, 30),
        facecolor = 'k',
        edgecolor = 'k')
    plt.imshow(wordcloud, interpolation = 'bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)q
    plt.show()
    """

# ------------------------------------------------------------------ #
# ------------------------- EXPANDABLE TREE ------------------------ #
# ------------------------------------------------------------------ #


def url_list(id_list, url_df):
    """
    This function returns a list of dictionaries with the paper ids and urls
    """
    ret = []
    for id_item in id_list:
        url = url_df['link'][url_df['ID'] == id_item].tolist()[0]
        ret.append({'name': id_item, 'url': url})

    return ret


def id_manager(in_group):
    """
    This function returns a list of IDS
    """
    id_group = in_group['ID'].tolist()
    id_group = list(itertools.chain.from_iterable([ix.split(',') for ix in id_group]))
    id_group = list(set([k.lstrip() for k in id_group]))
    return id_group


# ------------------ EXPANDABLE TREE REVIEWS BRANCH ---------------- #
tree_reviews = False
if tree_reviews:
    df_reviews = pd.read_csv('reviews.csv')
    urls = pd.read_csv('urls.csv')
    review_dict = {"name": "Reviews", "children": []}

    review_groups = df_reviews.groupby(['Branch'])

    for name, group in review_groups:
        if len(group) == 1:
            ids = id_manager(group)
            group_dict = {'name': name, 'children': url_list(ids, urls)}
            review_dict['children'].append(group_dict)
        else:
            subbranches = group.groupby(['Sub_branch'])
            sub_dict = {"name": name, "children": []}
            for key, subgroup in subbranches:
                ids = id_manager(subgroup)
                group_dict = {'name': key, 'children': url_list(ids, urls)}
                sub_dict['children'].append(group_dict)
            review_dict['children'].append(sub_dict)

    with open('tree_reviews.json', 'w') as fp:
        json.dump(review_dict, fp)


# ------------------ EXPANDABLE TREE NOTIONS BRANCH ---------------- #
tree_notions = False
if tree_notions:
    df_notions = pd.read_csv('notions.csv')
    urls = pd.read_csv('urls.csv')
    notion_dict = {"name": "Notions", "children": []}

    notion_groups = df_notions.groupby(['Branch', 'Attribute cleaned'])

    attribute_dict = {"name": "Attributes", "children": []}
    other_dict = []
    for name, group in notion_groups:
        ids = id_manager(group)
        if name[0] == 'Attributes':
            group_dict = {'name': name[1], 'children': url_list(ids, urls)}
            attribute_dict['children'].append(group_dict)
        else:
            group_dict = {'name': name[0], 'children': url_list(ids, urls)}
            other_dict.append(group_dict)
    notion_dict['children'].append(attribute_dict)
    notion_dict['children'] = notion_dict['children'] + other_dict

    with open('tree_notions.json', 'w') as fp:
        json.dump(notion_dict, fp)


# ------------------ EXPANDABLE TREE EVALUATION BRANCH ---------------- #
tree_evaluation = False
if tree_evaluation:
    df_evaluation = pd.read_csv('evaluation.csv')
    urls = pd.read_csv('urls.csv')
    evaluation_dict = {"name": "Evaluation", "children": []}
    evaluation_groups = df_evaluation.groupby(['Branch'])

    for name, group in evaluation_groups:
        branch_group = {"name": name, "children": []}
        subbranches1 = group.groupby(['Sub_branch_1'])
        for key, subgroup in subbranches1:
            if len(subgroup) == 1:
                ids = id_manager(subgroup)
                group_dict = {'name': key, 'children': url_list(ids, urls)}
                branch_group['children'].append(group_dict)
            else:
                branch_group1 = {"name": key, "children": []}
                subbranches2 = subgroup.groupby(['Sub_branch_2'])
                for key2, subgroup2 in subbranches2:
                    if len(subgroup2) == 1 and subgroup2['Sub_branch_3'].tolist()[0] == 'None':
                        ids = id_manager(subgroup2)
                        group_dict2 = {'name': key2, 'children': url_list(ids, urls)}
                        branch_group1['children'].append(group_dict2)
                    else:
                        branch_group2 = {"name": key2, "children": []}
                        subbranches3 = subgroup2.groupby(['Sub_branch_3'])
                        for key3, subgroup3 in subbranches3:
                            ids = id_manager(subgroup3)
                            group_dict3 = {'name': key3, 'children': url_list(ids, urls)}
                            branch_group2['children'].append(group_dict3)
                        branch_group1['children'].append(branch_group2)
                branch_group['children'].append(branch_group1)
        evaluation_dict['children'].append(branch_group)

    with open('tree_evaluation.json', 'w') as fp:
        json.dump(evaluation_dict, fp)


# ------------------ EXPANDABLE TREE EVALUATION BRANCH (WITHOUT THIRD LEVEL BRANCH) ---------------- #
tree_evaluation = False
if tree_evaluation:
    df_evaluation = pd.read_csv('evaluation.csv')
    urls = pd.read_csv('urls.csv')
    evaluation_dict = {"name": "Evaluation", "children": []}
    evaluation_groups = df_evaluation.groupby(['Branch'])

    for name, group in evaluation_groups:
        branch_group = {"name": name, "children": []}
        subbranches1 = group.groupby(['Sub_branch_1'])
        for key, subgroup in subbranches1:
            if len(subgroup) == 1:
                ids = id_manager(subgroup)
                group_dict = {'name': key, 'children': url_list(ids, urls)}
                branch_group['children'].append(group_dict)
            else:
                branch_group1 = {"name": key, "children": []}
                subbranches2 = subgroup.groupby(['Sub_branch_2'])
                for key2, subgroup2 in subbranches2:
                    ids = id_manager(subgroup2)
                    group_dict2 = {'name': key2, 'children': url_list(ids, urls)}
                    branch_group1['children'].append(group_dict2)
                branch_group['children'].append(branch_group1)
        evaluation_dict['children'].append(branch_group)

    with open('tree_evaluation.json', 'w') as fp:
        json.dump(evaluation_dict, fp)


# ------------------ EXPANDABLE TREE METHODS BRANCH ---------------- #
tree_methods = False
if tree_methods:
    df_ah = pd.read_csv('ante-hoc.csv')
    df_ph = pd.read_csv('post-hoc.csv')
    urls = pd.read_csv('urls.csv')

    ante_hoc_dict = {"name": "Ante-hoc", "children": []}
    df_ah_groups = df_ah.groupby(['method'])
    for name, group in df_ah_groups:
        ids = group['ID'].tolist()
        ids = list(itertools.chain.from_iterable([item.split(',') for item in ids]))
        ids = list(set([k.lstrip() for k in ids]))
        group_dict = {'name': name, 'children': url_list(ids, urls)}
        ante_hoc_dict['children'].append(group_dict)

    post_hoc_dict = {"name": "Post-hoc", "children": []}
    mod_spec_group_dict = {'name': 'Model specific', 'children': []}
    df_ph_groups = df_ph.groupby(['model_type'])

    for name, group in df_ph_groups:
        mod_group_dict = {'name': name, 'children': []}
        subgroups = group.groupby(['method'])
        for s_name, s_group in subgroups:
            ids = s_group['ID'].tolist()
            ids = list(itertools.chain.from_iterable([item.split(',') for item in ids]))
            ids = list(set([k.lstrip() for k in ids]))
            sub_group_dict = {'name': s_name, 'children': url_list(ids, urls)}
            mod_group_dict['children'].append(sub_group_dict)
    
        if name == 'Model agnostic':
            post_hoc_dict['children'].append(mod_group_dict)
        else:
            mod_spec_group_dict['children'].append(mod_group_dict)
    
    post_hoc_dict['children'].append(mod_spec_group_dict)

    tree_out_dict = [{"name": "Stage", "children": [ante_hoc_dict, post_hoc_dict]}]

    # Merging post-hoc and ante-hoc methods together
    df = df_ah
    df = df.append(df_ph, ignore_index=True)

    def group_creator(in_df, column, root_name):
        out_var = {'name': root_name, 'children': []}
        col_groups = in_df.groupby([column])
        for col_name, col_group in col_groups:
            col_group_dict = {'name': col_name, 'children': []}
            initial_groups = col_group.groupby(['initials'])
            for init_name, init_group in initial_groups:
                init_group_dict = {'name': init_name, 'children': []}
                sub_groups = init_group.groupby(['method'])
                for sub_name, sub_group in sub_groups:
                    sub_ids = sub_group['ID'].tolist()
                    sub_ids = list(itertools.chain.from_iterable([ix.split(',') for ix in sub_ids]))
                    sub_ids = list(set([k.lstrip() for k in sub_ids]))
                    sub_group_dict = {'name': sub_name, 'children': url_list(sub_ids, urls)}
                    init_group_dict['children'].append(sub_group_dict)
                col_group_dict['children'].append(init_group_dict)
            out_var['children'].append(col_group_dict)
        return out_var

    scope = group_creator(df, 'scope', 'Scope')
    tree_out_dict.append(scope)

    problem = group_creator(df, 'problem_type', 'Problem type')
    tree_out_dict.append(problem)

    input_data = group_creator(df, 'input_type', 'Input data')
    tree_out_dict.append(input_data)

    input_data = group_creator(df, 'explanation_type', 'Output format')
    tree_out_dict.append(input_data)

    with open('tree_methods.json', 'w') as fp:
        json.dump(tree_out_dict, fp)


# ---------------------- SUBSTITUTING PAPERS WITH REF NUMBERS ------------------------ #
numb_tree = False
if numb_tree:
    df_ref = pd.read_csv('paper_ref_number.csv')

    with open('papers.json') as json_file:
        tree_data = json.load(json_file)

    def iterate2(dictionary, in_df):
        ref_numbers = in_df.ID.tolist()
        for it_key, it_value in dictionary.items():
            if it_key == 'name':
                if it_value in ref_numbers:
                    dictionary[it_key] = in_df['Data'][in_df.ID == it_value].tolist()[0]
            else:
                for it_item in it_value:
                    if isinstance(it_item, dict):
                        iterate2(it_item, in_df)
                        continue
        return dictionary

    tree_out_dict = iterate2(tree_data, df_ref)

    with open('paper_numbers.json', 'w') as fp:
        json.dump(tree_out_dict, fp)


# ---------------------------------- SUNBURST --------------------------------------- #

def import_json_file(name):
    with open(name) as f:
      ret = json.load(f)
    return ret


def counters(in_dict):
    out_dict = {'name': in_dict['name'], 'value': len(in_dict['children'])}
    if 'url' not in in_dict['children'][0].keys():
        out_dict['children'] = []
        for new_dict in in_dict['children']:
            if 'url' not in new_dict.keys():
                out_dict['children'].append(counters(new_dict))
    return out_dict


evaluation = import_json_file('tree_evaluation.json')
methods = {'name': 'Methods', 'children': import_json_file('tree_methods.json')}
notions = import_json_file('tree_notions.json')
reviews = import_json_file('tree_reviews.json')

paper_json = {'name': 'XAI', 'children': []}
paper_json['children'].append(reviews)
paper_json['children'].append(notions)
paper_json['children'].append(evaluation)
paper_json['children'].append(methods)
with open('paper.json', 'w') as fp:
    json.dump(paper_json, fp)

final_tree = {'name': 'XAI', 'children': []}
final_tree['children'].append(counters(reviews))
final_tree['children'].append(counters(notions))
final_tree['children'].append(counters(evaluation))
final_tree['children'].append(counters(methods))
final_tree = [final_tree]

with open('tree_with_value.json', 'w') as fp:
    json.dump(final_tree, fp)
