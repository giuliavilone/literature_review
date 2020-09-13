import json
import pandas as pd
import itertools
import sys

#------------------ FORCE GRAPH ----------------#
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

    def iterate(dictionary, groupcol, coldict):
        for key, value in dictionary.items():
            if key =='name':
                source = value
                if not value in existing_nodes:
                    if value in coldict.keys():
                        nodes.append({"id": value, "group": coldict[value]})
                    else:
                        nodes.append({"id": value, "group": groupcol})
                    existing_nodes.append(value)
                    #print('key {!r} -> value {!r}'.format(key, value))
            else:
                for item in value:
                    links.append({"source": source, "target": item['name'], "value": 1})
                    if isinstance(item, dict):
                        iterate(item, groupcol, coldict)
                        continue
                #print('key {!r} -> value {!r}'.format(key, value))

    iterate(papers, 'black', colors)


    outdict = {"nodes":nodes,"links":links}
    with open('result.json', 'w') as fp:
        json.dump(outdict, fp)


#------------------ HIERARCHICAL EDGE BUNDLING ----------------#
edge_graph = False
if edge_graph:
    allnodes = []
    existingnodes = []
    outdict2 = {}
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
        #keys = ['flare.'+k for k in keys]
        allnodes = allnodes + keys
        comb = list(itertools.combinations(keys, 2))
        for item in comb:
            if str(item[0]+item[1]) in outdict2:
                outdict2[str(item[0]+item[1])]['size'] += 1
            elif str(item[1]+item[0]) in outdict2:
                outdict2[str(item[1]+item[0])]['size'] += 1
            else:
                existingnodes.append(item[0])
                outdict2[str(item[0]+item[1])] = {'name': item[0], 'size': 1, 'imports': [item[1]]}

    allnodes = list(set(allnodes))
    existingnodes = list(set(existingnodes))

    outlist = []
    for key, value in outdict2.items():
        outlist.append(value)

    missingnodes = [x for x in allnodes if x not in existingnodes]

    for item in missingnodes:
        outlist.append({'name': item, 'size': 1, 'imports': []})


    # Joining dictionaries with same name
    index_list = []
    for i in range(len(outlist)):
        for j in range(i+1, len(outlist)):
            if outlist[i]['name']==outlist[j]['name']:
                outlist[i]['size'] = outlist[i]['size'] + outlist[j]['size']
                outlist[i]['imports'] = outlist[i]['imports'] + outlist[j]['imports']
                index_list.append(j)

    index_list = list(set(index_list))
    for index in sorted(index_list, reverse=True):
        outlist.pop(index)

    print(len(outlist))

    with open('flare.json', 'w') as fp:
        json.dump(outlist, fp)



#--------------------------------- WORD CLOUD --------------------------------#
word_cloud = False
if word_cloud:
    df = pd.read_csv('keywords.csv')
    text = []
    for index, row in df.iterrows():
        # split the string into a list of keywords
        keys = row.keywords.split(';')
        keys = [k.lstrip() for k in keys]
        text = text + keys

    utext = [ (i,text.count(i)) for i in set(text) ]

    outlist = []
    for item in utext:
        outlist.append({"text":item[0],"size":item[1]})

    with open('wordcloud.json', 'w') as fp:
        json.dump(outlist, fp)

    commm="""
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

#------------------------------------------------------------------#
#------------------------- EXPANDABLE TREE ------------------------#
#------------------------------------------------------------------#

def url_list(idlist, urldf):
    """
    This function returns a list of dictionaries with the paper ids and urls
    """
    outlist = []
    for item in idlist:
        url = urldf['link'][urldf['ID']==item].tolist()[0]
        outlist.append({'name':item, 'url':url})

    return outlist

def id_manager(ingroup):
    """
    This function returns a list of IDS
    """
    ids = ingroup['ID'].tolist()
    ids = list(itertools.chain.from_iterable([item.split(',') for item in ids]))
    ids = list(set([k.lstrip() for k in ids]))
    return ids

#------------------ EXPANDABLE TREE REVIEWS BRANCH ----------------#

tree_reviews = False
if tree_reviews:
    df_reviews = pd.read_csv('reviews.csv')
    urls = pd.read_csv('urls.csv')
    reviewdict= {"name":"Reviews","children":[]}

    review_groups = df_reviews.groupby(['Branch'])

    for name, group in review_groups:
        if len(group) == 1:
            ids = id_manager(group)
            groupdict = {'name':name,'children':url_list(ids, urls)}
            reviewdict['children'].append(groupdict)
        else:
            subbranches = group.groupby(['Sub_branch'])
            subdict = {"name":name,"children":[]}
            for key, subgroup in subbranches:
                ids = id_manager(subgroup)
                groupdict = {'name':key,'children':url_list(ids, urls)}
                subdict['children'].append(groupdict)
            reviewdict['children'].append(subdict)

    with open('tree_reviews.json', 'w') as fp:
        json.dump(reviewdict, fp)

#------------------ EXPANDABLE TREE NOTIONS BRANCH ----------------#
tree_notions = False
if tree_notions:
    df_notions = pd.read_csv('notions.csv')
    urls = pd.read_csv('urls.csv')
    notiondict= {"name":"Notions","children":[]}

    notion_groups = df_notions.groupby(['Branch', 'Attribute cleaned'])

    attributedict = {"name":"Attributes","children":[]}
    otherdict = []
    for name, group in notion_groups:
        ids = id_manager(group)
        if name[0] =='Attributes':
            groupdict = {'name':name[1],'children':url_list(ids, urls)}
            attributedict['children'].append(groupdict)
        else:
            groupdict = {'name':name[0],'children':url_list(ids, urls)}
            otherdict.append(groupdict)
    notiondict['children'].append(attributedict)
    notiondict['children'] = notiondict['children'] + otherdict

    with open('tree_notions.json', 'w') as fp:
        json.dump(notiondict, fp)

#------------------ EXPANDABLE TREE EVALUATION BRANCH ----------------#
tree_evaluation = False
if tree_evaluation:
    df_evaluation = pd.read_csv('evaluation.csv')
    urls = pd.read_csv('urls.csv')
    evaluationdict= {"name":"Evaluation","children":[]}
    evaluation_groups = df_evaluation.groupby(['Branch'])

    for name, group in evaluation_groups:
        branchgroup = {"name":name,"children":[]}
        subbranches1 = group.groupby(['Sub_branch_1'])
        for key, subgroup in subbranches1:
            if len(subgroup)==1:
                ids = id_manager(subgroup)
                groupdict = {'name':key,'children':url_list(ids, urls)}
                branchgroup['children'].append(groupdict)
            else:
                branchgroup1 = {"name":key,"children":[]}
                subbranches2 = subgroup.groupby(['Sub_branch_2'])
                for key2, subgroup2 in subbranches2:
                    if len(subgroup2)==1 and subgroup2['Sub_branch_3'].tolist()[0] == 'None':
                        ids = id_manager(subgroup2)
                        groupdict2 = {'name':key2,'children':url_list(ids, urls)}
                        branchgroup1['children'].append(groupdict2)
                    else:
                        branchgroup2 = {"name":key2,"children":[]}
                        subbranches3 = subgroup2.groupby(['Sub_branch_3'])
                        for key3, subgroup3 in subbranches3:
                            ids = id_manager(subgroup3)
                            groupdict3 = {'name':key3,'children':url_list(ids, urls)}
                            branchgroup2['children'].append(groupdict3)
                        branchgroup1['children'].append(branchgroup2)
                branchgroup['children'].append(branchgroup1)
        evaluationdict['children'].append(branchgroup)


    with open('tree_evaluation.json', 'w') as fp:
        json.dump(evaluationdict, fp)

#------------------ EXPANDABLE TREE EVALUATION BRANCH (WITHOUT THIRD LEVEL BRANCH) ----------------#
tree_evaluation = False
if tree_evaluation:
    df_evaluation = pd.read_csv('evaluation.csv')
    urls = pd.read_csv('urls.csv')
    evaluationdict= {"name":"Evaluation","children":[]}
    evaluation_groups = df_evaluation.groupby(['Branch'])

    for name, group in evaluation_groups:
        branchgroup = {"name":name,"children":[]}
        subbranches1 = group.groupby(['Sub_branch_1'])
        for key, subgroup in subbranches1:
            if len(subgroup)==1:
                ids = id_manager(subgroup)
                groupdict = {'name':key,'children':url_list(ids, urls)}
                branchgroup['children'].append(groupdict)
            else:
                branchgroup1 = {"name":key,"children":[]}
                subbranches2 = subgroup.groupby(['Sub_branch_2'])
                for key2, subgroup2 in subbranches2:
                    ids = id_manager(subgroup2)
                    groupdict2 = {'name':key2,'children':url_list(ids, urls)}
                    branchgroup1['children'].append(groupdict2)
                branchgroup['children'].append(branchgroup1)
        evaluationdict['children'].append(branchgroup)


    with open('tree_evaluation.json', 'w') as fp:
        json.dump(evaluationdict, fp)

#------------------ EXPANDABLE TREE METHODS BRANCH ----------------#
tree_methods = True
if tree_methods:
    df_ah = pd.read_csv('ante-hoc.csv')
    df_ph = pd.read_csv('post-hoc.csv')
    urls = pd.read_csv('urls.csv')

    antehocdict= {"name": "Ante-hoc", "children": []}
    df_ah_groups = df_ah.groupby(['method'])
    for name, group in df_ah_groups:
        ids = group['ID'].tolist()
        ids = list(itertools.chain.from_iterable([item.split(',') for item in ids]))
        ids = list(set([k.lstrip() for k in ids]))
        groupdict = {'name': name, 'children': url_list(ids, urls)}
        antehocdict['children'].append(groupdict)


    posthocdict= {"name":"Post-hoc", "children": []}
    modspec_groupdict = {'name': 'Model specific', 'children': []}
    df_ph_groups = df_ph.groupby(['model_type'])

    for name, group in df_ph_groups:
        mod_groupdict = {'name': name, 'children': []}
        subgroups = group.groupby(['method'])
        for sname, sgroup in subgroups:
            ids = sgroup['ID'].tolist()
            ids = list(itertools.chain.from_iterable([item.split(',') for item in ids]))
            ids = list(set([k.lstrip() for k in ids]))
            subgroupdict = {'name': sname, 'children': url_list(ids, urls)}
            mod_groupdict['children'].append(subgroupdict)
    
        if name == 'Model agnostic':
            posthocdict['children'].append(mod_groupdict)
        else:
            modspec_groupdict['children'].append(mod_groupdict)
    
    posthocdict['children'].append(modspec_groupdict)

    treeoutdict = [{"name": "Stage", "children": [antehocdict, posthocdict]}]

    # Merging post-hoc and ante-hoc methods together
    df = df_ah
    df = df.append(df_ph, ignore_index= True)

    def group_creator(df, column, root_name):
        outvar = {'name': root_name, 'children': []}
        colgroups = df.groupby([column])
        for name, group in colgroups:
            groupdict = {'name': name, 'children':[]}
            initial_groups = group.groupby(['initials'])
            for initname, initgroup in initial_groups:
                initgroupdict = {'name': initname, 'children': []}
                subgroups = initgroup.groupby(['method'])
                for sname, sgroup in subgroups:
                    ids = sgroup['ID'].tolist()
                    ids = list(itertools.chain.from_iterable([item.split(',') for item in ids]))
                    ids = list(set([k.lstrip() for k in ids]))
                    subgroupdict = {'name': sname, 'children': url_list(ids, urls)}
                    initgroupdict['children'].append(subgroupdict)
                groupdict['children'].append(initgroupdict)
            outvar['children'].append(groupdict)
        return outvar

    scope = group_creator(df, 'scope', 'Scope')
    treeoutdict.append(scope)

    problem = group_creator(df, 'problem_type', 'Problem type')
    treeoutdict.append(problem)

    input_data = group_creator(df, 'input_type', 'Input data')
    treeoutdict.append(input_data)

    input_data = group_creator(df, 'explanation_type', 'Output format')
    treeoutdict.append(input_data)

    with open('tree_methods.json', 'w') as fp:
        json.dump(treeoutdict, fp)


# ---------------------- SUBSTITUTING PAPERS WITH REF NUMBERS ------------------------ #
numbtree = False
if numbtree:
    df_ref = pd.read_csv('paper_ref_number.csv')

    with open('papers.json') as json_file:
        treedata = json.load(json_file)


    def iterate2(dictionary, df):
        ref_numbers = df.ID.tolist()
        for key, value in dictionary.items():
            if key =='name':
                if value in ref_numbers:
                    dictionary[key] = df['Data'][df.ID==value].tolist()[0]
            else:
                for item in value:
                    if isinstance(item, dict):
                        iterate2(item, df)
                        continue
        return dictionary

    treeoutdict = iterate2(treedata, df_ref)

    with open('paper_numbers.json', 'w') as fp:
        json.dump(treeoutdict, fp)
